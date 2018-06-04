#pragma once

#include <memory>
#include <vector>

class DwBenchmark {
    /** Singleton class - keeps track of benchmarks performed during a run */

    public:
        struct SingleUnwind {
            int nb_frames;
            size_t nanoseconds;
        };

        static DwBenchmark& get_instance();

        void unwind_measure(); ///< Unwind from here, and add the measure

        void add_measure(const SingleUnwind& measure); ///< Add this measure
        void add_measure(int nb_frames, size_t microseconds);

        /** Dump formatted output on `os` displaying stats about this benchmark
         * run */
        void format_output(std::ostream& os) const;

    private:
        DwBenchmark();

        static std::unique_ptr<DwBenchmark> instance;

        std::vector<SingleUnwind> measures;
};
