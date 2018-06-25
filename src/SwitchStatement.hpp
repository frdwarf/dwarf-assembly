/** Contains an abstract switch statement, which can be turned to C code later
 * on. */

#pragma once

#include <string>
#include <vector>
#include <ostream>
#include <memory>

struct SwitchStatement {
    struct SwitchCase {
        uintptr_t low_bound, high_bound;
        std::string code;
    };

    std::string switch_var;
    std::string default_case;
    std::vector<SwitchCase> cases;
};

class AbstractSwitchCompiler {
    public:
        AbstractSwitchCompiler(int indent=0);
        void operator()(std::ostream& os, const SwitchStatement& sw);
        std::string operator()(const SwitchStatement& sw);

    protected:
        virtual void to_stream(
                std::ostream& os, const SwitchStatement& sw) = 0;
        std::string indent_str(const std::string& str) ;
        std::string indent() const;
        std::string endcl() const;

        int indent_count;
};
