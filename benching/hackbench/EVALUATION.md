# Hackbench - evaluation

Artifacts saved in `evaluation_artifacts`.

## Performance

Using the command line

```bash
for i in $(seq 1 100); do
  perf report 2>&1 >/dev/null | tail -n 1 \
    | python to_report_fmt.py | sed 's/^.* & .* & \([0-9]*\) & .*$/\1/g'
done
```

we save a sequence of 100 performance readings to some file.

Samples:
* `eh_elf`:  135251 unw/exec
* `vanilla`: 138233 unw/exec

Average time/unw:
* `eh_elf`:   102 ns
* `vanilla`: 2443 ns

Standard deviation:
* `eh_elf`:  2 ns
* `vanilla`: 47 ns

Average ratio: 24
Ratio uncertainty: 1.0

## Distibution of `unw_step` issues

### `eh_elf` case

* success:                              135251 (97.7%)
* fallback to DWARF:                      1467  (1.0%)
* fallback to libunwind heuristics:        329  (0.2%)
* fail to unwind:                         1410  (1.0%)
* total:                                138457

### `vanilla` case

* success:                              138201 (98.9%)
* fallback to libunwind heuristics:         32  (0.0%)
* fail to unwind:                         1411  (1.0%)
* total:                                139644
