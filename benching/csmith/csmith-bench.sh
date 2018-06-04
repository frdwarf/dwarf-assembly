#!/bin/bash

csmith "$@" | \
    sed 's/#include "csmith.h"/#include <bench.h>\n#include <csmith.h>/g' |\
    sed 's/return /bench_unwinding(); return /g'
