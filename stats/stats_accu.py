from elftools.dwarf import callframe
import enum
import subprocess
import re
import json
import collections

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


class ElfType(enum.Enum):
    ELF_LIB = enum.auto()
    ELF_BINARY = enum.auto()


class DwarfInstr(enum.Enum):
    @staticmethod
    def of_pyelf(val):
        _table = {
            callframe.RegisterRule.UNDEFINED: DwarfInstr.INSTR_UNDEF,
            callframe.RegisterRule.SAME_VALUE: DwarfInstr.INSTR_SAME_VALUE,
            callframe.RegisterRule.OFFSET: DwarfInstr.INSTR_OFFSET,
            callframe.RegisterRule.VAL_OFFSET: DwarfInstr.INSTR_VAL_OFFSET,
            callframe.RegisterRule.REGISTER: DwarfInstr.INSTR_REGISTER,
            callframe.RegisterRule.EXPRESSION: DwarfInstr.INSTR_EXPRESSION,
            callframe.RegisterRule.VAL_EXPRESSION:
                DwarfInstr.INSTR_VAL_EXPRESSION,
            callframe.RegisterRule.ARCHITECTURAL:
                DwarfInstr.INSTR_ARCHITECTURAL,
        }
        return _table[val]

    INSTR_UNDEF = enum.auto()
    INSTR_SAME_VALUE = enum.auto()
    INSTR_OFFSET = enum.auto()
    INSTR_VAL_OFFSET = enum.auto()
    INSTR_REGISTER = enum.auto()
    INSTR_EXPRESSION = enum.auto()
    INSTR_VAL_EXPRESSION = enum.auto()
    INSTR_ARCHITECTURAL = enum.auto()


def intify_dict(d):
    out = {}
    for key in d:
        try:
            nKey = int(key)
        except Exception:
            nKey = key

        try:
            out[nKey] = int(d[key])
        except ValueError:
            out[nKey] = d[key]
    return out


class RegData:
    def __init__(self, instrs=None, regs=None, exprs=None):
        if instrs is None:
            instrs = {}
        if regs is None:
            regs = [0]*17
        if exprs is None:
            exprs = {}
        self.instrs = intify_dict(instrs)
        self.regs = regs
        self.exprs = intify_dict(exprs)

    @staticmethod
    def map_dict_keys(fnc, dic):
        out = {}
        for key in dic:
            out[fnc(key)] = dic[key]
        return out

    def dump(self):
        return {
            'instrs': RegData.map_dict_keys(lambda x: x.value, self.instrs),
            'regs': self.regs,
            'exprs': self.exprs,
        }

    @staticmethod
    def load(data):
        return RegData(
            instrs=RegData.map_dict_keys(
                lambda x: DwarfInstr(int(x)),
                data['instrs']),
            regs=data['regs'],
            exprs=data['exprs'],
        )


class RegsList:
    def __init__(self, cfa=None, regs=None):
        if cfa is None:
            cfa = RegsList.fresh_reg()
        if regs is None:
            regs = [RegsList.fresh_reg() for _ in range(17)]
        self.cfa = cfa
        self.regs = regs

    @staticmethod
    def fresh_reg():
        return RegData()

    def dump(self):
        return {
            'cfa': RegData.dump(self.cfa),
            'regs': [RegData.dump(r) for r in self.regs],
        }

    @staticmethod
    def load(data):
        return RegsList(
            cfa=RegData.load(data['cfa']),
            regs=[RegData.load(r) for r in data['regs']],
        )


class FdeData:
    def __init__(self, fde_count=0, fde_with_lines=None, regs=None):
        if fde_with_lines is None:
            fde_with_lines = {}
        if regs is None:
            regs = RegsList()

        self.fde_count = fde_count
        self.fde_with_lines = intify_dict(fde_with_lines)
        self.regs = regs

    def dump(self):
        return {
            'fde_count': self.fde_count,
            'fde_with_lines': self.fde_with_lines,
            'regs': self.regs.dump(),
        }

    @staticmethod
    def load(data):
        return FdeData(
            fde_count=int(data['fde_count']),
            fde_with_lines=data['fde_with_lines'],
            regs=RegsList.load(data['regs']))


class SingleFdeData:
    def __init__(self, path, elf_type, data):
        self.path = path
        self.elf_type = elf_type
        self.data = data  # < of type FdeData

        self.gather_deps()

    def gather_deps(self):
        """ Collect ldd data on the binary """
        # self.deps = elf_so_deps(self.path)
        self.deps = []

    def dump(self):
        return {
            'path': self.path,
            'elf_type': self.elf_type.value,
            'data': self.data.dump()
        }

    @staticmethod
    def load(data):
        return SingleFdeData(
            data['path'],
            ElfType(int(data['elf_type'])),
            FdeData.load(data['data']))


class StatsAccumulator:
    def __init__(self):
        self.fdes = []

    def add_fde(self, fde_data):
        self.fdes.append(fde_data)

    def get_fdes(self):
        return self.fdes

    def add_stats_accu(self, stats_accu):
        for fde in stats_accu.get_fdes():
            self.add_fde(fde)

    def dump(self, path):
        dict_form = [fde.dump() for fde in self.fdes]
        print(dict_form)
        with open(path, 'w') as handle:
            handle.write(json.dumps(dict_form))

    @staticmethod
    def load(path):
        with open(path, 'r') as handle:
            text = handle.read()
        out = StatsAccumulator()
        out.fdes = [SingleFdeData.load(data) for data in json.loads(text)]
        return out
