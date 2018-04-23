#include "SimpleDwarf.hpp"

static std::ostream& operator<<(
        std::ostream& out,
        SimpleDwarf::MachineRegister reg)
{
    switch(reg) {
        case SimpleDwarf::REG_RIP:
            out << "rip";
            break;
        case SimpleDwarf::REG_RSP:
            out << "rsp";
            break;
        case SimpleDwarf::REG_RBP:
            out << "rbp";
            break;
        case SimpleDwarf::REG_RA:
            out << "RA";
            break;
    }

    return out;
}

std::ostream& operator<<(std::ostream& out, const SimpleDwarf::DwRegister& reg)
{
    switch(reg.type) {
        case SimpleDwarf::DwRegister::REG_UNDEFINED:
            out << "u";
            break;
        case SimpleDwarf::DwRegister::REG_REGISTER:
            out << reg.reg
                << ((reg.offset >= 0) ? "+" : "")
                << reg.offset;
            break;
        case SimpleDwarf::DwRegister::REG_CFA_OFFSET:
            out << 'c'
                << ((reg.offset >= 0) ? "+" : "")
                << reg.offset;
            break;
        case SimpleDwarf::DwRegister::REG_NOT_IMPLEMENTED:
            out << 'X';
            break;
    }
    return out;
}

std::ostream& operator<<(std::ostream& out, const SimpleDwarf::DwRow& row) {
    out << std::hex << row.ip << std::dec
        << '\t' << row.cfa
        << '\t' << row.rbp
        << '\t' << row.ra;
    out << std::endl;
    return out;
}

std::ostream& operator<<(std::ostream& out, const SimpleDwarf::Fde& fde) {
    out << "FDE: "
        << std::hex << fde.beg_ip << " … " << fde.end_ip << std::dec
        << std::endl
        << "IP\tCFA\tRBP\tRA"
        << std::endl;
    for(const auto& row: fde.rows)
        out << row;
    return out;
}

std::ostream& operator<<(std::ostream& out, const SimpleDwarf& dwarf) {
    for(const auto& fde: dwarf.fde_list)
        out << fde << std::endl;
    return out;
}
