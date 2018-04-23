/** Generates C code from SimpleDwarf */

#pragma once

#include <ostream>

#include "SimpleDwarf.hpp"

class CodeGenerator {
    public:
        /// Unimplemented case
        class NotImplementedCase: public std::exception {};

        /** Create a CodeGenerator to generate code for the given dwarf, on the
         * given std::ostream object (eg. cout). */
        CodeGenerator(const SimpleDwarf& dwarf, std::ostream& os);

        /// Actually generate the code on the given stream
        void generate();

    private: //meth
        void gen_of_dwarf();
        void gen_of_fde(const SimpleDwarf::Fde& fde);
        void gen_of_row(
                const SimpleDwarf::DwRow& row,
                uintptr_t row_end);
        void gen_of_reg(
                const SimpleDwarf::DwRegister& reg);

    private:
        SimpleDwarf dwarf;
        std::ostream& os;
};
