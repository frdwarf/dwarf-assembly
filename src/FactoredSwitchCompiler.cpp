#include "FactoredSwitchCompiler.hpp"

#include <sstream>
#include <string>
using namespace std;

FactoredSwitchCompiler::FactoredSwitchCompiler(int indent):
    AbstractSwitchCompiler(indent), cur_label_id(0)
{
}

void FactoredSwitchCompiler::to_stream(
        std::ostream& os, const SwitchStatement& sw)
{
    JumpPointMap jump_points;

    gen_binsearch_tree(os, jump_points, sw.switch_var,
            sw.cases.begin(), sw.cases.end());

    os << indent_str(sw.default_case) << "\n"
       << indent() << "/* ===== LABELS  ============================== */\n\n";

    gen_jump_points_code(os, jump_points);
}

FactoredSwitchCompiler::FactorJumpPoint
FactoredSwitchCompiler::get_jump_point(
        FactoredSwitchCompiler::JumpPointMap& jump_map,
        const SwitchStatement::SwitchCaseContent& sw_case)
{
#ifdef STATS
    stats.refer_count++;
#endif//STATS

    auto pregen = jump_map.find(sw_case);
    if(pregen != jump_map.end()) // Was previously generated
        return pregen->second;

#ifdef STATS
    stats.generated_count++;
#endif//STATS

    // Wasn't generated previously -- we'll generate it here
    size_t label_id = cur_label_id++;
    ostringstream label_ss;
    label_ss << "_factor_" << label_id;
    FactorJumpPoint label_name = label_ss.str();

    jump_map.insert(make_pair(sw_case, label_name));
    return label_name;
}

void FactoredSwitchCompiler::gen_jump_points_code(std::ostream& os,
        const FactoredSwitchCompiler::JumpPointMap& jump_map)
{
    for(const auto& block: jump_map) {
        os << indent() << block.second << ":\n"
           << indent_str(block.first.code) << "\n\n";
    }
    os << indent() << "assert(0);\n";
}

void FactoredSwitchCompiler::gen_binsearch_tree(
        std::ostream& os,
        FactoredSwitchCompiler::JumpPointMap& jump_map,
        const std::string& sw_var,
        const FactoredSwitchCompiler::case_iterator_t& begin,
        const FactoredSwitchCompiler::case_iterator_t& end)
{
    size_t iter_delta = end - begin;
    if(iter_delta == 0)
        os << indent() << "assert(0);\n";
    else if(iter_delta == 1) {
        FactorJumpPoint jump_point = get_jump_point(
                jump_map, begin->content);
        os << indent() << "// IP=0x" << hex << begin->low_bound
                       << " ... 0x" << begin->high_bound << dec << "\n"
           << indent() << "goto " << jump_point << ";\n";
    }
    else {
        const case_iterator_t mid = begin + iter_delta / 2;

        os << indent() << "if(" << sw_var << " < 0x"
           << hex << mid->low_bound << dec << ") {\n";
        indent_count++;
        gen_binsearch_tree(os, jump_map, sw_var, begin, mid);
        indent_count--;
        os << indent() << "} else {\n";
        indent_count++;
        gen_binsearch_tree(os, jump_map, sw_var, mid, end);
        indent_count--;
        os << indent() << "}\n";
    }
}
