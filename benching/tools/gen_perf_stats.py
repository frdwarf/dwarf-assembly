#!/usr/bin/env python3

""" Generates performance statistics for the eh_elf vs vanilla libunwind unwinding,
based on time series generated beforehand

Intended to be run from `statistics.sh`
"""

from collections import namedtuple
import numpy as np
import sys
import os


Datapoint = namedtuple("Datapoint", ["nb_frames", "total_time", "avg_time"])


def read_series(path):
    with open(path, "r") as handle:
        for line in handle:
            nb_frames, total_time, avg_time = map(int, line.strip().split())
            yield Datapoint(nb_frames, total_time, avg_time)


FLAVOURS = ["eh_elf", "vanilla"]
WITH_NOCACHE = False

if "WITH_NOCACHE" in os.environ:
    WITH_NOCACHE = True
    FLAVOURS.append("vanilla-nocache")

path_format = os.path.join(sys.argv[1], "{}_times")
datapoints = {}
avg_times = {}
total_times = {}
avgs_total = {}
avgs = {}
std_deviations = {}
unwound_frames = {}

for flv in FLAVOURS:
    datapoints[flv] = list(read_series(path_format.format(flv)))
    avg_times[flv] = list(map(lambda x: x.avg_time, datapoints[flv]))
    total_times[flv] = list(map(lambda x: x.total_time, datapoints[flv]))
    avgs[flv] = sum(avg_times[flv]) / len(avg_times[flv])
    avgs_total[flv] = sum(total_times[flv]) / len(total_times[flv])
    std_deviations[flv] = np.sqrt(np.var(avg_times[flv]))

    cur_unwound_frames = list(map(lambda x: x.nb_frames, datapoints[flv]))
    unwound_frames[flv] = cur_unwound_frames[0]
    for run_id, unw_frames in enumerate(cur_unwound_frames[1:]):
        if unw_frames != unwound_frames[flv]:
            print(
                "{}, run {}: unwound {} frames, reference unwound {}".format(
                    flv, run_id + 1, unw_frames, unwound_frames[flv]
                ),
                file=sys.stderr,
            )

avg_ratio = avgs["vanilla"] / avgs["eh_elf"]
ratio_uncertainty = (
    1
    / avgs["eh_elf"]
    * (
        std_deviations["vanilla"]
        + avgs["vanilla"] / avgs["eh_elf"] * std_deviations["eh_elf"]
    )
)


def format_flv(flv_dict, formatter, alterator=None):
    out = ""
    for flv in FLAVOURS:
        val = flv_dict[flv]
        altered = alterator(val) if alterator else val
        out += "* {}: {}\n".format(flv, formatter.format(altered))
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
    "Unwound frames:\n{}\n"
    "Average whole unwinding time (one run):\n{}\n"
    "Average time to unwind one frame:\n{}\n"
    "Standard deviation:\n{}\n"
    "Average ratio: {}\n"
    "Ratio uncertainty: {}".format(
        format_flv(unwound_frames, "{}"),
        format_flv(avgs_total, "{} μs", alterator=lambda x: x // 1000),
        format_flv(avgs, "{} ns"),
        format_flv(std_deviations, "{}"),
        get_ratios(avgs),
        ratio_uncertainty,
    )
)
