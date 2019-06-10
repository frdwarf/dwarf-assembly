# gzip - evaluation

Artifacts saved in `evaluation_artifacts`.

## Performance

Using the command line

```bash
for i in $(seq 1 100); do
  perf report 2>&1 >/dev/null | tail -n 1 \
    | python ../hackbench/to_report_fmt.py \
    | sed 's/^.* & .* & \([0-9]*\) & .*$/\1/g'
done
```

we save a sequence of 100 performance readings to some file.

Samples:
* `eh_elf`:  331134 unw/exec
* `vanilla`: 331144 unw/exec

Average time/unw:
* `eh_elf`:    83 ns
* `vanilla`: 1304 ns

Standard deviation:
* `eh_elf`:   2 ns
* `vanilla`: 24 ns

Average ratio: 15.7
Ratio uncertainty: 0.8

## Distibution of `unw_step` issues

### `eh_elf` case

* success:                              331134 (99.9%)
* fallback to DWARF:                         2  (0.0%)
* fallback to libunwind heuristics:          8  (0.0%)
* fail to unwind:                          379  (0.1%)
* total:                                331523

### `vanilla` case

* success:                              331136 (99.9%)
* fallback to libunwind heuristics:          8  (0.0%)
* fail to unwind:                          379  (0.1%)
* total:                                331523
