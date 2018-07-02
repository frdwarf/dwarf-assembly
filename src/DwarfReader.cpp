#include "DwarfReader.hpp"

#include "plt_std_expr.hpp"

#include <fstream>
#include <fileno.hpp>
#include <set>

using namespace std;
using namespace dwarf;

typedef std::set<std::pair<int, core::FrameSection::register_def> >
    dwarfpp_row_t;

DwarfReader::DwarfReader(const string& path):
    root(fileno(ifstream(path)))
{}

SimpleDwarf DwarfReader::read() const {
    const core::FrameSection& fs = root.get_frame_section();
    SimpleDwarf output;

    for(auto fde_it = fs.fde_begin(); fde_it != fs.fde_end(); ++fde_it) {
        SimpleDwarf::Fde parsed_fde = read_fde(*fde_it);
        output.fde_list.push_back(parsed_fde);
    }

    return output;
}

SimpleDwarf::Fde DwarfReader::read_fde(const core::Fde& fde) const {
    SimpleDwarf::Fde output;
    output.fde_offset = fde.get_fde_offset();
    output.beg_ip = fde.get_low_pc();
    output.end_ip = fde.get_low_pc() + fde.get_func_length();

    auto rows = fde.decode().rows;
    const core::Cie& cie = *fde.find_cie();
    int ra_reg = cie.get_return_address_register_rule();

    for(const auto row_pair: rows) {
        SimpleDwarf::DwRow cur_row;

        cur_row.ip = row_pair.first.lower();

        const dwarfpp_row_t& row = row_pair.second;

        for(const auto& cell: row) {
            if(cell.first == DW_FRAME_CFA_COL3) {
                cur_row.cfa = read_register(cell.second);
            }
            else {
                try {
                    SimpleDwarf::MachineRegister reg_type =
                        from_dwarfpp_reg(cell.first, ra_reg);
                    switch(reg_type) {
                        case SimpleDwarf::REG_RBP:
                            cur_row.rbp = read_register(cell.second);
                            break;
                        case SimpleDwarf::REG_RBX:
                            cur_row.rbx = read_register(cell.second);
                            break;
                        case SimpleDwarf::REG_RA:
                            cur_row.ra = read_register(cell.second);
                            break;
                        default:
                            break;
                    }
                }
                catch(const UnsupportedRegister&) {} // Just ignore it.
            }
        }

        if(cur_row.cfa.type == SimpleDwarf::DwRegister::REG_UNDEFINED)
        {
            // Not set
            throw InvalidDwarf();
        }

        output.rows.push_back(cur_row);
    }

    return output;
}


SimpleDwarf::DwRegister DwarfReader::read_register(
        const core::FrameSection::register_def& reg
        ) const
{
    SimpleDwarf::DwRegister output;

    try {
        switch(reg.k) {
            case core::FrameSection::register_def::REGISTER:
                output.type = SimpleDwarf::DwRegister::REG_REGISTER;
                output.offset = reg.register_plus_offset_r().second;
                output.reg = from_dwarfpp_reg(
                        reg.register_plus_offset_r().first);
                break;

            case core::FrameSection::register_def::SAVED_AT_OFFSET_FROM_CFA:
                output.type = SimpleDwarf::DwRegister::REG_CFA_OFFSET;
                output.offset = reg.saved_at_offset_from_cfa_r();
                break;

            case core::FrameSection::register_def::INDETERMINATE:
            case core::FrameSection::register_def::UNDEFINED:
                output.type = SimpleDwarf::DwRegister::REG_UNDEFINED;
                break;

            case core::FrameSection::register_def::SAVED_AT_EXPR:
                if(is_plt_expr(reg))
                    output.type = SimpleDwarf::DwRegister::REG_PLT_EXPR;
                else
                    output.type = SimpleDwarf::DwRegister::REG_NOT_IMPLEMENTED;
                break;

            default:
                output.type = SimpleDwarf::DwRegister::REG_NOT_IMPLEMENTED;
                break;
        }
    }
    catch(const UnsupportedRegister& e) {
        output.type = SimpleDwarf::DwRegister::REG_NOT_IMPLEMENTED;
    }

    return output;
}

SimpleDwarf::MachineRegister DwarfReader::from_dwarfpp_reg(
        int reg_id,
        int ra_reg
        ) const
{
    if(reg_id == ra_reg)
        return SimpleDwarf::REG_RA;
    switch(reg_id) {
        case lib::DWARF_X86_64_RIP:
            return SimpleDwarf::REG_RIP;
        case lib::DWARF_X86_64_RSP:
            return SimpleDwarf::REG_RSP;
        case lib::DWARF_X86_64_RBP:
            return SimpleDwarf::REG_RBP;
        case lib::DWARF_X86_64_RBX:
            return SimpleDwarf::REG_RBX;
        default:
            throw UnsupportedRegister();
    }
}

static bool compare_dw_expr(
        const encap::loc_expr& e1,
        const encap::loc_expr& e2)
{
    const std::vector<encap::expr_instr>& e1_vec =
        static_cast<const vector<encap::expr_instr>&>(e1);
    const std::vector<encap::expr_instr>& e2_vec =
        static_cast<const vector<encap::expr_instr>&>(e2);

    return e1_vec == e2_vec;
}

bool DwarfReader::is_plt_expr(
        const core::FrameSection::register_def& reg) const
{
    if(reg.k != core::FrameSection::register_def::SAVED_AT_EXPR)
        return false;
    const encap::loc_expr& expr = reg.saved_at_expr_r();

    bool res = compare_dw_expr(expr, REFERENCE_PLT_EXPR);
    return res;
}
