/** SimpleDwarfFilter to remove the first `n-1` rows of a block of `n`
 * contiguous rows that have the exact same address. */

#pragma once

#include "SimpleDwarf.hpp"
#include "SimpleDwarfFilter.hpp"

class OverriddenRowFilter: public SimpleDwarfFilter {
    public:
        OverriddenRowFilter(bool enable=true);

    private:
        SimpleDwarf do_apply(const SimpleDwarf& dw) const;
};
