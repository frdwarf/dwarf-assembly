""" Overlay of PyElfTools for quick access to what we want here """

from elftools.elf.elffile import ELFFile
from elftools.common.exceptions import ELFError, DWARFError
from stats_accu import ElfType
import os


ELF_BLACKLIST = [
    '/usr/lib/libavcodec.so',
]


def get_cfi(path):
    ''' Get the CFI entries from the ELF at the provided path '''

    try:
        with open(path, 'rb') as file_handle:
            elf_file = ELFFile(file_handle)

            if not elf_file.has_dwarf_info():
                print("No DWARF")
                return None

            dw_info = elf_file.get_dwarf_info()
            if dw_info.has_CFI():
                cfis = dw_info.CFI_entries()
            elif dw_info.has_EH_CFI():
                cfis = dw_info.EH_CFI_entries()
            else:
                print("No CFI")
                return None
    except ELFError:
        print("ELF Error")
        return None
    except DWARFError:
        print("DWARF Error")
        return None
    except PermissionError:
        print("Permission Error")
        return None
    except KeyError:
        print("Key Error")
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
        ('/lib', ElfType.ELF_LIB),
        ('/usr/lib', ElfType.ELF_LIB),
        ('/usr/local/lib', ElfType.ELF_LIB),
        ('/bin', ElfType.ELF_BINARY),
        ('/usr/bin', ElfType.ELF_BINARY),
        ('/usr/local/bin', ElfType.ELF_BINARY),
        ('/sbin', ElfType.ELF_BINARY),
    ]
    to_explore = sysbin_dirs

    seen_elfs = set()

    while to_explore:
        bindir, elftype = to_explore.pop()

        if not os.path.isdir(bindir):
            continue

        for direntry in os.scandir(bindir):
            if not direntry.is_file():
                if direntry.is_dir():
                    to_explore.append((direntry.path, elftype))
                continue

            canonical_name = readlink_rec(direntry.path)
            for blacked in ELF_BLACKLIST:
                if canonical_name.startswith(blacked):
                    continue
            if canonical_name in seen_elfs:
                continue

            valid_elf = True
            try:
                with open(canonical_name, 'rb') as handle:
                    magic_bytes = handle.read(4)
                    if magic_bytes != b'\x7fELF':
                        valid_elf = False
                    elf_class = handle.read(1)
                    if elf_class != b'\x02':  # ELF64
                        valid_elf = False
            except Exception:
                continue
            if not valid_elf:
                continue

            if not os.path.isfile(canonical_name):
                continue

            seen_elfs.add(canonical_name)
            yield (canonical_name, elftype)
