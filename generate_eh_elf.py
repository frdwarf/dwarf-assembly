#!/usr/bin/env python3

"""
Generates the `.eh_frame` equivalent in C code of the given ELF file, and
all the shared objects it depends upon.
"""


import os
import sys
import subprocess
import tempfile
import argparse
from enum import Enum

from shared_python import elf_so_deps, do_remote, is_newer
from extract_pc import generate_pc_list


DWARF_ASSEMBLY_BIN = os.path.join(
    os.path.dirname(os.path.abspath(sys.argv[0])),
    'dwarf-assembly')
C_BIN = (
    'gcc' if 'C' not in os.environ
    else os.environ['C'])


class SwitchGenPolicy(Enum):
    ''' The various switch generation policies possible '''
    SWITCH_PER_FUNC = '--switch-per-func'
    GLOBAL_SWITCH = '--global-switch'


class Config:
    ''' Holds the run's settings '''

    default_aux = [
        '~/.cache/eh_elfs',
    ]

    def __init__(self,
                 output,
                 aux,
                 no_dft_aux,
                 objects,
                 sw_gen_policy=SwitchGenPolicy.GLOBAL_SWITCH,
                 force=False,
                 use_pc_list=False,
                 c_opt_level='3',
                 enable_deref_arg=False,
                 cc_debug=False,
                 remote=None):
        self.output = '.' if output is None else output
        self.aux = (
            aux
            + ([] if no_dft_aux else self.default_aux)
        )
        self.objects = objects
        self.sw_gen_policy = sw_gen_policy
        self.force = force
        self.use_pc_list = use_pc_list
        self.c_opt_level = c_opt_level
        self.enable_deref_arg = enable_deref_arg
        self.cc_debug = cc_debug
        self.remote = remote

    @staticmethod
    def default_aux_str():
        return ', '.join(Config.default_aux)

    def dwarf_assembly_args(self):
        ''' Arguments to `dwarf_assembly` '''
        out = []
        out.append(self.sw_gen_policy.value)
        if self.enable_deref_arg:
            out.append('--enable-deref-arg')
        return out

    def cc_opts(self):
        ''' Options to pass to the C compiler '''
        out = ['-fPIC']
        if self.cc_debug:
            out.append('-g')
        out.append(self.opt_level())
        return out

    def opt_level(self):
        ''' The optimization level to pass to gcc '''
        return '-O{}'.format(self.c_opt_level)

    def aux_dirs(self):
        ''' Get the list of auxiliary directories '''
        return self.aux


def gen_dw_asm_c(obj_path, out_path, config, pc_list_path=None):
    ''' Generate the C code produced by dwarf-assembly from `obj_path`, saving
    it as `out_path` '''

    dw_assembly_args = config.dwarf_assembly_args()
    if pc_list_path is not None:
        dw_assembly_args += ['--pc-list', pc_list_path]

    try:
        with open(out_path, 'w') as out_handle:
            # TODO enhance error handling
            dw_asm_output = subprocess.check_output(
                [DWARF_ASSEMBLY_BIN, obj_path] + dw_assembly_args) \
                .decode('utf-8')
            out_handle.write(dw_asm_output)
    except subprocess.CalledProcessError as exn:
        raise Exception(
            ("Cannot generate C code from object file {} using {}: process "
             "terminated with exit code {}.").format(
                 obj_path,
                 DWARF_ASSEMBLY_BIN,
                 exn.returncode))


def resolve_symlink_chain(objpath):
    ''' Resolves a symlink chain. This returns a pair `(new_obj, chain)`,
    `new_obj` being the canonical path for `objpath`, and `chain` being a list
    representing the path followed, eg. `[(objpath, a), (a, b), (b, new_obj)]`.
    The goal of this function is to allow reproducing symlink architectures at
    the eh_elf level. '''

    chain = []
    out_path = objpath

    while os.path.islink(out_path):
        new_path = os.readlink(out_path)
        if not os.path.isabs(new_path):
            new_path = os.path.join(os.path.dirname(out_path), new_path)
        chain.append((out_path, new_path))
        out_path = new_path

    return (out_path, chain)


def to_eh_elf_path(so_path, out_dir, base=False):
    ''' Transform a library path into its eh_elf counterpart '''
    base_path = os.path.basename(so_path) + '.eh_elf'
    if base:
        return base_path
    return os.path.join(out_dir, base_path + '.so')


def find_out_dir(obj_path, config):
    ''' Find the directory in which the eh_elf corresponding to `obj_path` will
    be outputted, among the output directory and the aux directories '''

    for candidate in config.aux_dirs():
        eh_elf_path = to_eh_elf_path(obj_path, candidate)
        if os.path.exists(eh_elf_path):
            return candidate

    # No match among the aux dirs
    return config.output


def gen_eh_elf(obj_path, config):
    ''' Generate the eh_elf corresponding to `obj_path`, saving it as
    `out_dir/$(basename obj_path).eh_elf.so` (or in the current working
    directory if out_dir is None) '''

    out_dir = find_out_dir(obj_path, config)
    obj_path, link_chain = resolve_symlink_chain(obj_path)

    print("> {}...".format(os.path.basename(obj_path)))

    link_chain = map(
        lambda elt:
            (to_eh_elf_path(elt[0], out_dir),
             os.path.basename(to_eh_elf_path(elt[1], out_dir))),
        link_chain)

    out_base_name = to_eh_elf_path(obj_path, out_dir, base=True)
    out_so_path = to_eh_elf_path(obj_path, out_dir, base=False)
    pc_list_dir = os.path.join(out_dir, 'pc_list')

    if is_newer(out_so_path, obj_path) and not config.force:
        return  # The object is recent enough, no need to recreate it

    if os.path.exists(out_dir) and not os.path.isdir(out_dir):
        raise Exception("The output path {} is not a directory.".format(
            out_dir))
    if not os.path.exists(out_dir):
        os.makedirs(out_dir, exist_ok=True)

    with tempfile.TemporaryDirectory() as compile_dir:
        # Generate PC list
        pc_list_path = None
        if config.use_pc_list:
            pc_list_path = \
                os.path.join(pc_list_dir, out_base_name + '.pc_list')
            os.makedirs(pc_list_dir, exist_ok=True)
            print('\tGenerating PC list…')
            generate_pc_list(obj_path, pc_list_path)

        # Generate the C source file
        print("\tGenerating C…")
        c_path = os.path.join(compile_dir, (out_base_name + '.c'))
        gen_dw_asm_c(obj_path, c_path, config, pc_list_path)

        # Compile it into a .o
        print("\tCompiling into .o…")
        o_path = os.path.join(compile_dir, (out_base_name + '.o'))
        if config.remote:
            remote_out = do_remote(
                config.remote,
                [
                    C_BIN,
                    '-o', out_base_name + '.o',
                    '-c', out_base_name + '.c'
                ] + config.cc_opts(),
                send_files=[c_path],
                retr_files=[(out_base_name + '.o', o_path)])
            call_rc = 1 if remote_out is None else 0
        else:
            call_rc = subprocess.call(
                [C_BIN, '-o', o_path, '-c', c_path,
                 config.opt_level(), '-fPIC'])
        if call_rc != 0:
            raise Exception("Failed to compile to a .o file")

        # Compile it into a .so
        print("\tCompiling into .so…")
        call_rc = subprocess.call(
            [C_BIN, '-o', out_so_path, '-shared', o_path])
        if call_rc != 0:
            raise Exception("Failed to compile to a .so file")

    # Re-create symlinks
    for elt in link_chain:
        if os.path.exists(elt[0]):
            if not os.path.islink(elt[0]):
                raise Exception(
                    "{}: file already exists and is not a symlink.".format(
                        elt[0]))
            os.remove(elt[0])
        os.symlink(elt[1], elt[0])


def gen_all_eh_elf(obj_path, config):
    ''' Call `gen_eh_elf` on obj_path and all its dependencies '''
    deps = elf_so_deps(obj_path)
    deps.append(obj_path)
    for dep in deps:
        gen_eh_elf(dep, config)


def gen_eh_elfs(obj_path,
                out_dir,
                global_switch=True,
                deps=True,
                remote=None):
    ''' Call gen{_all,}_eh_elf with args setup accordingly with the given
    options '''

    switch_gen_policy = (
        SwitchGenPolicy.GLOBAL_SWITCH if global_switch
        else SwitchGenPolicy.SWITCH_PER_FUNC
    )

    config = Config(
        out_dir,
        [obj_path],
        sw_gen_policy=switch_gen_policy,
        remote=remote,
    )

    if deps:
        return gen_all_eh_elf([obj_path], config)
    else:
        return gen_eh_elf([obj_path], config)


def process_args():
    ''' Process `sys.argv` arguments '''

    parser = argparse.ArgumentParser(
        description="Compile ELFs into their related eh_elfs",
    )

    parser.add_argument('--deps', action='store_const',
                        const=gen_all_eh_elf, default=gen_eh_elf,
                        dest='gen_func',
                        help=("Also generate eh_elfs for the shared objects "
                              "this object depends on"))
    parser.add_argument('-o', '--output', metavar="path",
                        help=("Save the generated objects at the given path "
                              "instead of the current working directory"))
    parser.add_argument('-a', '--aux', action='append', default=[],
                        help=("Alternative output directories. These "
                              "directories are searched for existing matching "
                              "eh_elfs, and if found, these files are updated "
                              "instead of creating new files in the --output "
                              "directory. By default, some aux directories "
                              "are always considered, unless -A is passed: "
                              "{}.").format(Config.default_aux_str()))
    parser.add_argument('-A', '--no-dft-aux', action='store_true',
                        help=("Do not use the default auxiliary output "
                              "directories: {}.").format(
                                  Config.default_aux_str()))
    parser.add_argument('--remote', metavar='ssh_args',
                        help=("Execute the heavyweight commands on the remote "
                              "machine, using `ssh ssh_args`."))
    parser.add_argument('--use-pc-list', action='store_true',
                        help=("Generate a PC list using `extract_pc.py` for "
                              "each processed ELF file, and call "
                              "dwarf-assembly accordingly."))
    parser.add_argument('--force', '-f', action='store_true',
                        help=("Force re-generation of the output files, even "
                              "when those files are newer than the target "
                              "ELF."))
    parser.add_argument('--enable-deref-arg', action='store_true',
                        help=("Pass the `--enable-deref-arg` to "
                              "dwarf-assembly, enabling an extra `deref` "
                              "argument for each lookup function, allowing "
                              "to work on remote address spaces."))
    parser.add_argument("-g", "--cc-debug", action='store_true',
                        help=("Compile the source file with -g for easy "
                              "debugging"))
    # c_opt_level
    opt_level_grp = parser.add_mutually_exclusive_group()
    opt_level_grp.add_argument('-O0', action='store_const', const='0',
                               dest='c_opt_level',
                               help=("Compile C file with this optimization "
                                     "level."))
    opt_level_grp.add_argument('-O1', action='store_const', const='1',
                               dest='c_opt_level',
                               help=("Compile C file with this optimization "
                                     "level."))
    opt_level_grp.add_argument('-O2', action='store_const', const='2',
                               dest='c_opt_level',
                               help=("Compile C file with this optimization "
                                     "level."))
    opt_level_grp.add_argument('-O3', action='store_const', const='3',
                               dest='c_opt_level',
                               help=("Compile C file with this optimization "
                                     "level."))
    opt_level_grp.add_argument('-Os', action='store_const', const='s',
                               dest='c_opt_level',
                               help=("Compile C file with this optimization "
                                     "level."))
    opt_level_grp.set_defaults(c_opt_level='3')

    switch_gen_policy = \
        parser.add_mutually_exclusive_group(required=True)
    switch_gen_policy.add_argument('--switch-per-func',
                                   dest='sw_gen_policy',
                                   action='store_const',
                                   const=SwitchGenPolicy.SWITCH_PER_FUNC,
                                   help=("Passed to dwarf-assembly."))
    switch_gen_policy.add_argument('--global-switch',
                                   dest='sw_gen_policy',
                                   action='store_const',
                                   const=SwitchGenPolicy.GLOBAL_SWITCH,
                                   help=("Passed to dwarf-assembly."))
    parser.add_argument('object', nargs='+',
                        help="The ELF object(s) to process")
    return parser.parse_args()


def main():
    args = process_args()
    print(args)
    config = Config(
        args.output,
        args.aux,
        args.no_dft_aux,
        args.object,
        args.sw_gen_policy,
        args.force,
        args.use_pc_list,
        args.c_opt_level,
        args.enable_deref_arg,
        args.cc_debug,
        args.remote,
    )

    for obj in args.object:
        args.gen_func(obj, config)


if __name__ == "__main__":
    main()
