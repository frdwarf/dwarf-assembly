""" Shared snippets between the various python scripts of this project """

import subprocess
import re
import os
from collections import namedtuple


def is_newer(file1, file2):
    ''' Returns True iff file1 is newer than file2 '''
    try:
        f1_mtime = os.path.getmtime(file1)
        f2_mtime = os.path.getmtime(file2)

        if f1_mtime > f2_mtime:
            return True
    except OSError:
        pass

    return False


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

    except subprocess.CalledProcessError as exn:
        raise Exception(
            ("Cannot get dependencies for {}: ldd terminated with exit code "
             "{}.").format(path, exn.returncode))


def do_remote(remote, command, send_files=None, retr_files=None):
    ''' Execute remotely (via ssh) a given command

    The command is executed on the machine described by `remote` (see ssh(1)).

    If `preload` is set, then the remote file at this path will be sourced
    before running any command, allowing to set PATH and other variables.

    send_files is a list of file paths that must be first copied at the root of
    a temporary directory on `remote` before running the command. Consider
    yourself jailed in that directory.

    retr_files is a list of files that will be copied to the local machine
    after the command is executed. Each list item can either be a string, which
    is both the path on the remote and the local machine; or a pair
    `(file_name, local_path)`. In the latter case, `file_name` is copied as
    `local_path/file_name` if `local_path` is a directory, or as `local_path`
    otherwise, on the local machine.
    '''

    if send_files is None:
        send_files = []
    if retr_files is None:
        retr_files = []

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
        if isinstance(descr, type('')):
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
