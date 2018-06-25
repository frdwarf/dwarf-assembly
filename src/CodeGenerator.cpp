#include "CodeGenerator.hpp"
#include "gen_context_struct.hpp"
#include "settings.hpp"
#include "../shared/context_struct.h"

#include <algorithm>
#include <limits>
#include <exception>
#include <sstream>

using namespace std;

class UnhandledRegister: public std::exception {};

static const char* PRELUDE =
"#include <assert.h>\n"
"\n"
;

struct UnwFlags {
    UnwFlags():
        error(false), rip(false), rsp(false), rbp(false), rbx(false) {}


    bool error, rip, rsp, rbp, rbx;

    uint8_t to_uint8() const {
        uint8_t out = 0;
        if(rip)
            out |= (1 << UNWF_RIP);
        if(rsp)
            out |= (1 << UNWF_RSP);
        if(rbp)
            out |= (1 << UNWF_RBP);
        if(rbx)
            out |= (1 << UNWF_RBX);
        if(error)
            out |= (1 << UNWF_ERROR);

        return out;
    }
};


CodeGenerator::CodeGenerator(
        const SimpleDwarf& dwarf,
        std::ostream& os,
        NamingScheme naming_scheme,
        AbstractSwitchCompiler* sw_compiler) :
    dwarf(dwarf), os(os), pc_list(nullptr),
    naming_scheme(naming_scheme), switch_compiler(sw_compiler)
{
    if(!settings::pc_list.empty()) {
        pc_list = make_unique<PcListReader>(settings::pc_list);
        pc_list->read();
    }
}

void CodeGenerator::generate() {
    gen_of_dwarf();
}

SwitchStatement CodeGenerator::gen_fresh_switch() const {
    SwitchStatement out;
    out.switch_var = "pc";
    ostringstream default_oss;
    UnwFlags flags;
    flags.error = true;
    default_oss
        << "out_ctx.flags = " << (int) flags.to_uint8() << "u;\n"
        << "return out_ctx;\n";
    out.default_case = default_oss.str();
    return out;
}

void CodeGenerator::switch_append_fde(
        SwitchStatement& sw,
        const SimpleDwarf::Fde& fde) const
{
    for(size_t fde_row_id=0; fde_row_id < fde.rows.size(); ++fde_row_id)
    {
        SwitchStatement::SwitchCase sw_case;

        uintptr_t up_bound = fde.end_ip - 1;
        if(fde_row_id != fde.rows.size() - 1)
            up_bound = fde.rows[fde_row_id + 1].ip - 1;
        sw_case.low_bound = fde.rows[fde_row_id].ip;
        sw_case.high_bound = up_bound;

        ostringstream case_oss;
        gen_of_row_content(fde.rows[fde_row_id], case_oss);
        sw_case.content.code = case_oss.str();

        sw.cases.push_back(sw_case);
    }
}

void CodeGenerator::gen_of_dwarf() {
    os << CONTEXT_STRUCT_STR << '\n'
       << PRELUDE << '\n' << endl;

    switch(settings::switch_generation_policy) {
        case settings::SGP_SwitchPerFunc:
        {
            vector<LookupEntry> lookup_entries;

            // A function per FDE
            for(const auto& fde: dwarf.fde_list) {
                LookupEntry cur_entry;
                cur_entry.name = naming_scheme(fde);
                cur_entry.beg = fde.beg_ip;
                cur_entry.end = fde.end_ip;
                lookup_entries.push_back(cur_entry);

                gen_function_of_fde(fde);
                os << endl;
            }

            gen_lookup(lookup_entries);
            break;
        }
        case settings::SGP_GlobalSwitch:
        {
            gen_unwind_func_header("_eh_elf");
            SwitchStatement sw_stmt = gen_fresh_switch();
            for(const auto& fde: dwarf.fde_list)
                switch_append_fde(sw_stmt, fde);
            (*switch_compiler)(os, sw_stmt);
            gen_unwind_func_footer();
            break;
        }
    }
}

void CodeGenerator::gen_unwind_func_header(const std::string& name) {
    string deref_arg;
    if(settings::enable_deref_arg)
        deref_arg = ", deref_func_t deref";

    os << "unwind_context_t "
       << name
       << "(unwind_context_t ctx, uintptr_t pc" << deref_arg << ") {\n"
       << "\tunwind_context_t out_ctx;" << endl;
}

void CodeGenerator::gen_unwind_func_footer() {
    os << "}" << endl;
}

void CodeGenerator::gen_function_of_fde(const SimpleDwarf::Fde& fde) {
    gen_unwind_func_header(naming_scheme(fde));

    SwitchStatement sw_stmt = gen_fresh_switch();
    switch_append_fde(sw_stmt, fde);
    (*switch_compiler)(os, sw_stmt);

    gen_unwind_func_footer();
}

void CodeGenerator::gen_of_row_content(
        const SimpleDwarf::DwRow& row,
        std::ostream& stream) const
{
    UnwFlags flags;

    try {
        if(!check_reg_valid(row.ra)) {
            // RA might be undefined (last frame), but if it is defined and we
            // don't implement it (eg. EXPR), it is an error
            flags.error = true;
            goto write_flags;
        }

        if(check_reg_valid(row.cfa)) {
            flags.rsp = true;
            stream << "out_ctx.rsp = ";
            gen_of_reg(row.cfa, stream);
            stream << ';' << endl;
        }
        else { // rsp is required (CFA)
            flags.error = true;
            goto write_flags;
        }

        if(check_reg_defined(row.rbp)) {
            flags.rbp = true;
            stream << "out_ctx.rbp = ";
            gen_of_reg(row.rbp, stream);
            stream << ';' << endl;
        }

        if(check_reg_defined(row.ra)) {
            flags.rip = true;
            stream << "out_ctx.rip = ";
            gen_of_reg(row.ra, stream);
            stream << ';' << endl;
        }

        if(check_reg_defined(row.rbx)) {
            flags.rbx = true;
            stream << "out_ctx.rbx = ";
            gen_of_reg(row.rbx, stream);
            stream << ';' << endl;
        }
    } catch(const UnhandledRegister& exn) {
        // This should not happen, since we check_reg_*, but heh.
        flags.error = true;
        stream << ";\n";
    }

write_flags:
    stream << "out_ctx.flags = " << (int)flags.to_uint8() << "u;" << endl;

    stream << "return " << "out_ctx" << ";" << endl;
}

static const char* ctx_of_dw_name(SimpleDwarf::MachineRegister reg) {
    switch(reg) {
        case SimpleDwarf::REG_RIP:
            throw CodeGenerator::NotImplementedCase();
        case SimpleDwarf::REG_RSP:
            return "ctx.rsp";
        case SimpleDwarf::REG_RBP:
            return "ctx.rbp";
        case SimpleDwarf::REG_RBX:
            return "ctx.rbx";
        case SimpleDwarf::REG_RA:
            throw CodeGenerator::NotImplementedCase();
    }
    return "";
}

bool CodeGenerator::check_reg_defined(
        const SimpleDwarf::DwRegister& reg) const
{
    switch(reg.type) {
        case SimpleDwarf::DwRegister::REG_UNDEFINED:
        case SimpleDwarf::DwRegister::REG_NOT_IMPLEMENTED:
            return false;
        default:
            return true;
    }
}
bool CodeGenerator::check_reg_valid(const SimpleDwarf::DwRegister& reg) const {
    return reg.type != SimpleDwarf::DwRegister::REG_NOT_IMPLEMENTED;
}

void CodeGenerator::gen_of_reg(const SimpleDwarf::DwRegister& reg,
        ostream& stream) const
{
    switch(reg.type) {
        case SimpleDwarf::DwRegister::REG_UNDEFINED:
            // This function is not supposed to be called on an undefined
            // register
            throw UnhandledRegister();
            break;
        case SimpleDwarf::DwRegister::REG_REGISTER:
            stream << ctx_of_dw_name(reg.reg)
                << " + (" << reg.offset << ")";
            break;
        case SimpleDwarf::DwRegister::REG_CFA_OFFSET: {
            if(settings::enable_deref_arg) {
                stream << "deref(out_ctx.rsp + ("
                   << reg.offset
                   << "))";
            }
            else {
                stream << "*((uintptr_t*)(out_ctx.rsp + ("
                   << reg.offset
                   << ")))";
            }
            break;
        }
        case SimpleDwarf::DwRegister::REG_NOT_IMPLEMENTED:
            stream << "0";
            throw UnhandledRegister();
            break;
    }
}

void CodeGenerator::gen_lookup(const std::vector<LookupEntry>& entries) {
    os << "_fde_func_t _fde_lookup(uintptr_t pc) {\n"
       << "\tswitch(pc) {" << endl;
    for(const auto& entry: entries) {
        os << "\t\tcase " << std::hex << "0x" << entry.beg
           << " ... 0x" << entry.end - 1 << ":\n" << std::dec
           << "\t\t\treturn &" << entry.name << ";" << endl;
    }
    os << "\t\tdefault: assert(0);\n"
       << "\t}\n"
       << "}" << endl;
}
