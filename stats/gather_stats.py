from pyelftools_overlay import system_elfs
import pathos
import signal
import itertools

from stats_accu import StatsAccumulator


class FilesProcessor:
    def __init__(self, cores, stats_accu=None):
        self.stop_processing = False
        self._processed_counter = itertools.count()
        self.cores = cores

        if stats_accu is None:
            stats_accu = StatsAccumulator()
        self.stats_accu = stats_accu

    def stop_processing_now(self):
        self.stop_processing = True

    def next_counter(self):
        return self._processed_counter.__next__()

    def run(self, elf_list):
        self.elf_count = len(elf_list)
        with pathos.multiprocessing.ProcessPool(nodes=self.cores) as pool:
            pool.map(self.process_single_file, elf_list)

    def process_single_file(self, elf_path):
        if self.stop_processing:
            return

        cur_file_count = self.next_counter()
        print('> [{}/{} {:.0f}%] {}'.format(
            cur_file_count, self.elf_count,
            cur_file_count / self.elf_count * 100, elf_path))
        self.stats_accu.process_file(elf_path)


def gather_system_files(config):
    stats_accu = StatsAccumulator()
    processor = FilesProcessor(config.cores, stats_accu)

    def signal_graceful_exit(sig, frame):
        ''' Stop gracefully now '''
        nonlocal processor

        print("Stopping after this ELF…")
        processor.stop_processing_now()

    signal.signal(signal.SIGINT, signal_graceful_exit)

    elf_list = []
    for elf_path in system_elfs():
        elf_list.append(elf_path)

    processor.run(elf_list)

    return stats_accu
