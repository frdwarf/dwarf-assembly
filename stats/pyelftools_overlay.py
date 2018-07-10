""" Overlay of PyElfTools for quick access to what we want here """

from elftools.elf.elffile import ELFFile
from elftools.common.exceptions import ELFError, DWARFError
import os


def get_cfi(path):
    ''' Get the CFI entries from the ELF at the provided path '''

    try:
        with open(path, 'rb') as file_handle:
            elf_file = ELFFile(file_handle)

            if not elf_file.has_dwarf_info():
                return None

            dw_info = elf_file.get_dwarf_info()
            if dw_info.has_CFI():
                cfis = dw_info.CFI_entries()
            elif dw_info.has_EH_CFI():
                cfis = dw_info.EH_CFI_entries()
            else:
                return None
    except ELFError:
        return None
    except DWARFError:
        return None
    except PermissionError:
        return None

    return cfis


def system_elfs():
    ''' Iterator over system libraries '''

    def readlink_rec(path):
        if not os.path.islink(path):
            return path

        return readlink_rec(
            os.path.join(os.path.dirname(path),
                         os.readlink(path)))

    sysbin_dirs = [
        '/lib',
        '/usr/lib',
        '/usr/local/lib',
        '/bin',
        '/usr/bin',
        '/usr/local/bin',
        '/sbin',
    ]
    to_explore = sysbin_dirs

    seen_elfs = set()

    while to_explore:
        bindir = to_explore.pop()

        if not os.path.isdir(bindir):
            continue

        for direntry in os.scandir(bindir):
            if not direntry.is_file():
                if direntry.is_dir():
                    to_explore.append(direntry.path)
                continue

            canonical_name = readlink_rec(direntry.path)
            if canonical_name in seen_elfs:
                continue

            seen_elfs.add(canonical_name)
            yield canonical_name
