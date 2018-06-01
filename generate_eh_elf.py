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

from shared_python import elf_so_deps, do_remote, is_newer
from extract_pc import generate_pc_list


DWARF_ASSEMBLY_BIN = os.path.join(
    os.path.dirname(os.path.abspath(sys.argv[0])),
    'dwarf-assembly')
C_BIN = (
    'gcc' if 'C' not in os.environ
    else os.environ['C'])


def gen_dw_asm_c(obj_path, out_path, dwarf_assembly_args):
    ''' Generate the C code produced by dwarf-assembly from `obj_path`, saving
    it as `out_path` '''

    try:
        with open(out_path, 'w') as out_handle:
            # TODO enhance error handling
            dw_asm_output = subprocess.check_output(
                [DWARF_ASSEMBLY_BIN, obj_path] + dwarf_assembly_args) \
                .decode('utf-8')
            out_handle.write(dw_asm_output)
    except subprocess.CalledProcessError as exn:
        raise Exception(
            ("Cannot generate C code from object file {} using {}: process "
             "terminated with exit code {}.").format(
                 obj_path,
                 DWARF_ASSEMBLY_BIN,
                 exn.returncode))


def gen_eh_elf(obj_path, args, dwarf_assembly_args=None):
    ''' Generate the eh_elf corresponding to `obj_path`, saving it as
    `out_dir/$(basename obj_path).eh_elf.so` (or in the current working
    directory if out_dir is None) '''

    if args.output is None:
        out_dir = '.'
    else:
        out_dir = args.output

    if dwarf_assembly_args is None:
        dwarf_assembly_args = []

    print("> {}...".format(os.path.basename(obj_path)))

    out_base_name = os.path.basename(obj_path) + '.eh_elf'
    out_so_path = os.path.join(out_dir, (out_base_name + '.so'))
    pc_list_dir = os.path.join(out_dir, 'pc_list')

    if is_newer(out_so_path, obj_path) and not args.force:
        return  # The object is recent enough, no need to recreate it

    with tempfile.TemporaryDirectory() as compile_dir:
        # Generate PC list
        if args.use_pc_list:
            pc_list_path = \
                os.path.join(pc_list_dir, out_base_name + '.pc_list')
            os.makedirs(pc_list_dir, exist_ok=True)
            print('\tGenerating PC list…')
            generate_pc_list(obj_path, pc_list_path)
            dwarf_assembly_args += ['--pc-list', pc_list_path]

        # Generate the C source file
        print("\tGenerating C…")
        c_path = os.path.join(compile_dir, (out_base_name + '.c'))
        gen_dw_asm_c(obj_path, c_path, dwarf_assembly_args)

        # Compile it into a .o
        print("\tCompiling into .o…")
        o_path = os.path.join(compile_dir, (out_base_name + '.o'))
        opt_level = args.c_opt_level
        if opt_level is None:
            opt_level = '-O3'
        if args.remote:
            remote_out = do_remote(
                args.remote,
                [C_BIN,
                 '-o', out_base_name + '.o',
                 '-c', out_base_name + '.c',
                 opt_level, '-fPIC'],
                send_files=[c_path],
                retr_files=[(out_base_name + '.o', o_path)])
            call_rc = 1 if remote_out is None else 0
        else:
            call_rc = subprocess.call(
                [C_BIN, '-o', o_path, '-c', c_path, opt_level, '-fPIC'])
        if call_rc != 0:
            raise Exception("Failed to compile to a .o file")

        # Compile it into a .so
        print("\tCompiling into .so…")
        call_rc = subprocess.call(
            [C_BIN, '-o', out_so_path, '-shared', o_path])
        if call_rc != 0:
            raise Exception("Failed to compile to a .so file")


def gen_all_eh_elf(obj_path, args, dwarf_assembly_args=None):
    ''' Call `gen_eh_elf` on obj_path and all its dependencies '''
    if dwarf_assembly_args is None:
        dwarf_assembly_args = []

    deps = elf_so_deps(obj_path)
    deps.append(obj_path)
    for dep in deps:
        gen_eh_elf(dep, args, dwarf_assembly_args)


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
    # c_opt_level
    opt_level_grp = parser.add_mutually_exclusive_group()
    opt_level_grp.add_argument('-O0', action='store_const', const='-O0',
                               dest='c_opt_level',
                               help=("Compile C file with this optimization "
                                     "level."))
    opt_level_grp.add_argument('-O1', action='store_const', const='-O1',
                               dest='c_opt_level',
                               help=("Compile C file with this optimization "
                                     "level."))
    opt_level_grp.add_argument('-O2', action='store_const', const='-O2',
                               dest='c_opt_level',
                               help=("Compile C file with this optimization "
                                     "level."))
    opt_level_grp.add_argument('-O3', action='store_const', const='-O3',
                               dest='c_opt_level',
                               help=("Compile C file with this optimization "
                                     "level."))
    opt_level_grp.add_argument('-Os', action='store_const', const='-Os',
                               dest='c_opt_level',
                               help=("Compile C file with this optimization "
                                     "level."))

    switch_generation_policy = \
        parser.add_mutually_exclusive_group(required=True)
    switch_generation_policy.add_argument('--switch-per-func',
                                          action='store_const', const='',
                                          help=("Passed to dwarf-assembly."))
    switch_generation_policy.add_argument('--global-switch',
                                          action='store_const', const='',
                                          help=("Passed to dwarf-assembly."))
    parser.add_argument('object', nargs='+',
                        help="The ELF object(s) to process")
    return parser.parse_args()


def main():
    args = process_args()

    DW_ASSEMBLY_OPTS = {
        'switch_per_func': '--switch-per-func',
        'global_switch': '--global-switch',
    }

    dwarf_assembly_opts = []
    args_dict = vars(args)
    for opt in DW_ASSEMBLY_OPTS:
        if opt in args and args_dict[opt] is not None:
            dwarf_assembly_opts.append(DW_ASSEMBLY_OPTS[opt])
    if args.enable_deref_arg:
        dwarf_assembly_opts.append('--enable-deref-arg')

    for obj in args.object:
        args.gen_func(obj, args, dwarf_assembly_opts)


if __name__ == "__main__":
    main()
