/** Ensures that there is no overlapping between FDEs. In case of slight
 * conflict, the higher-IP FDE has priority. */

#pragma once

#include "SimpleDwarf.hpp"
#include "SimpleDwarfFilter.hpp"

class AntiOverlapFilter: public SimpleDwarfFilter {
    public:
        AntiOverlapFilter(bool enable=true);

    private:
        SimpleDwarf do_apply(const SimpleDwarf& dw) const;
};
