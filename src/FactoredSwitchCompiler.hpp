/** A switch generator that tries to factor out most of the redundancy between
 * switch blocks, generating manually a switch-like template */

#pragma once

#include "SwitchStatement.hpp"
#include <map>

class FactoredSwitchCompiler: public AbstractSwitchCompiler {
    public:
#ifdef STATS
        struct Stats {
            Stats(): generated_count(0), refer_count(0) {}
            int generated_count, refer_count;
        };

        const Stats& get_stats() const { return stats; }
#endif
        FactoredSwitchCompiler(int indent=0);

    private:
        typedef std::string FactorJumpPoint;
        typedef std::map<SwitchStatement::SwitchCaseContent, FactorJumpPoint>
            JumpPointMap;
        typedef std::vector<SwitchStatement::SwitchCase>::const_iterator
            case_iterator_t;

    private:
        virtual void to_stream(std::ostream& os, const SwitchStatement& sw);

        FactorJumpPoint get_jump_point(JumpPointMap& jump_map,
                const SwitchStatement::SwitchCaseContent& sw_case);

        void gen_jump_points_code(std::ostream& os,
                const JumpPointMap& jump_map);

        void gen_binsearch_tree(
                std::ostream& os,
                JumpPointMap& jump_map,
                const std::string& sw_var,
                const case_iterator_t& begin,
                const case_iterator_t& end);

        size_t cur_label_id;

#ifdef STATS
        Stats stats;
#endif//STATS
};
