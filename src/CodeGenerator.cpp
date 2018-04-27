#include "CodeGenerator.hpp"
#include "gen_context_struct.hpp"

using namespace std;

static const char* PRELUDE =
"#include <assert.h>\n"
"\n"
;

CodeGenerator::CodeGenerator(
        const SimpleDwarf& dwarf,
        std::ostream& os,
        NamingScheme naming_scheme):
    dwarf(dwarf), os(os), naming_scheme(naming_scheme)
{}

void CodeGenerator::generate() {
    gen_of_dwarf();
}

void CodeGenerator::gen_of_dwarf() {
    os << CONTEXT_STRUCT_STR << '\n'
       << PRELUDE << '\n' << endl;

    vector<LookupEntry> lookup_entries;

    // A function per FDE
    for(const auto& fde: dwarf.fde_list) {
        LookupEntry cur_entry;
        cur_entry.name = naming_scheme(fde);
        cur_entry.beg = fde.beg_ip;
        cur_entry.end = fde.end_ip;
        lookup_entries.push_back(cur_entry);

        gen_of_fde(fde);
        os << endl;
    }

    gen_lookup(lookup_entries);
}

void CodeGenerator::gen_of_fde(const SimpleDwarf::Fde& fde) {
    os << "unwind_context_t "
       << naming_scheme(fde)
       << "(unwind_context_t ctx, uintptr_t pc) {\n"
       << "\tunwind_context_t out_ctx;\n"
       << "\tswitch(pc) {" << endl;

    for(size_t fde_row_id=0; fde_row_id < fde.rows.size(); ++fde_row_id)
    {
        uintptr_t up_bound = fde.end_ip;
        if(fde_row_id != fde.rows.size() - 1)
            up_bound = fde.rows[fde_row_id + 1].ip - 1;

        gen_of_row(fde.rows[fde_row_id], up_bound);
    }

    os << "\t\tdefault: assert(0);\n"
       << "\t}\n"
       << "}" << endl;
}

void CodeGenerator::gen_of_row(
        const SimpleDwarf::DwRow& row,
        uintptr_t row_end)
{
    os << "\t\tcase " << row.ip
       << " ... " << row_end << ":" << endl;

    os << "\t\t\t" << "out_ctx.rsp = ";
    gen_of_reg(row.cfa);
    os << ';' << endl;

    os << "\t\t\t" << "out_ctx.rbp = ";
    gen_of_reg(row.rbp);
    os << ';' << endl;

    os << "\t\t\t" << "out_ctx.rip = ";
    gen_of_reg(row.ra);
    os << ';' << endl;

    os << "\t\t\treturn " << "out_ctx" << ";" << endl;
}

static const char* ctx_of_dw_name(SimpleDwarf::MachineRegister reg) {
    switch(reg) {
        case SimpleDwarf::REG_RIP:
            throw CodeGenerator::NotImplementedCase();
        case SimpleDwarf::REG_RSP:
            return "ctx.rsp";
        case SimpleDwarf::REG_RBP:
            return "ctx.rbp";
        case SimpleDwarf::REG_RA:
            throw CodeGenerator::NotImplementedCase();
    }
    return "";
}

void CodeGenerator::gen_of_reg(const SimpleDwarf::DwRegister& reg) {
    switch(reg.type) {
        case SimpleDwarf::DwRegister::REG_UNDEFINED:
            os << "0";  // FIXME do better?
            break;
        case SimpleDwarf::DwRegister::REG_REGISTER:
            os << ctx_of_dw_name(reg.reg)
                << " + (" << reg.offset << ")";
            break;
        case SimpleDwarf::DwRegister::REG_CFA_OFFSET:
            os << "*((uintptr_t*)(out_ctx.rsp + ("
               << reg.offset
               << ")))";
            break;
        case SimpleDwarf::DwRegister::REG_NOT_IMPLEMENTED:
            os << "0; assert(0)";
            break;
    }
}

void CodeGenerator::gen_lookup(const std::vector<LookupEntry>& entries) {
    os << "_fde_func_t _fde_lookup(uintptr_t pc) {\n"
       << "\tswitch(pc) {" << endl;
    for(const auto& entry: entries) {
        os << "\t\tcase " << entry.beg << " ... " << entry.end - 1 << ":\n"
           << "\t\t\treturn &" << entry.name << ";" << endl;
    }
    os << "\t\tdefault: assert(0);\n"
       << "\t}\n"
       << "}" << endl;
}
