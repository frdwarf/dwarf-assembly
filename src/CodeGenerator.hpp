/** Generates C code from SimpleDwarf */

#pragma once

#include <ostream>
#include <functional>
#include <memory>

#include "SimpleDwarf.hpp"
#include "PcListReader.hpp"
#include "SwitchStatement.hpp"

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
                NamingScheme naming_scheme,
                AbstractSwitchCompiler* sw_compiler);

        /// Actually generate the code on the given stream
        void generate();

    private: //meth
        struct LookupEntry {
            std::string name;
            uintptr_t beg, end;
        };


        SwitchStatement gen_fresh_switch() const;
        void switch_append_fde(
                SwitchStatement& sw,
                const SimpleDwarf::Fde& fde) const;
        void gen_of_dwarf();
        void gen_unwind_func_header(const std::string& name);
        void gen_unwind_func_footer();
        void gen_function_of_fde(const SimpleDwarf::Fde& fde);
        void gen_of_row_content(
                const SimpleDwarf::DwRow& row,
                std::ostream& stream) const;
        void gen_of_reg(
                const SimpleDwarf::DwRegister& reg,
                std::ostream& stream) const;

        void gen_lookup(const std::vector<LookupEntry>& entries);

        bool check_reg_defined(const SimpleDwarf::DwRegister& reg) const;
        bool check_reg_valid(const SimpleDwarf::DwRegister& reg) const;

    private:
        SimpleDwarf dwarf;
        std::ostream& os;
        std::unique_ptr<PcListReader> pc_list;

        NamingScheme naming_scheme;

        std::unique_ptr<AbstractSwitchCompiler> switch_compiler;
};
