#include "EmptyFdeDeleter.hpp"

#include <algorithm>
#include <cstdio>

using namespace std;

EmptyFdeDeleter::EmptyFdeDeleter(bool enable): SimpleDwarfFilter(enable) {}

SimpleDwarf EmptyFdeDeleter::do_apply(const SimpleDwarf& dw) const {
    SimpleDwarf out(dw);

    auto fde = out.fde_list.begin();
    while(fde != out.fde_list.end()) {
        if(fde->rows.empty())
            fde = out.fde_list.erase(fde);
        else
            ++fde;
    }
    return out;
}
