#include "SimpleDwarfFilter.hpp"

SimpleDwarfFilter::SimpleDwarfFilter(bool enable): enable(enable)
{}

SimpleDwarf SimpleDwarfFilter::apply(const SimpleDwarf& dw) const {
    if(!enable)
        return dw;
    return do_apply(dw);
}

SimpleDwarf SimpleDwarfFilter::operator()(const SimpleDwarf& dw) {
    return apply(dw);
}
