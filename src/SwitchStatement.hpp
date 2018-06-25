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
        AbstractSwitchCompiler(const SwitchStatement& sw,
                int indent=0);
        void operator()(std::ostream& os);
        std::string operator()();

    protected:
        virtual void to_stream(std::ostream& os) = 0;
        std::string indent_str(const std::string& str) ;
        std::string indent() const;
        std::string endcl() const;


        SwitchStatement sw;
        int indent_count;
};

class AbstractSwitchCompilerFactory {
    public:
        AbstractSwitchCompilerFactory();
        virtual std::shared_ptr<AbstractSwitchCompiler> operator()(
                const SwitchStatement& sw,
                int indent=0) = 0;
};

template<class Compiler>
class SwitchCompilerFactory : public AbstractSwitchCompilerFactory {
    public:
        virtual std::shared_ptr<AbstractSwitchCompiler> operator()(
                const SwitchStatement& sw,
                int indent=0)
        {
            return std::shared_ptr<AbstractSwitchCompiler>(
                    new Compiler(sw, indent));
        }
};
