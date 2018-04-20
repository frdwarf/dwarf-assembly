# Dwarf Assembly

Some experiments around compiling the most used Dwarf informations (ELF debug
data) directly into assembly.

This project is a big work in progress, don't expect anything to be stable for
now.

## Dependencies

As of now, this project relies on the following libraries:

* libelf
* libdwarf
* [libdwarfpp](https://github.com/stephenrkell/libdwarfpp), itself depending on
    - [libcxxfileno](https://github.com/stephenrkell/libcxxfileno)
    - [libsrk31cxx](https://github.com/stephenrkell/libsrk31cxx)

These libraries are expected to be installed somewhere your compiler can find
them.
