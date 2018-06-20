#include "SimpleDwarfFilter.hpp"

SimpleDwarfFilter::SimpleDwarfFilter()
{}

SimpleDwarf SimpleDwarfFilter::apply(const SimpleDwarf& dw) const {
    // For convenience of future enhancements
    return do_apply(dw);
}

SimpleDwarf SimpleDwarfFilter::operator()(const SimpleDwarf& dw) {
    return apply(dw);
}
