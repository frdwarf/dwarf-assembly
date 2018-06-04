/** Benchmarking library: a collection of functions that can be called to
 * benchmark dwarf-assembly
 **/

#pragma once

#ifdef __cplusplus
extern "C" {
#endif

void bench_unwinding();
void bench_dump_data();

#ifdef __cplusplus
} // END extern "C"
#endif
