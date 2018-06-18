#!/usr/bin/env python3

""" Compare the sizes of the .eh_frame section in the original binary and of
the .text in the generated .eh_elf.so. """


import argparse
import os
import subprocess
from collections import namedtuple

from shared_python import elf_so_deps, readlink_rec


''' An ELF object, including the path to the ELF itself, and the path to its
matching eh_elf '''
ElfObject = namedtuple('ElfObject', 'elf eh_elf')


def format_size(size):
    ''' Format a size to a human-readable string '''

    units = ['B', 'KiB', 'MiB', 'GiB']  # We'll never go over that
    cur_unit = 0
    while cur_unit < len(units) and size >= 1024:
        size /= 1024
        cur_unit += 1

    return '{:.1f} {}'.format(size, units[cur_unit])


def invoke_objdump_headers(elf_loc):
    ''' Call objdump -h, returning the list of lines outputted '''

    if not os.path.isfile(elf_loc):
        raise FileNotFoundError

    try:
        objdump_out = subprocess.check_output(['objdump', '-h', elf_loc]) \
            .decode('utf-8')
    except subprocess.CalledProcessError as exn:
        raise Exception(("Cannot run objdump on {}: objdump "
                         "terminated with exit code {}.").format(
                             elf_loc, exn.returncode))

    return objdump_out.split('\n')


def get_elf_sections(elf_loc):
    ''' List the ELF sections of the given ELF '''

    sections = {}
    for line in invoke_objdump_headers(elf_loc):
        line = line.strip()
        if not line or not '0' <= line[0] <= '9':  # not a section line
            continue

        spl = line.split()
        sections[spl[1]] = {
            'name': spl[1],
            'size': int(spl[2], 0x10),
        }

    return sections


def matching_eh_elf(eh_locs, elf_name):
    ''' Get the .eh_elf.so file matching elf_name in the list of directories
    eh_locs.

    Raises FileNotFoundError if there is no such file '''

    basename = os.path.basename(elf_name) + '.eh_elf.so'
    for prefix in eh_locs:
        eh_elf_path = os.path.join(prefix, basename)
        if os.path.isfile(eh_elf_path):
            return eh_elf_path
    raise FileNotFoundError("No such file {}".format(basename))


def objects_list(args):
    ''' Get the list of elf objects to process '''

    out = []

    if args.deps:
        objects = set(args.object)
        for obj in args.object:
            objects = objects.union(elf_so_deps(obj))
        objects = list(objects)
        objects.sort()
    else:
        objects = args.object

    objects = list(map(readlink_rec, objects))

    for obj in objects:
        out.append(ElfObject(obj, matching_eh_elf(args.eh_elfs, obj)))

    return out


def process_args():
    ''' Process `sys.argv` arguments '''

    parser = argparse.ArgumentParser(
        description=("Compare the sizes of the .eh_frame section in the "
                     "original binary and of the .text in the generated "
                     ".eh_elf.so."),
    )

    parser.add_argument('--deps', action='store_true',
                        help=("Also compare the shared objects this object "
                              "depends on"))
    parser.add_argument('--eh-elfs', required=True, action='append',
                        help=("Indicate the directory in which eh_elfs are "
                              "located"))
    parser.add_argument('object', nargs='+',
                        help="The ELF object(s) to process")
    return parser.parse_args()


def get_or_default(obj, field, default=None):
    ''' Access a field of a subscriptable, returning a default if there is no
    such field '''

    if field not in obj:
        return default
    return obj[field]


def main():
    args = process_args()
    objs = objects_list(args)

    col_names = [
        'Shared object',
        'Orig eh_frame',
        'Gen eh_elf .text',
        '+ .rodata',
        'Growth',
    ]

    col_len = []

    displayed_name_filter = lambda x: os.path.basename(x.elf)
    max_elf_name = max(map(lambda x: len(displayed_name_filter(x)), objs))
    col_len.append(max(max_elf_name, len(col_names[0])))
    for i in range(1, len(col_names)):
        col_len.append(len(col_names[i]) + 1)
    col_len = list(map(str, col_len))

    header_format = ('{:<' + col_len[0] + '}   '
                     '{:<' + col_len[1] + '}   '
                     '{:<' + col_len[2] + '}   '
                     '{:<' + col_len[3] + '}   '
                     '{:<' + col_len[4] + '}')
    row_format = ('{:>' + col_len[0] + '}   '
                  '{:>' + col_len[1] + '}   '
                  '{:>' + col_len[2] + '}   '
                  '{:>' + col_len[3] + '}   '
                  '{:>' + col_len[4] + '}')
    print(header_format.format(
        col_names[0],
        col_names[1],
        col_names[2],
        col_names[3],
        col_names[4],
    ))

    total_eh_frame_size = 0
    total_eh_elf_text_size = 0
    total_eh_elf_size = 0

    for obj in objs:
        elf_sections = get_elf_sections(obj.elf)
        eh_elf_sections = get_elf_sections(obj.eh_elf)

        eh_frame_size = get_or_default(
            elf_sections, '.eh_frame', {'size': 0})['size']
        eh_elf_text_size = get_or_default(
            eh_elf_sections, '.text', {'size': 0})['size']
        eh_elf_size = eh_elf_text_size + \
            get_or_default(
                eh_elf_sections, '.rodata', {'size': 0})['size']

        total_eh_frame_size += eh_frame_size
        total_eh_elf_text_size += eh_elf_text_size
        total_eh_elf_size += eh_elf_size

        print(row_format.format(
            displayed_name_filter(obj),
            format_size(eh_frame_size),
            format_size(eh_elf_text_size),
            format_size(eh_elf_size),
            '{:.2f}'.format(eh_elf_size / eh_frame_size)))

        # Checking for missed big sections
        for section in eh_elf_sections:
            if section == '.text' or section == '.rodata':
                continue
            if eh_elf_sections[section]['size'] > eh_elf_size / 2:
                print("\t\t/!\\ Section {} is big ({}) in the eh_elf".format(
                    section, format_size(eh_elf_sections[section]['size'])))

    print(row_format.format(
        'Total',
        format_size(total_eh_frame_size),
        format_size(total_eh_elf_size),
        format_size(total_eh_elf_text_size),
        '{:.2f}'.format(total_eh_elf_size / total_eh_frame_size)))


if __name__ == '__main__':
    main()
