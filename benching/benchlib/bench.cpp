#include "bench.h"

#include <iostream>
#include "DwBenchmark.hpp"

void bench_unwinding() {
    DwBenchmark::get_instance().unwind_measure();
}

void bench_dump_data() {
    DwBenchmark::get_instance().format_output(std::cout);
}
