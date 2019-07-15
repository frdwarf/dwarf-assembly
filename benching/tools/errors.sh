#!/bin/bash

source "$(dirname $0)/common.sh"

TMP_FILE=$(mktemp)
if [ -z "$EH_ELFS_NAME" ]; then
    EH_ELFS_NAME="eh_elfs"
fi

function get_perf_output {
    envtype=$1
    source $ENV_APPLY "$envtype" "dbg"
    LD_LIBRARY_PATH="$BENCH_DIR/$EH_ELFS_NAME:$LD_LIBRARY_PATH" \
        UNW_DEBUG_LEVEL=15 \
        perf report -i "$BENCH_DIR/perf.data" 2>$TMP_FILE >/dev/null
    deactivate
}

function count_successes {
    cat $TMP_FILE | tail -n 1 | sed 's/^.*, \([0-9]*\) calls.*$/\1/g'
}

function count_total_calls {
    cat $TMP_FILE | grep -c "^  >.*step:.* returning"
}

function count_errors {
    cat $TMP_FILE | grep -c "^  >.*step:.* returning -"
}

function count_eh_fallbacks {
    cat $TMP_FILE | grep -c "step:.* falling back"
}

function count_vanilla_fallbacks {
    cat $TMP_FILE | grep -c "step:.* frame-chain"
}

function count_fallbacks_to_dwarf {
    cat $TMP_FILE | grep -c "step:.* fallback with"
}

function count_fallbacks_failed {
    cat $TMP_FILE | grep -c "step:.* dwarf_step also failed"
}

function count_fail_after_fallback_to_dwarf {
    cat $TMP_FILE \
        | "$(dirname $0)/line_patterns.py" \
            "fallback with" \
            "step:.* unw_step called" \
            ~"step:.* unw_step called" \
            "step:.* returning -" \
        | grep Complete -c
}

function report {
    flavour="$1"

    status_report "$flavour issues distribution"

    successes=$(count_successes)
    failures=$(count_errors)
    total=$(count_total_calls)

    if [ "$flavour" = "eh_elf" ]; then
        fallbacks=$(count_eh_fallbacks)
        fallbacks_to_dwarf=$(count_fallbacks_to_dwarf)
        fallbacks_to_dwarf_failed_after=$(count_fail_after_fallback_to_dwarf)
        fallbacks_failed=$(count_fallbacks_failed)
        fallbacks_to_heuristics="$(( $fallbacks \
            - $fallbacks_to_dwarf \
            - $fallbacks_failed))"
        echo -e "* success:\t\t\t\t$successes"
        echo -e "* fallback to DWARF:\t\t\t$fallbacks_to_dwarf"
        echo -e "* …of which failed at next step:\t$fallbacks_to_dwarf_failed_after"
        echo -e "* fallback to libunwind heuristics:\t$fallbacks_to_heuristics"
        computed_sum=$(( $successes + $fallbacks - $fallbacks_failed + $failures ))
    else
        fallbacks=$(count_vanilla_fallbacks)
        successes=$(( $successes - $fallbacks ))
        echo -e "* success:\t\t\t\t$successes"
        echo -e "* fallback to libunwind heuristics:\t$fallbacks"
        computed_sum=$(( $successes + $fallbacks + $failures ))
    fi
    echo -e "* fail to unwind:\t\t\t$failures"
    echo -e "* total:\t\t\t\t$total"
    if [ "$computed_sum" -ne "$total" ] ; then
        echo "-- WARNING: missing cases (computed sum $computed_sum != $total) --"
    fi
}

# eh_elf stats
get_perf_output "eh_elf"
report "eh_elf"

# Vanilla stats
get_perf_output "vanilla"
report "vanilla"

rm "$TMP_FILE"
