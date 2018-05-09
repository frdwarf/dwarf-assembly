#!/usr/bin/env python3

""" Extract the list of program counters (PC) at which an instruction can be
found in the .text section of an ELF object. """


import argparse
import os
import subprocess
import re
import copy
from shared_python import elf_so_deps, is_newer


def generate_pc_list(elf, out_path):
    ''' Generate the list of valid program counters for the ELF object `elf`,
    and save it to `out_path`
    
    out_path is a binary file, each 8B chunk being a little-endian PC '''

    if is_newer(out_path, elf):
        return

    with open(out_path, 'wb') as out_handle:
        objdump_out = subprocess.check_output(
            ['objdump', '-d', elf]).decode('utf-8')
        lines = objdump_out.split('\n')

        instr_line_re = re.compile(
            r'^([0-9a-fA-F]+):\s+(?:[0-9a-fA-F]{2} )+')

        for line in lines:
            line = line.strip()
            matched = instr_line_re.match(line)
            if matched:
                pc = int(matched.group(1), 0x10)
                pc_bytes = pc.to_bytes(8, byteorder='little', signed=False)
                out_handle.write(pc_bytes)


def process_args():
    ''' Process `sys.argv` arguments '''

    parser = argparse.ArgumentParser(
        description=('Extract the list of program counters (PC) at which an '
                     'instruction can be found in the .text section of an ELF '
                     'object.')
    )

    parser.add_argument('--deps', action='store_true',
                        help=("Also process the shared objects this object "
                              "depends on"))
    parser.add_argument('-o', '--output', required=True,
                        help=("output directory in which the produced files "
                              "will be stored"))
    parser.add_argument('object', nargs='+',
                        help="The ELF object(s) to process")
    return parser.parse_args()


def main():
    args = process_args()

    objs_list = copy.copy(args.object)
    if args.deps:
        for obj in args.object:
            objs_list += elf_so_deps(obj)

    for obj in objs_list:
        basename = os.path.basename(obj)
        print('> {}…'.format(basename))
        out_path = os.path.join(args.output,
                                basename + '.pc_list')
        generate_pc_list(obj, out_path)


if __name__ == '__main__':
    main()
