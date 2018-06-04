#include "DwBenchmark.hpp"

#include <ostream>
#include <cassert>
#include <chrono>

#ifdef UNWIND_EH_ELF
#include "../../stack_walker/stack_walker.hpp"
#endif

#ifdef UNWIND_LIBUNWIND
#include <libunwind.h>
#endif

using namespace std;

unique_ptr<DwBenchmark> DwBenchmark::instance = nullptr;

DwBenchmark::DwBenchmark() {
#ifdef UNWIND_EH_ELF
    stack_walker_init();
#endif
}

DwBenchmark& DwBenchmark::get_instance() {
    if(!DwBenchmark::instance)
        instance = unique_ptr<DwBenchmark>(new DwBenchmark);
    return *instance;
}

void DwBenchmark::unwind_measure() {
#ifdef UNWIND_EH_ELF
    unwind_context_t context = get_context();
    SingleUnwind this_measure;
    this_measure.nb_frames = 0;

    auto start_time = chrono::high_resolution_clock::now();
    while(unwind_context(context)) {
        this_measure.nb_frames++;
    }
    auto end_time = chrono::high_resolution_clock::now();

    this_measure.nanoseconds = chrono::duration_cast<chrono::nanoseconds>(
            end_time - start_time).count();

    add_measure(this_measure);
#elif UNWIND_LIBUNWIND
    unw_context_t context;
    int rc = unw_getcontext(&context);
    if(rc < 0)
        assert(false);
    unw_cursor_t cursor;
    rc = unw_init_local(&cursor, &context);
    if(rc < 0)
        assert(false);

    SingleUnwind this_measure;
    this_measure.nb_frames = 0;

    auto start_time = chrono::high_resolution_clock::now();
    while(unw_step(&cursor) > 0) {
        this_measure.nb_frames++;
    }
    auto end_time = chrono::high_resolution_clock::now();

    this_measure.nanoseconds = chrono::duration_cast<chrono::nanoseconds>(
            end_time - start_time).count();

    add_measure(this_measure);
#else
    assert(false);
#endif
}

void DwBenchmark::add_measure(const SingleUnwind& measure) {
    measures.push_back(measure);
}
void DwBenchmark::add_measure(int nb_frames, size_t microseconds) {
    add_measure(SingleUnwind({nb_frames, microseconds}));
}

void DwBenchmark::format_output(std::ostream& os) const {
    size_t nb_unwind_frames = 0;
    size_t total_nanoseconds = 0;

    for(const auto& measure: measures) {
        nb_unwind_frames += measure.nb_frames;
        total_nanoseconds += measure.nanoseconds;
    }

    double clock_precision_ns =
        ((double)
            (1000*1000*1000 * std::chrono::high_resolution_clock::period::num))
        / ((double) std::chrono::high_resolution_clock::period::den);

    os << "Total time:        " << total_nanoseconds << "ns" << endl
       << "Total frames:      " << nb_unwind_frames << endl
       << "Avg frames/unwind: "
       << (double)nb_unwind_frames / (double)measures.size() << endl
       << "Avg time/frame:    "
       << (double)total_nanoseconds / nb_unwind_frames << "ns" << endl
       << "Clock precision:   " << clock_precision_ns << "ns" << endl;
}
