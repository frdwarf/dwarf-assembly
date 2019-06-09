#include "OverriddenRowFilter.hpp"

OverriddenRowFilter::OverriddenRowFilter(bool enable)
    : SimpleDwarfFilter(enable)
{}

SimpleDwarf OverriddenRowFilter::do_apply(const SimpleDwarf& dw) const {
    SimpleDwarf out;

    for(const auto& fde: dw.fde_list) {
        out.fde_list.push_back(SimpleDwarf::Fde());
        SimpleDwarf::Fde& cur_fde = out.fde_list.back();
        cur_fde.fde_offset = fde.fde_offset;
        cur_fde.beg_ip = fde.beg_ip;
        cur_fde.end_ip = fde.end_ip;

        if(fde.rows.empty())
            continue;

        for(size_t pos=0; pos < fde.rows.size(); ++pos) {
            const auto& row = fde.rows[pos];
            if(pos == fde.rows.size() - 1
                    || row.ip != fde.rows[pos+1].ip)
            {
                cur_fde.rows.push_back(row);
            }
        }
    }

    return out;
}
