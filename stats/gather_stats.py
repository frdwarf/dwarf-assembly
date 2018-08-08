from elftools.common.exceptions import DWARFError
from pyelftools_overlay import system_elfs, get_cfi
from elftools.dwarf import callframe
import concurrent.futures
import random


from stats_accu import \
    StatsAccumulator, SingleFdeData, FdeData, DwarfInstr


class ProcessWrapper:
    def __init__(self, fct):
        self._fct = fct

    def __call__(self, elf_descr):
        try:
            path, elftype = elf_descr

            print("Processing {}…".format(path))

            cfi = get_cfi(path)
            if not cfi:
                return None

            return self._fct(path, elftype, cfi)
        except DWARFError:
            return None


def process_wrapper(fct):
    return ProcessWrapper(fct)


@process_wrapper
def process_elf(path, elftype, cfi):
    ''' Process a single file '''

    data = FdeData()

    for entry in cfi:
        if isinstance(entry, callframe.CIE):  # Is a CIE
            process_cie(entry, data)
        elif isinstance(entry, callframe.FDE):  # Is a FDE
            process_fde(entry, data)

    return SingleFdeData(path, elftype, data)


def incr_cell(table, key):
    ''' Increments table[key], or sets it to 1 if unset '''
    if key in table:
        table[key] += 1
    else:
        table[key] = 1


def process_cie(cie, data):
    ''' Process a CIE '''
    pass  # Nothing needed from a CIE


def process_fde(fde, data):
    ''' Process a FDE '''
    data.fde_count += 1

    decoded = fde.get_decoded()
    row_count = len(decoded.table)
    incr_cell(data.fde_with_lines, row_count)

    for row in decoded.table:
        process_reg(data.regs.cfa, row['cfa'])
        for entry in row:
            if isinstance(entry, int):
                process_reg(data.regs.regs[entry], row[entry])


def process_reg(out_reg, reg_def):
    ''' Process a register '''
    if isinstance(reg_def, callframe.CFARule):
        if reg_def.reg is not None:
            out_reg.regs[reg_def.reg] += 1
        else:
            pass  # TODO exprs
    else:
        incr_cell(out_reg.instrs, DwarfInstr.of_pyelf(reg_def.type))
        if reg_def.type == callframe.RegisterRule.REGISTER:
            out_reg.regs[reg_def.arg] += 1
        elif (reg_def.type == callframe.RegisterRule.EXPRESSION) \
                or (reg_def.type == callframe.RegisterRule.VAL_EXPRESSION):
            pass  # TODO exprs


def gather_system_files(config, sample_size=None):
    stats_accu = StatsAccumulator()

    elf_list = []
    for elf_path in system_elfs():
        elf_list.append(elf_path)

    if sample_size is not None:
        elf_list_sampled = random.sample(elf_list, sample_size)
        elf_list = elf_list_sampled

    if config.cores > 1:
        with concurrent.futures.ProcessPoolExecutor(max_workers=config.cores)\
                as executor:
            for fde in executor.map(process_elf, elf_list):
                stats_accu.add_fde(fde)
    else:
        for elf in elf_list:
            stats_accu.add_fde(process_elf(elf))

    return stats_accu


def map_system_files(mapper, sample_size=None, cores=None, include=None,
                     elflist=None):
    ''' `mapper` must take (path, elf_type, cfi) '''
    if cores is None:
        cores = 1
    if include is None:
        include = []

    mapper = process_wrapper(mapper)

    if elflist is None:
        elf_list = []
        for elf_path in system_elfs():
            elf_list.append(elf_path)

        if sample_size is not None:
            elf_list_sampled = random.sample(elf_list, sample_size)
            elf_list = elf_list_sampled

        elf_list += list(map(lambda x: (x, None), include))
    else:
        elf_list = elflist

    if cores > 1:
        with concurrent.futures.ProcessPoolExecutor(max_workers=cores)\
                as executor:
            out = executor.map(mapper, elf_list)
    else:
        out = map(mapper, elf_list)

    return out, elf_list
