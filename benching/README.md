# Benching `eh_elfs`

## Benchmark setup

Pick some name for your `eh_elfs` directory. We will call it `$EH_ELF_DIR`.

### Generate the `eh_elfs`

```bash
../../generate_eh_elf.py --deps -o "$EH_ELF_DIR" \
  --keep-holes -O2 --global-switch --enable-deref-arg "$BENCHED_BINARY"
```

### Record a `perf` session

```bash
perf record --call-graph dwarf,4096 "$BENCHED_BINARY" [args]
```

### Set up the environment

```bash
source ../../env/apply [vanilla | vanilla-nocache | *eh_elf] [dbg | *release]
```

The first value selects the version of libunwind you will be running, the
second selects whether you want to run in debug or release mode (use release to
get readings, debug to check for errors).

You can reset your environment to its previous state by running `deactivate`.

If you pick the `eh_elf` flavour, you will also have to

```bash
export LD_LIBRARY_PATH="$EH_ELF_DIR:$LD_LIBRARY_PATH"
```

## Extract results

### Base readings

**In release mode** (faster), run

```bash
perf report 2>&1 >/dev/null
```

with both `eh_elf` and `vanilla` shells. Compare average time.

### Getting debug output

```bash
UNW_DEBUG_LEVEL=5 perf report 2>&1 >/dev/null
```

### Total number of calls to `unw_step`

```bash
UNW_DEBUG_LEVEL=5 perf report 2>&1 >/dev/null | grep -c "step:.* returning"
```

### Total number of vanilla errors

With the `vanilla` context,

```bash
UNW_DEBUG_LEVEL=5 perf report 2>&1 >/dev/null | grep -c "step:.* returning -"
```

### Total number of fallbacks to original DWARF

With the `eh_elf` context,

```bash
UNW_DEBUG_LEVEL=5 perf report 2>&1 >/dev/null | grep -c "step:.* falling back"
```

### Total number of fallbacks to original DWARF that actually used DWARF

With the `eh_elf` context,

```bash
UNW_DEBUG_LEVEL=5 perf report 2>&1 >/dev/null | grep -c "step:.* fallback with"
```

### Get succeeded fallback locations

```bash
UNW_DEBUG_LEVEL=5 perf report 2>&1 >/dev/null \
  | grep "step: .* fallback with" -B 15 \
  | grep "In memory map" | sort | uniq -c
```
