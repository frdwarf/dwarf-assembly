#include "NativeSwitchCompiler.hpp"

using namespace std;

NativeSwitchCompiler::NativeSwitchCompiler(
        const SwitchStatement& sw, int indent):
    AbstractSwitchCompiler(sw, indent)
{}

void NativeSwitchCompiler::to_stream(ostream& os) {
    os << indent() << "switch(" << sw.switch_var << ") {\n";
    indent_count++;

    for(const auto& cur_case: sw.cases) {
        os << indent() << "case 0x"
           << hex << cur_case.low_bound << " ... 0x" << cur_case.high_bound
           << dec << ":\n";
        indent_count++;
        os << indent_str(cur_case.code);
        indent_count--;
    }

    os << indent() << "default:\n";
    indent_count++;
    os << indent_str(sw.default_case);
    indent_count--;
    os << indent() << "}\n";
    indent_count--;
}
