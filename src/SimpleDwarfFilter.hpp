/** An abstract parent class for any SimpleDwarf filter, that is. a class that
 * transforms some SimpleDwarf into some other SimpleDwarf. */

#pragma once

#include <vector>

#include "SimpleDwarf.hpp"

class SimpleDwarfFilter {
    public:
        /** Constructor
         *
         * @param apply set to false to disable this filter. This setting is
         * convenient for compact filter-chaining code. */
        SimpleDwarfFilter(bool enable=true);

        /// Applies the filter
        SimpleDwarf apply(const SimpleDwarf& dw) const;

        /// Same as apply()
        SimpleDwarf operator()(const SimpleDwarf& dw);

    private:
        virtual SimpleDwarf do_apply(const SimpleDwarf& dw) const = 0;

        bool enable;
};
