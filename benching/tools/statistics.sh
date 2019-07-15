#!/bin/bash

source "$(dirname $0)/common.sh"

TEMP_DIR="$(mktemp -d)"
NB_RUNS=10

function collect_perf_time_data {
    envtype=$1
    source $ENV_APPLY "$envtype" "release"
    LD_LIBRARY_PATH="$BENCH_DIR/eh_elfs:$LD_LIBRARY_PATH" \
        perf report -i "$BENCH_DIR/perf.data" 2>&1 >/dev/null \
        | tail -n 1 \
        | python "$(dirname $0)/to_report_fmt.py" \
        | sed 's/^.* & .* & \([0-9]*\) & .*$/\1/g'
    deactivate
}

function collect_perf_time_data_runs {
    envtype=$1
    outfile=$2
    status_report "Collecting $envtype data over $NB_RUNS runs"
    rm -f "$outfile"
    for run in $(seq 1 $NB_RUNS); do
        collect_perf_time_data "$envtype" >> "$outfile"
    done
}

eh_elf_data="$TEMP_DIR/eh_elf_times"
vanilla_data="$TEMP_DIR/vanilla_times"

collect_perf_time_data_runs "eh_elf" "$eh_elf_data"
collect_perf_time_data_runs "vanilla" "$vanilla_data"

status_report "benchmark statistics"
python "$(dirname "$0")/gen_perf_stats.py" "$TEMP_DIR"

rm -rf "$TEMP_DIR"
