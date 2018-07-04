/** SimpleDwarfFilter to keep a unique Dwarf row for each group of consecutive
 * lines that are equivalent, that is, that share the same considered
 * registers' values. */

#pragma once

#include "SimpleDwarf.hpp"
#include "SimpleDwarfFilter.hpp"

class ConseqEquivFilter: public SimpleDwarfFilter {
    public:
        ConseqEquivFilter(bool enable=true);

    private:
        SimpleDwarf do_apply(const SimpleDwarf& dw) const;
};
