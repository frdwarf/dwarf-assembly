/** This compile unit holds a few global variables controlling the code
 * generator's settings. These variables are used program-wide.
 */

#pragma once

#include <string>

namespace settings {
    /// Controls how the eh_elf switches are generated
    enum SwitchGenerationPolicy {
        SGP_SwitchPerFunc, ///< One switch per function, plus a lookup function
        SGP_GlobalSwitch ///< One big switch per ELF file
    };

    extern SwitchGenerationPolicy switch_generation_policy;
    extern std::string pc_list;
    extern bool enable_deref_arg;
    extern bool keep_holes; /**< Keep holes between FDEs. Larger eh_elf files,
                              but more accurate unwinding. */
}
