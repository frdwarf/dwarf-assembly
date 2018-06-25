#include "SwitchStatement.hpp"

#include <sstream>

using namespace std;

AbstractSwitchCompiler::AbstractSwitchCompiler(
        const SwitchStatement& sw,
        int indent)
    : sw(sw), indent_count(indent)
{
}

void AbstractSwitchCompiler::operator()(ostream& os) {
    to_stream(os);
}

string AbstractSwitchCompiler::operator()() {
    ostringstream os;
    (*this)(os);
    return os.str();
}

std::string AbstractSwitchCompiler::indent_str(const std::string& str) {
    ostringstream out;

    int last_find = -1;
    size_t find_pos;
    while((find_pos = str.find('\n', last_find + 1)) != string::npos) {
        out << indent()
            << str.substr(last_find + 1, find_pos - last_find); // includes \n
        last_find = find_pos;
    }
    if(last_find + 1 < (int)str.size()) {
        out << indent()
            << str.substr(last_find + 1)
            << '\n';
    }
    return out.str();
}

std::string AbstractSwitchCompiler::indent() const {
    return string(indent_count, '\t');
}
std::string AbstractSwitchCompiler::endcl() const {
    return string("\n") + indent();
}

AbstractSwitchCompilerFactory::AbstractSwitchCompilerFactory() {}
