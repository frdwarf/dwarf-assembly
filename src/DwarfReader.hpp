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

class DwarfReader {
    public:
        class InvalidDwarf: public std::exception {};

        /** Read the elf file located at `path`. */
        DwarfReader(const std::string& path);

        /** Actually read the ELF file, generating a `SimpleDwarf` output. */
        SimpleDwarf read() const;

    private: //meth
        SimpleDwarf::Fde read_fde(const dwarf::core::Fde& fde) const;

        SimpleDwarf::DwRegister read_register(
                const dwarf::core::FrameSection::register_def& reg) const;

        SimpleDwarf::MachineRegister from_dwarfpp_reg(
                int reg_id,
                int ra_reg=-1
                ) const;

        class UnsupportedRegister: public std::exception {};

    private:
        dwarf::core::root_die root;
};
