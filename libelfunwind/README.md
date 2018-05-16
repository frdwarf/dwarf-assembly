# libelfunwind

Reproduces the interface of libunwind, and exports a `libunwind.so` binary, so
that changing `LD_LIBRARY_PATH` makes it possible to use `dwarf-assembly`
instead of `dwarf` as an unwinding process in eg. `perf`.

## `perf` currently used libunwind features

```
  # Types
  unw_accessors_t
  unw_word_t
  unw_regnum_t
  unw_proc_info_t
  unw_fpreg_t
  unw_dyn_info_t
  unw_addr_space_t
  unw_cursor_t

  # Functions
  unw_create_addr_space
  unw_destroy_addr_space
  unw_flush_cache
  unw_get_reg
  unw_init_remote
  unw_is_signal_frame
  unw_set_caching_policy
  unw_step
```
