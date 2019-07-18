#include "FactoredSwitchCompiler.hpp"

#include <sstream>
#include <string>
#include <iostream>
using namespace std;

FactoredSwitchCompiler::FactoredSwitchCompiler(int indent):
    AbstractSwitchCompiler(indent), cur_label_id(0)
{
}

void FactoredSwitchCompiler::to_stream(
        std::ostream& os, const SwitchStatement& sw)
{
    if(sw.cases.empty()) {
        std::cerr << "WARNING: empty unwinding data!\n";
        os
            << indent_str("/* WARNING: empty unwinding data! */\n")
            << indent_str(sw.default_case) << "\n";
        return;
    }
    JumpPointMap jump_points;

    uintptr_t low_bound = sw.cases.front().low_bound,
              high_bound = sw.cases.back().high_bound;

    os << indent() << "if("
       << "0x" << hex << low_bound << " <= " << sw.switch_var
       << " && " << sw.switch_var << " <= 0x" << high_bound << dec << ") {\n";
    indent_count++;

    gen_binsearch_tree(os, jump_points, sw.switch_var,
            sw.cases.begin(), sw.cases.end(),
            make_pair(low_bound, high_bound));

    indent_count--;
    os << indent() << "}\n";

    os << indent() << "_factor_default:\n"
       << indent_str(sw.default_case) << "\n"
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
        const FactoredSwitchCompiler::case_iterator_t& end,
        const loc_range_t& loc_range)
{
    size_t iter_delta = end - begin;
    if(iter_delta == 0)
        os << indent() << "assert(0);\n";
    else if(iter_delta == 1) {
        FactorJumpPoint jump_point = get_jump_point(
                jump_map, begin->content);
        if(loc_range.first < begin->low_bound) {
            os << indent() << "if(" << sw_var << " < 0x"
               << hex << begin->low_bound << dec
               << ") goto _factor_default; "
               << "// IP=0x" << hex << loc_range.first << " ... 0x"
               << begin->low_bound - 1 << "\n";
        }
        if(begin->high_bound + 1 < loc_range.second) {
            os << indent() << "if(0x" << hex << begin->high_bound << dec
               << " < " << sw_var << ") goto _factor_default; "
               << "// IP=0x" << hex << begin->high_bound + 1 << " ... 0x"
               << loc_range.second - 1 << "\n";
        }
        os << indent() << "// IP=0x" << hex << begin->low_bound
                       << " ... 0x" << begin->high_bound << dec << "\n"
           << indent() << "goto " << jump_point << ";\n";
    }
    else {
        const case_iterator_t mid = begin + iter_delta / 2;

        os << indent() << "if(" << sw_var << " < 0x"
           << hex << mid->low_bound << dec << ") {\n";
        indent_count++;
        gen_binsearch_tree(
                os, jump_map, sw_var, begin, mid,
                make_pair(loc_range.first, mid->low_bound));
        indent_count--;
        os << indent() << "} else {\n";
        indent_count++;
        gen_binsearch_tree(
                os, jump_map, sw_var, mid, end,
                make_pair(mid->low_bound, loc_range.second));
        indent_count--;
        os << indent() << "}\n";
    }
}
