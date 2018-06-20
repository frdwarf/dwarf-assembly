/** Ensures there is no "hole" between two consecutive PC ranges, to optimize
 * generated code size. */

#pragma once

#include "SimpleDwarf.hpp"
#include "SimpleDwarfFilter.hpp"

class PcHoleFiller: public SimpleDwarfFilter {
    public:
        PcHoleFiller();

    private:
        SimpleDwarf do_apply(const SimpleDwarf& dw) const;
};
