#include "DwarfReader.hpp"

#include "plt_std_expr.hpp"

#include <fstream>
#include <fileno.hpp>
#include <set>

using namespace std;
using namespace dwarf;

DwarfReader::DwarfReader(const string& path):
    root(fileno(ifstream(path)))
{}

// Debug function -- dumps an expression
static void dump_expr(const core::FrameSection::register_def& reg) {
    assert(reg.k == core::FrameSection::register_def::SAVED_AT_EXPR
           || reg.k == core::FrameSection::register_def::VAL_OF_EXPR);

    const encap::loc_expr& expr = reg.saved_at_expr_r();

    for(const auto& elt: expr) {
        fprintf(stderr, "(%02x, %02llx, %02llx, %02llx) :: ",
                elt.lr_atom, elt.lr_number, elt.lr_number2, elt.lr_offset);
    }
    fprintf(stderr, "\n");
}

SimpleDwarf DwarfReader::read() {
    const core::FrameSection& fs = root.get_frame_section();
    SimpleDwarf output;

    for(auto fde_it = fs.fde_begin(); fde_it != fs.fde_end(); ++fde_it) {
        SimpleDwarf::Fde parsed_fde = read_fde(*fde_it);
        output.fde_list.push_back(parsed_fde);
    }

    return output;
}

void DwarfReader::add_cell_to_row(
        const dwarf::core::FrameSection::register_def& reg,
        int reg_id,
        int ra_reg,
        SimpleDwarf::DwRow& cur_row)
{
    if(reg_id == DW_FRAME_CFA_COL3) {
        cur_row.cfa = read_register(reg);
    }
    else {
        try {
            SimpleDwarf::MachineRegister reg_type =
                from_dwarfpp_reg(reg_id, ra_reg);
            switch(reg_type) {
                case SimpleDwarf::REG_RBP:
                    cur_row.rbp = read_register(reg);
                    break;
                case SimpleDwarf::REG_RBX:
                    cur_row.rbx = read_register(reg);
                    break;
                case SimpleDwarf::REG_RA:
                    cur_row.ra = read_register(reg);
                    break;
                default:
                    break;
            }
        }
        catch(const UnsupportedRegister&) {} // Just ignore it.
    }
}

void DwarfReader::append_row_to_fde(
        const dwarfpp_row_t& row,
        uintptr_t row_addr,
        int ra_reg,
        SimpleDwarf::Fde& output)
{
    SimpleDwarf::DwRow cur_row;

    cur_row.ip = row_addr;

    for(const auto& cell: row) {
        add_cell_to_row(cell.second, cell.first, ra_reg, cur_row);
    }

    if(cur_row.cfa.type == SimpleDwarf::DwRegister::REG_UNDEFINED)
    {
        // Not set
        throw InvalidDwarf();
    }

    output.rows.push_back(cur_row);
}

template<typename Key, typename Value>
static std::set<std::pair<Key, Value> > map_to_setpair(
        const std::map<Key, Value>& src_map)
{
    std::set<std::pair<Key, Value> > out;
    for(const auto map_it: src_map) {
        out.insert(map_it);
    }
    return out;
}

void DwarfReader::append_results_to_fde(
        const dwarf::core::FrameSection::instrs_results& results,
        int ra_reg,
        SimpleDwarf::Fde& output)
{
    for(const auto row_pair: results.rows) {
        append_row_to_fde(
                row_pair.second,
                row_pair.first.lower(),
                ra_reg,
                output);
    }
    if(results.unfinished_row.size() > 0) {
        try {
            append_row_to_fde(
                    map_to_setpair(results.unfinished_row),
                    results.unfinished_row_addr,
                    ra_reg,
                    output);
        } catch(const InvalidDwarf&) {
            // Ignore: the unfinished_row can be undefined
        }
    }
}

SimpleDwarf::Fde DwarfReader::read_fde(const core::Fde& fde) {
    SimpleDwarf::Fde output;
    output.fde_offset = fde.get_fde_offset();
    output.beg_ip = fde.get_low_pc();
    output.end_ip = fde.get_low_pc() + fde.get_func_length();

    const core::Cie& cie = *fde.find_cie();
    int ra_reg = cie.get_return_address_register_rule();

    // CIE rows
    core::FrameSection cie_fs(root.get_dbg(), true);
    auto cie_rows = cie_fs.interpret_instructions(
            cie,
            fde.get_low_pc(),
            cie.get_initial_instructions(),
            cie.get_initial_instructions_length());

    // FDE rows
    auto fde_rows = fde.decode();

    // instrs
    append_results_to_fde(cie_rows, ra_reg, output);
    append_results_to_fde(fde_rows, ra_reg, output);

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
                else if(!interpret_simple_expr(reg, output))
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

bool DwarfReader::interpret_simple_expr(
        const dwarf::core::FrameSection::register_def& reg,
        SimpleDwarf::DwRegister& output
        ) const
{
    bool deref = false;
    if(reg.k == core::FrameSection::register_def::SAVED_AT_EXPR)
        deref = true;
    else if(reg.k == core::FrameSection::register_def::VAL_OF_EXPR)
        deref = false;
    else
        return false;

    const encap::loc_expr& expr = reg.saved_at_expr_r();
    if(expr.size() > 2 || expr.empty())
        return false;

    const auto& exp_reg = expr[0];
    if(0x70 <= exp_reg.lr_atom && exp_reg.lr_atom <= 0x8f) { // DW_OP_breg<n>
        int reg_id = exp_reg.lr_atom - 0x70;
        try {
            output.reg = from_dwarfpp_reg(reg_id, -1); // Cannot be CFA anyway
            output.offset = exp_reg.lr_number;
        } catch(const UnsupportedRegister& /* exn */) {
            return false; // Unsupported register
        }
    }

    if(expr.size() == 2) { // OK if deref
        if(expr[1].lr_atom == 0x06) { // deref
            if(deref)
                return false;
            deref = true;
        }
        else
            return false;
    }

    if(deref)
        return false; // TODO try stats? Mabye it's worth implementing
    output.type = SimpleDwarf::DwRegister::REG_REGISTER;
    return true;
}
