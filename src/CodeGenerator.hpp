/** Generates C code from SimpleDwarf */

#pragma once

#include <ostream>
#include <functional>
#include <memory>

#include "SimpleDwarf.hpp"
#include "PcListReader.hpp"

class CodeGenerator {
    public:
        /// A function deriving a generated function name from a FDE
        typedef std::function<std::string(const SimpleDwarf::Fde&)>
            NamingScheme;

        /// Unimplemented case
        class NotImplementedCase: public std::exception {};

        class InvalidPcList: public std::exception {};

        /** Create a CodeGenerator to generate code for the given dwarf, on the
         * given std::ostream object (eg. cout). */
        CodeGenerator(const SimpleDwarf& dwarf, std::ostream& os,
                NamingScheme naming_scheme);

        /// Actually generate the code on the given stream
        void generate();

    private: //meth
        struct LookupEntry {
            std::string name;
            uintptr_t beg, end;
        };

        void gen_of_dwarf();
        void gen_unwind_func_header(const std::string& name);
        void gen_unwind_func_footer();
        void gen_function_of_fde(const SimpleDwarf::Fde& fde);
        void gen_switchpart_of_fde(const SimpleDwarf::Fde& fde);
        void gen_of_row(
                const SimpleDwarf::DwRow& row,
                uintptr_t row_end);
        void gen_case(uintptr_t low_bound, uintptr_t high_bound);
        void gen_of_reg(
                const SimpleDwarf::DwRegister& reg);

        void gen_lookup(const std::vector<LookupEntry>& entries);

    private:
        SimpleDwarf dwarf;
        std::ostream& os;
        std::unique_ptr<PcListReader> pc_list;

        NamingScheme naming_scheme;
};
