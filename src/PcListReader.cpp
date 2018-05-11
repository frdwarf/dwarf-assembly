#include "PcListReader.hpp"

#include <fstream>

using namespace std;

PcListReader::PcListReader(const std::string& path): path(path)
{}

void PcListReader::read() {
    ifstream handle(path, ifstream::in | ifstream::binary);
    if(!handle.good()) {
        throw PcListReader::CannotReadFile();
    }

    uintptr_t last_pc;
    unsigned char buffer[8];

    while(!handle.eof()) {
        handle.read((char*)buffer, 8);
        if(handle.gcount() != 8)
            throw PcListReader::BadFormat();

        last_pc = 0;
        for(int shift = 0; shift < 8; ++shift) {
            uintptr_t c_byte = buffer[shift];
            c_byte <<= 8*shift;
            last_pc |= c_byte;
        }
        pc_list.push_back(last_pc);
    }
}
