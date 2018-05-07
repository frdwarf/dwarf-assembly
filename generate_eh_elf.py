#!/usr/bin/env python3

"""
Generates the `.eh_frame` equivalent in C code of the given ELF file, and
all the shared objects it depends upon.
"""


import os
import sys
import subprocess
import re
import tempfile
import argparse
from collections import namedtuple


DWARF_ASSEMBLY_BIN = os.path.join(
    os.path.dirname(os.path.abspath(sys.argv[0])),
    'dwarf-assembly')
C_BIN = (
    'gcc' if 'C' not in os.environ
    else os.environ['C'])


def elf_so_deps(path):
    ''' Get the list of shared objects dependencies of the given ELF object.
    This is obtained by running `ldd`. '''

    deps_list = []

    try:
        ldd_output = subprocess.check_output(['/usr/bin/ldd', path]) \
            .decode('utf-8')
        ldd_re = re.compile(r'^.* => (.*) \(0x[0-9a-fA-F]*\)$')

        ldd_lines = ldd_output.strip().split('\n')
        for line in ldd_lines:
            line = line.strip()
            match = ldd_re.match(line)
            if match is None:
                continue  # Just ignore that line — it might be eg. linux-vdso
            deps_list.append(match.group(1))

        return deps_list

    except subprocess.CalledProcessError as e:
        raise Exception(
            ("Cannot get dependencies for {}: ldd terminated with exit code "
             "{}.").format(path, e.returncode))


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
    except subprocess.CalledProcessError as e:
        raise Exception(
            ("Cannot generate C code from object file {} using {}: process "
             "terminated with exit code {}.").format(
                 obj_path,
                 DWARF_ASSEMBLY_BIN,
                 e.returncode))


def do_remote(remote, command, send_files=None, retr_files=None):
    def ssh_do(cmd_args, working_directory=None):
        try:
            cmd = ['ssh', remote]
            if working_directory:
                cmd += ['cd', working_directory, '&&']
            cmd += cmd_args

            return subprocess.check_output(cmd).decode('utf-8').strip()
        except subprocess.CalledProcessError as e:
            return None

    def ssh_copy(what, where, is_upload):
        if is_upload:
            where = '{}:{}'.format(remote, where)
        else:
            what = '{}:{}'.format(remote, what)

        subprocess.check_output(['scp', what, where])

    TransferredFile = namedtuple('TransferredFile', 'local remote')

    def interpret_transferred_file(descr):
        if type(descr) == type(''):
            return TransferredFile(descr, descr)
        if os.path.isdir(descr[1]):
            to = os.path.join(descr[1], descr[0])
        else:
            to = descr[1]
        return TransferredFile(descr[0], to)

    # Create temp dir
    tmp_dir = ssh_do(['mktemp', '-d'])

    # Upload `send_files`
    for f in send_files:
        dest = tmp_dir+'/'
        ssh_copy(f, dest, is_upload=True)

    # Do whatever must be done
    output = ssh_do(command, working_directory=tmp_dir)

    # Download `retr_files`
    for f in map(interpret_transferred_file, retr_files):
        src = os.path.join(tmp_dir, f.local)
        ssh_copy(src, f.remote, is_upload=False)

    # Remove temp dir
    ssh_do(['rm', '-rf', tmp_dir])

    return output


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

    try:
        so_mtime = os.path.getmtime(out_so_path)
        obj_mtime = os.path.getmtime(obj_path)

        if obj_mtime < so_mtime:
            return  # The object is recent enough, no need to recreate it
    except OSError:
        pass


    with tempfile.TemporaryDirectory() as compile_dir:
        # Generate the C source file
        print("\tGenerating C…")
        c_path = os.path.join(compile_dir, (out_base_name + '.c'))
        gen_dw_asm_c(obj_path, c_path, dwarf_assembly_args)

        # Compile it into a .o
        print("\tCompiling into .o…")
        o_path = os.path.join(compile_dir, (out_base_name + '.o'))
        if args.remote:
            remote_out = do_remote(
                args.remote,
                [C_BIN,
                 '-o', out_base_name + '.o',
                 '-c', out_base_name + '.c',
                 '-O3', '-fPIC'],
                send_files=[c_path],
                retr_files=[(out_base_name + '.o', o_path)])
            call_rc = 1 if remote_out is None else 0
        else:
            call_rc = subprocess.call(
                [C_BIN, '-o', o_path, '-c', c_path, '-O3', '-fPIC'])
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

    for obj in args.object:
        args.gen_func(obj, args, dwarf_assembly_opts)


if __name__ == "__main__":
    main()
