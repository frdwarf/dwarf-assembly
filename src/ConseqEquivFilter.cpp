#include "ConseqEquivFilter.hpp"

using namespace std;

ConseqEquivFilter::ConseqEquivFilter() {}

static bool equiv_reg(
        const SimpleDwarf::DwRegister& r1,
        const SimpleDwarf::DwRegister& r2)
{
    return r1.type == r2.type
        && r1.offset == r2.offset
        && r1.reg == r2.reg;
}

static bool equiv_row(
        const SimpleDwarf::DwRow& r1,
        const SimpleDwarf::DwRow& r2)
{
    return r1.ip == r2.ip
        && equiv_reg(r1.cfa, r2.cfa)
        && equiv_reg(r1.rbp, r2.rbp)
        && equiv_reg(r1.ra, r2.ra);
}

SimpleDwarf ConseqEquivFilter::do_apply(const SimpleDwarf& dw) const {
    SimpleDwarf out;

    for(const auto& fde: dw.fde_list) {
        out.fde_list.push_back(SimpleDwarf::Fde());
        SimpleDwarf::Fde& cur_fde = out.fde_list.back();
        cur_fde.fde_offset = fde.fde_offset;
        cur_fde.beg_ip = fde.beg_ip;
        cur_fde.end_ip = fde.end_ip;

        if(fde.rows.empty())
            continue;

        cur_fde.rows.push_back(fde.rows.front());
        for(size_t pos=1; pos < fde.rows.size(); ++pos) {
            const auto& row = fde.rows[pos];
            if(!equiv_row(row, cur_fde.rows.back())) {
                cur_fde.rows.push_back(row);
            }
        }
    }

    return out;
}
