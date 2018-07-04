/** Deletes empty FDEs (that is, FDEs with no rows) from the FDEs collection.
 * This is used to ensure they do not interfere with PcHoleFiller and such. */

#pragma once

#include "SimpleDwarf.hpp"
#include "SimpleDwarfFilter.hpp"

class EmptyFdeDeleter: public SimpleDwarfFilter {
    public:
        EmptyFdeDeleter(bool enable=true);

    private:
        SimpleDwarf do_apply(const SimpleDwarf& dw) const;
};
