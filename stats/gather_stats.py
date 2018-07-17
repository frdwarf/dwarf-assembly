from pyelftools_overlay import system_elfs, get_cfi
from elftools.dwarf import callframe
import multiprocessing
import signal
import random

from stats_accu import \
    StatsAccumulator, SingleFdeData, \
    RegsList, FdeData, DwarfInstr


class FilesProcessor(multiprocessing.Process):
    def __init__(self, elf_list, shared_queue):
        super().__init__()
        self.stop_processing = False
        self.processed_counter = 0
        self.elf_list = elf_list
        self.shared_queue = shared_queue

    def stop_processing_now(self):
        self.stop_processing = True

    def run(self):
        pos = 0
        for descr in self.elf_list:
            if self.stop_processing:
                break
            self.process_single_file(descr, pos)
            pos += 1

        print("=== Finished {} ===".format(self.name))
        return 0

    def process_single_file(self, elf_descr, pos_in_list):
        if self.stop_processing:
            return

        elf_path, elf_type = elf_descr

        self.processed_counter += 1
        print('[{}, {}/{}] {}'.format(
            self.shared_queue.qsize(),
            pos_in_list + 1,
            len(self.elf_list),
            elf_path))
        self.process_file(elf_path, elf_type)

    def process_file(self, path, elftype):
        ''' Process a single file '''

        cfi = get_cfi(path)
        if not cfi:
            return None

        data = FdeData()

        for entry in cfi:
            if isinstance(entry, callframe.CIE):  # Is a CIE
                self.process_cie(entry, data)
            elif isinstance(entry, callframe.FDE):  # Is a FDE
                self.process_fde(entry, data)

        out = SingleFdeData(path, elftype, data)
        self.shared_queue.put(out)

    def incr_cell(self, table, key):
        ''' Increments table[key], or sets it to 1 if unset '''
        if key in table:
            table[key] += 1
        else:
            table[key] = 1

    def process_cie(self, cie, data):
        ''' Process a CIE '''
        pass  # Nothing needed from a CIE

    def process_fde(self, fde, data):
        ''' Process a FDE '''
        data.fde_count += 1

        decoded = fde.get_decoded()
        row_count = len(decoded.table)
        self.incr_cell(data.fde_with_lines, row_count)

        for row in decoded.table:
            self.process_reg(data.regs.cfa, row['cfa'])
            for entry in row:
                if isinstance(entry, int):
                    self.process_reg(data.regs.regs[entry], row[entry])

    def process_reg(self, out_reg, reg_def):
        ''' Process a register '''
        if isinstance(reg_def, callframe.CFARule):
            if reg_def.reg is not None:
                out_reg.regs[reg_def.reg] += 1
            else:
                pass  # TODO exprs
        else:
            self.incr_cell(out_reg.instrs, DwarfInstr.of_pyelf(reg_def.type))
            if reg_def.type == callframe.RegisterRule.REGISTER:
                out_reg.regs[reg_def.arg] += 1
            elif (reg_def.type == callframe.RegisterRule.EXPRESSION) \
                    or (reg_def.type == callframe.RegisterRule.VAL_EXPRESSION):
                pass  # TODO exprs


def gather_system_files(config, sample_size=None):
    stats_accu = StatsAccumulator()
    processors = []

    def signal_graceful_exit(sig, frame):
        ''' Stop gracefully now '''
        nonlocal processors

        print("Stopping after this ELF…")
        for processor in processors:
            processor.stop_processing_now()

    signal.signal(signal.SIGINT, signal_graceful_exit)

    elf_list = []
    for elf_path in system_elfs():
        elf_list.append(elf_path)

    if sample_size is not None:
        elf_list_sampled = random.sample(elf_list, sample_size)
        elf_list = elf_list_sampled

    elf_count = len(elf_list)
    elf_per_process = elf_count // config.cores
    elf_list_slices = []
    for i in range(config.cores - 1):
        elf_list_slices.append(
            elf_list[i * elf_per_process : (i+1) * elf_per_process])
    elf_list_slices.append(
        elf_list[(config.cores - 1) * elf_per_process
                 : config.cores * elf_per_process])

    shared_queue = multiprocessing.Queue(elf_count)

    for elf_range in elf_list_slices:
        processors.append(FilesProcessor(elf_range, shared_queue))

    if config.cores > 1:
        for processor in processors:
            processor.start()

        while True:
            for processor in processors:
                if processor.is_alive():
                    print("== Waiting {} ({} {}) ==".format(
                        processor.name, processor.exitcode,
                        processor.is_alive()))
                    processor.join(timeout=1)
                    if processor.exitcode is None:
                        break  # Loop around
                print("== Joined {} ==".format(processor.name))

            terminated = True
            for processor in processors:
                if processor.exitcode is None:
                    terminated = False
            if terminated:
                break
    else:
        processors[0].run()  # run(), not start(): in the same thread

    while not shared_queue.empty():  # Reliable because everything is joined
        stats_accu.add_fde(shared_queue.get_nowait())

    return stats_accu
