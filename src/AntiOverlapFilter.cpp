#include "AntiOverlapFilter.hpp"

#include <algorithm>
#include <cstdio>

using namespace std;

AntiOverlapFilter::AntiOverlapFilter(bool enable): SimpleDwarfFilter(enable) {}

SimpleDwarf AntiOverlapFilter::do_apply(const SimpleDwarf& dw) const {
    SimpleDwarf out(dw);
    sort(out.fde_list.begin(), out.fde_list.end(),
            [](const SimpleDwarf::Fde& a, const SimpleDwarf::Fde& b) {
                return a.beg_ip < b.beg_ip;
            });

    for(size_t pos=0; pos < out.fde_list.size() - 1; ++pos) {
        if(out.fde_list[pos].end_ip >= out.fde_list[pos + 1].beg_ip) {
            fprintf(stderr,
                    "WARNING: overlapping FDEs %016lx-%016lx and %016lx-%016lx\n",
                    out.fde_list[pos].beg_ip, out.fde_list[pos].end_ip,
                    out.fde_list[pos + 1].beg_ip, out.fde_list[pos + 1].end_ip);
            out.fde_list[pos].end_ip = out.fde_list[pos + 1].beg_ip - 1;
        }
        out.fde_list[pos].end_ip = out.fde_list[pos + 1].beg_ip;
    }
    return out;
}
