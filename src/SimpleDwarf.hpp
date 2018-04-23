/** SimpleDwarf - a simplified representation of Dwarf rules and table
 *
 * This class is made to handle a simple subset of the Dwarf table - the subset
 * that is the most ubiquitous. It should cover most of the real-life cases.
 */

#pragma once

#include <cstdint>
#include <vector> // We only need linear swipes, no need for anything fancier

struct SimpleDwarf {
    /** A machine register (eg. %rip) among the supported ones (x86_64 only
     * for now) */
    static const std::size_t HANDLED_REGISTERS_COUNT = 3;
    enum MachineRegister {
        REG_RIP, REG_RSP, REG_RBP
    };

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
        uintptr_t offset; ///< Offset from the expression, if applicable
        MachineRegister reg; ///< Machine register implied, if applicable
    };

    struct DwRow {
        uintptr_t ip;
        DwRegister cfa;
        DwRegister regs[HANDLED_REGISTERS_COUNT];
    };

    struct Fde {
        uintptr_t beg_ip, end_ip;
        std::vector<DwRow> rows;
    };

    std::vector<Fde> fde_list;
};
