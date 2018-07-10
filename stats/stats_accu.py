from elftools.dwarf import callframe
from pyelftools_overlay import get_cfi
from enum import Enum
import json
import subprocess
import re

from math import ceil


class ProportionFinder:
    ''' Finds figures such as median, etc. on the original structure of a
    dictionnary mapping a value to its occurrence count '''

    def __init__(self, count_per_value):
        self.cumulative = []
        prev_count = 0
        for key in sorted(count_per_value.keys()):
            n_count = prev_count + count_per_value[key]
            self.cumulative.append(
                (key, n_count))
            prev_count = n_count

        self.elem_count = prev_count

    def find_at_proportion(self, proportion):
        if not self.cumulative:  # Empty list
            return None

        low_bound = ceil(self.elem_count * proportion)

        def binsearch(beg, end):
            med = ceil((beg + end) / 2)

            if beg + 1 == end:
                return self.cumulative[beg][0]

            if self.cumulative[med - 1][1] < low_bound:
                return binsearch(med, end)
            return binsearch(beg, med)

        return binsearch(0, len(self.cumulative))


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


class ElfType(Enum):
    ELF_LIB = auto()
    ELF_BINARY = auto()


class SingleFdeData:
    def __init__(self, path, elf_type, data):
        self.path = path
        self.elf_type = elf_type
        self.data = data

        self.gather_deps()

    def gather_deps(self):
        """ Collect ldd data on the binary """
        self.deps = elf_so_deps(self.path)


class StatsAccumulator:
    def __init__(self):
        self.elf_count = 0
        self.fde_count = 0
        self.fde_row_count = 0
        self.fde_with_n_rows = {}

    def serialize(self, path):
        ''' Save the gathered data to `stream` '''

        notable_fields = [
            'elf_count',
            'fde_count',
            'fde_row_count',
            'fde_with_n_rows',
        ]
        out = {}
        for field in notable_fields:
            out[field] = self.__dict__[field]

        with open(path, 'wb') as stream:
            json.dump(out, stream)

    @staticmethod
    def unserialize(path):
        out = StatsAccumulator()
        with open(path, 'wb') as stream:
            data = json.load(stream)
        for field in data:
            out.field = data[field]
        return out

    def report(self):
        ''' Report on the statistics gathered '''

        self.fde_rows_proportion = ProportionFinder(
            self.fde_with_n_rows)

        rows = [
            ("ELFs analyzed", self.elf_count),
            ("FDEs analyzed", self.fde_count),
            ("FDE rows analyzed", self.fde_row_count),
            ("Avg. rows per FDE", self.fde_row_count / self.fde_count),
            ("Median rows per FDE",
             self.fde_rows_proportion.find_at_proportion(0.5)),
            ("Max rows per FDE", max(self.fde_with_n_rows.keys())),
        ]

        title_size = max(map(lambda x: len(x[0]), rows))
        line_format = "{:<" + str(title_size + 1) + "} {}"

        for row in rows:
            print(line_format.format(row[0], row[1]))

    def process_file(self, path):
        ''' Process a single file '''

        cfi = get_cfi(path)
        if not cfi:
            return

        self.elf_count += 1

        for entry in cfi:
            if isinstance(entry, callframe.CIE):  # Is a CIE
                self.process_cie(entry)
            elif isinstance(entry, callframe.FDE):  # Is a FDE
                self.process_fde(entry)

    def incr_cell(self, table, key):
        ''' Increments table[key], or sets it to 1 if unset '''
        if key in table:
            table[key] += 1
        else:
            table[key] = 1

    def process_cie(self, cie):
        ''' Process a CIE '''
        pass  # Nothing needed from a CIE

    def process_fde(self, fde):
        ''' Process a FDE '''
        self.fde_count += 1

        decoded = fde.get_decoded()
        row_count = len(decoded.table)
        self.fde_row_count += row_count
        self.incr_cell(self.fde_with_n_rows, row_count)
