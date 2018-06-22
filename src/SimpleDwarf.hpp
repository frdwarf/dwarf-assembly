/** SimpleDwarf - a simplified representation of Dwarf rules and table
 *
 * This class is made to handle a simple subset of the Dwarf table - the subset
 * that is the most ubiquitous. It should cover most of the real-life cases.
 */

#pragma once

#include <cstdint>
#include <vector> // We only need linear swipes, no need for anything fancier
#include <ostream>

struct SimpleDwarf {
    /** A machine register (eg. %rip) among the supported ones (x86_64 only
     * for now) */
    static const std::size_t HANDLED_REGISTERS_COUNT = 5;
    enum MachineRegister {
        REG_RIP, REG_RSP, REG_RBP, REG_RBX,
        REG_RA ///< A bit of cheating: not a machine register
    };

    static uint8_t to_shared_flag(MachineRegister mreg);

    struct DwRegister {
        /** Holds a single Dwarf register value */

        DwRegister(): type(REG_UNDEFINED), offset(0), reg(REG_RIP /* 0 */) {}

        /// Type of register (what does the expression mean?)
        enum Type {
            REG_UNDEFINED, /**< Undefined register (the value will be
                             defined at some later IP in the same DIE) */
            REG_REGISTER, ///< Value of a machine register plus offset
            REG_CFA_OFFSET, ///< Value stored at some offset from CFA
            REG_NOT_IMPLEMENTED ///< This type of register is not supported
        };

        Type type; ///< Type of this register
        int offset; ///< Offset from the expression, if applicable
        MachineRegister reg; ///< Machine register implied, if applicable

        friend std::ostream& operator<<(std::ostream &, const DwRegister&);
    };

    struct DwRow {
        uintptr_t ip; ///< Instruction pointer
        DwRegister cfa; ///< Canonical Frame Address
        DwRegister rbp; ///< Base pointer register
        DwRegister rbx; ///< RBX, sometimes used for unwinding
        DwRegister ra; ///< Return address

        friend std::ostream& operator<<(std::ostream &, const DwRow&);
    };

    struct Fde {
        uintptr_t fde_offset; ///< This FDE's offset in the original DWARF
        uintptr_t beg_ip, ///< This FDE's start instruction pointer incl.
                  end_ip; ///< This FDE's end instruction pointer excl.
        std::vector<DwRow> rows; ///< Dwarf rows for this FDE

        friend std::ostream& operator<<(std::ostream &, const Fde&);
    };

    std::vector<Fde> fde_list; ///< List of FDEs in this Dwarf

    friend std::ostream& operator<<(std::ostream &, const SimpleDwarf&);
};

/// Dumps this object to `out`
std::ostream& operator<<(std::ostream& out,
        const SimpleDwarf::DwRegister& reg);

/// Dumps this object to `out`
std::ostream& operator<<(std::ostream& out, const SimpleDwarf::DwRow& reg);

/// Dumps this object to `out`
std::ostream& operator<<(std::ostream& out, const SimpleDwarf::Fde& reg);

/// Dumps this object to `out`
std::ostream& operator<<(std::ostream& out, const SimpleDwarf& reg);
