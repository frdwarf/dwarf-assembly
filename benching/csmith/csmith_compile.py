#!/usr/bin/env python3

""" Helper file to generate Csmith test cases for benchmarking purposes """

import argparse
import subprocess
import os
import re
import sys
import copy

sys.path.append('../..')

from shared_python import do_remote
from generate_eh_elf import gen_eh_elfs


def get_base_id(out_dir, base_name):
    ''' Find the smallest xx such that
    ∀y >= x, `[out_dir]/[base_name]0*[yy].*` does not exist '''

    direntry_id_re = re.compile(r'0*(\d+)\..*')

    out = -1

    for entry in os.scandir(out_dir):
        fname = entry.name
        if not fname.startswith(base_name):
            continue
        fname = fname[len(base_name):]  # Truncate base_name from fname
        match = direntry_id_re.match(fname)
        if match is None:
            continue

        out = max(out, int(match.group(1)))

    return out + 1


def csmith_generate(name, args):
    ''' Generate a C file using Csmith (possibly on --remote) '''

    command = [
        args.csmith_binary,
    ]

    if args.fast_csmith:
        command += ['--max-funcs', '15']
    else:
        command += ['--max-funcs', '100']

    def write_file(content):
        with open(name, 'w') as handle:
            handle.write(content)

    def postprocess(content):
        csmith_h_re = re.compile(r'#include "csmith.h"')
        return_re = re.compile(r'\breturn\b')
        content = csmith_h_re.sub(
            '#include <bench.h>\n#include <csmith.h>',
            return_re.sub(
                'bench_unwinding(); return',
                content))
        write_file(content)

    if args.remote:
        out = do_remote(args.remote, command)
    else:
        out = subprocess.check_output(command).decode('utf-8')

    if out is None:
        print("Generating {} failed".format(name), file=sys.stderr)
        return False

    postprocess(out)
    return True


def csmith_compile_libunwind(name, src, args):
    ''' Compile a Csmith-generated file, using libunwind as an unwinding
    mechanism for benchmarking '''

    base_dir = os.path.dirname(os.path.realpath(__file__))
    benchlib_path = os.path.normpath(os.path.join(base_dir, '../benchlib/'))
    env = copy.copy(os.environ)
    env.update({
        'LD_RUN_PATH': benchlib_path,
    })
    command = [
        'gcc', '-O3',
        '-L' + benchlib_path, '-lbench.unwind',
        '-I' + benchlib_path,
        '-I' + '/usr/include/csmith-2.3.0',
        '-o', name,
        src,
    ]
    print('LD_RUN_PATH={} {}'.format(env['LD_RUN_PATH'], ' '.join(command)))

    try:
        subprocess.run(' '.join(command), env=env, check=True, shell=True)
    except subprocess.CalledProcessError as exn:
        print("Compiling {}: failed with return code {}".format(
            name, exn.returncode), file=sys.stderr)
        return False

    return True


def csmith_compile_eh_elf(name, src, args):
    ''' Compile a Csmith-generated file, using eh_elf and stack_walker as a
    mechanism for benchmarking '''

    base_dir = os.path.realpath(__file__)
    env = {
        'LD_RUN_PATH': ':'.join(
            [
                os.path.join(base_dir, '../benchlib'),
                os.path.join(base_dir, '../../stack_walker'),
                'eh_elfs'
            ]),
    }
    command = [
        'gcc', '-O3',
        src,
        '-L', os.path.join(base_dir, '../benchlib/'), '-lbench.eh_elf',
        '-L', os.path.join(base_dir, '../../stack_walker'),
        '-lstack_walker.global',
        '-o', name,
    ]

    try:
        subprocess.run(command, env=env, check=True)
    except subprocess.CalledProcessError as exn:
        print("Compiling {}: failed with return code {}".format(
            name, exn.returncode), file=sys.stderr)
        return False

    eh_elf_path = os.path.join(args.output, 'eh_elfs')
    os.makedirs(eh_elf_path, exist_ok=True)
    gen_eh_elfs(name,
                eh_elf_path,
                global_switch=True,
                deps=True,
                remote=args.remote)
    return True


def generate_and_compile(name_base, args):
    c_name = name_base + '.c'
    unwind_bin_name = name_base + '.unwind.bin'
    eh_elf_bin_name = name_base + '.eh_elf.bin'

    print('\tGenerating C file…')
    if not csmith_generate(c_name, args):
        return False
    print('\tCompiling with libunwind…')
    if not csmith_compile_libunwind(unwind_bin_name, c_name, args):
        return False
    print('\tCompiling with eh_elf…')
    if not csmith_compile_eh_elf(eh_elf_bin_name, c_name, args):
        return False
    return True


def process_args():
    ''' Process `sys.argv` arguments '''

    parser = argparse.ArgumentParser(prog="csmith_compile")

    parser.add_argument('--remote',
                        help=("Execute the heavyweight steps of the "
                              "computation on the remote machine "
                              "indicated, formatted for ssh"))
    subparsers = parser.add_subparsers()

    gc_parser = subparsers.add_parser(
        'gen-test',
        help=("Generate one or more Csmith test cases for benchmarking, and "
              "compile them into the corresponding binaries linked against "
              "libunwind and eh_elfs")
    )

    gc_parser.add_argument('--csmith-binary', default='csmith',
                           help=("Use a different csmith binary path"))
    gc_parser.add_argument('--output', '-o', required=True,
                           help=("Store the produced tests in this directory"))
    gc_parser.add_argument('--name', '-t', default='',
                           help=("Define the naming scheme for the output "
                                 "files. The files will be named "
                                 "[name]xx.ext, where xx is the id of the "
                                 "generated test. By default, [name] is empty,"
                                 " and xx is initialized as the smallest id"
                                 "such that no [name]yy.ext exists, with "
                                 "yy >= xx."))
    gc_parser.add_argument('--fast-csmith', action='store_true',
                           help=("Quickly generate a small (and probably "
                                 "uninterresting) Csmith source file. Useful "
                                 "for fast setup testing."))
    gc_parser.add_argument('--number', '-n', default='1',
                           help=("The number of test cases to generate. "
                                 "Defaults to 1."))
    gc_parser.set_defaults(main_func=main_gen_compile)

    parsed = parser.parse_args()
    if 'main_func' not in parsed:  # No subcommand
        parser.print_help()
        sys.exit(1)

    return parsed


def main_gen_compile(args):
    """ Main function handling gen-test """

    base_id = get_base_id(args.output, args.name)

    def naming_scheme(test_id):
        return os.path.join(
            args.output,
            "{}{:03}".format(args.name, test_id))

    for zeroed_test_id in range(int(args.number)):
        test_id = base_id + zeroed_test_id
        name_base = naming_scheme(test_id)
        print('> {}…'.format(name_base))
        generate_and_compile(name_base, args=args)


def main():
    args = process_args()
    args.main_func(args)


if __name__ == '__main__':
    main()
