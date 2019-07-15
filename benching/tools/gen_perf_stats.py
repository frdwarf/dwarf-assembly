#!/usr/bin/env python3

""" Generates performance statistics for the eh_elf vs vanilla libunwind unwinding,
based on time series generated beforehand

First run
```bash
for i in $(seq 1 100); do
  perf report 2>&1 >/dev/null | tail -n 1 \
      | python ../hackbench/to_report_fmt.py \
          | sed 's/^.* & .* & \([0-9]*\) & .*$/\1/g'
done > $SOME_PLACE/$FLAVOUR_times
```

for each flavour (eh_elf, vanilla)

Then run this script, with `$SOME_PLACE` as argument.
"""

import numpy as np
import sys
import os


def read_series(path):
    with open(path, "r") as handle:
        for line in handle:
            yield int(line.strip())


FLAVOURS = ["eh_elf", "vanilla"]
WITH_NOCACHE = False

if "WITH_NOCACHE" in os.environ:
    WITH_NOCACHE = True
    FLAVOURS.append("vanilla-nocache")

path_format = os.path.join(sys.argv[1], "{}_times")
times = {}
avgs = {}
std_deviations = {}

for flv in FLAVOURS:
    times[flv] = list(read_series(path_format.format(flv)))
    avgs[flv] = sum(times[flv]) / len(times[flv])
    std_deviations[flv] = np.sqrt(np.var(times[flv]))

avg_ratio = avgs["vanilla"] / avgs["eh_elf"]
ratio_uncertainty = (
    1
    / avgs["eh_elf"]
    * (
        std_deviations["vanilla"]
        + avgs["vanilla"] / avgs["eh_elf"] * std_deviations["eh_elf"]
    )
)


def format_flv(flv_dict, formatter):
    out = ""
    for flv in FLAVOURS:
        val = flv_dict[flv]
        out += "* {}: {}\n".format(flv, formatter.format(val))
    return out


def get_ratios(avgs):
    def avg_of(flavour):
        return avgs[flavour] / avgs["eh_elf"]

    if WITH_NOCACHE:
        return "\n\tcached: {}\n\tuncached: {}".format(
            avg_of("vanilla"), avg_of("vanilla-nocache")
        )
    else:
        return avg_of("vanilla")


print(
    "Average time:\n{}\n"
    "Standard deviation:\n{}\n"
    "Average ratio: {}\n"
    "Ratio uncertainty: {}".format(
        format_flv(avgs, "{} ns"),
        format_flv(std_deviations, "{}"),
        get_ratios(avgs),
        ratio_uncertainty,
    )
)
