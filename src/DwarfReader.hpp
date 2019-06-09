/** Use libdwarfpp to read the Dwarf data of some ELF, and output a SimpleDwarf
 * structure. */

#pragma once

#include <string>

#include <dwarfpp/lib.hpp>
#include <dwarfpp/regs.hpp>
#include <dwarfpp/frame.hpp>
#include <dwarfpp/attr.hpp>
#include <dwarfpp/root.hpp>

#include "SimpleDwarf.hpp"

typedef std::set<std::pair<int, dwarf::core::FrameSection::register_def> >
    dwarfpp_row_t;

class DwarfReader {
    public:
        class InvalidDwarf: public std::exception {};

        /** Read the elf file located at `path`. */
        DwarfReader(const std::string& path);

        /** Actually read the ELF file, generating a `SimpleDwarf` output. */
        SimpleDwarf read();

    private: //meth
        SimpleDwarf::Fde read_fde(const dwarf::core::Fde& fde);

        void append_results_to_fde(
                const dwarf::core::FrameSection::instrs_results& results,
                int ra_reg,
                SimpleDwarf::Fde& output);

        SimpleDwarf::DwRegister read_register(
                const dwarf::core::FrameSection::register_def& reg) const;

        void add_cell_to_row(
                const dwarf::core::FrameSection::register_def& reg,
                int reg_id,
                int ra_reg,
                SimpleDwarf::DwRow& cur_row);

        void append_row_to_fde(
                const dwarfpp_row_t& row,
                uintptr_t row_addr,
                int ra_reg,
                SimpleDwarf::Fde& output);

        SimpleDwarf::MachineRegister from_dwarfpp_reg(
                int reg_id,
                int ra_reg=-1
                ) const;

        bool is_plt_expr(
                const dwarf::core::FrameSection::register_def& reg) const;

        bool interpret_simple_expr(
                const dwarf::core::FrameSection::register_def& reg,
                SimpleDwarf::DwRegister& output
                ) const;

        class UnsupportedRegister: public std::exception {};

    private:
        dwarf::core::root_die root;
};
