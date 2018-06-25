/** Compiles a SwitchStatement to a native C switch */

#include "SwitchStatement.hpp"

class NativeSwitchCompiler: public AbstractSwitchCompiler {
    public:
        NativeSwitchCompiler(int indent=0);
    private:
        virtual void to_stream(std::ostream& os, const SwitchStatement& sw);
};
