/** Reads .pc_list files, containing a list of valid program counters for some
 * elf file.
 */

#pragma once

#include <vector>
#include <string>
#include <cstdint>

class PcListReader {
    public:
        /// Thrown when the file is somehow not readable
        class CannotReadFile: std::exception {};

        /// Thrown when the file contains bad content (probably not aligned 8B)
        class BadFormat: std::exception {};

        PcListReader(const std::string& path);

        /// Actually read and process the file
        void read();

        /// Access the PC list (filled iff `read` was called before)
        std::vector<uintptr_t>& get_list() { return pc_list; }

    private:
        std::string path;
        std::vector<uintptr_t> pc_list;
};
