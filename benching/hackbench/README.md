# Running the benchmarks

Pick some name for your `eh_elfs` directory. We will call it `$EH_ELF_DIR`.

## Generate the `eh_elfs`

```bash
../../generate_eh_elf.py --deps -o "$EH_ELF_DIR" \
  --keep-holes -O2 --global-switch --enable-deref-arg hackbench
```

## Record a `perf` session

```bash
perf record --call-graph dwarf,4096 ./hackbench 10 process 100
```

You can arbitrarily increase the first number up to ~100 and the second to get
a longer session. This will most probably take all your computer's resources
while it is running.

## Set up the environment

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

### Actually get readings

```bash
perf report 2>&1 >/dev/null
```
