# Dwarf Assembly

A compiler from DWARF unwinding data to native x86\_64 binaries.

This repository also contains various experiments, tools, benchmarking scripts,
stats scripts, etc. to work on this compiler.

## Dependencies

As of now, this project relies on the following libraries:

* libelf
* libdwarf
* [libdwarfpp](https://github.com/stephenrkell/libdwarfpp), itself depending on
    - [libcxxfileno](https://github.com/stephenrkell/libcxxfileno)
    - [libsrk31cxx](https://github.com/stephenrkell/libsrk31cxx)

These libraries are expected to be installed somewhere your compiler can find
them. If you are using Archlinux, you can check
[these `PKGBUILD`s](https://git.tobast.fr/m2-internship/pkgbuilds).

## Scripts and directories

* `./generate_eh_elf.py`: generate `.eh_elf.so` files for a binary (and its
  dependencies if required)
* `./compare_sizes.py`: compare the sizes of the `.eh_frame` of a binary (and
  its dependencies) with the sizes of the `.text` of the generated ELFs.
* `./extract_pc.py`: extracts a list of valid program counters of an ELF and
  produce a file as read by `dwarf-assembly`, **deprecated**.

* `benching`: all about benchmarking
* `env`: environment variables manager to ease the use of various `eh_elf`s in
  parallel, for experiments.
* `shared`: code shared between various subprojects
* `src`: the compiler code itself
* `stack_walker`: a primitive stack walker using `eh_elf`s
* `stack_walker_libunwind`: a primitive stack walker using vanilla `libunwind`
* `stats`: a statistics gathering module
* `tests`: some tests regarding `eh_elf`s, **deprecated**.

## How to use

To compile `eh_elf`s for a given ELF file, say `foo.bin`, it is recommended to
use `generate_eh_elf.py`. Help can be obtained with `--help`. A standard
command is

```bash
./generate_eh_elf.py --deps --enable-deref-arg --global-switch -o eh_elfs foo.bin
```

This will compile `foo.bin` and all the shared objects it relies on into
`eh_elf`s, in the directory `./eh_elfs`, using a dereferencing argument (which
is necessary for `perf-eh_elfs`).

## Generate the intermediary C file

If you're curious about the intermediary C file generated for a given ELF file
`foo.bin`, you must call `dwarf-assembly` directly. A parameter `--help` can be
passed; a standard command is

```bash
./dwarf-assembly --global-switch --enable-deref-arg foo.bin
```

**Beware**! This will generate the C code on the standard output.
