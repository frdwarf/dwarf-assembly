/**
 * This is a custom version of libunwind making use of dwarf-assembly and its
 * eh_elfs as an unwinding procedure.
 **/

#include <stdint.h>

struct unw_context_t {};
struct unw_cursor_t {};

typedef int unw_regnum_t;
typedef uint64_t unw_word_t;


int unw_getcontext(unw_context_t *);
int unw_init_local(unw_cursor_t *, unw_context_t *);
// int unw_init_remote(unw_cursor_t *, unw_addr_space_t, void *);
int unw_step(unw_cursor_t *);
int unw_get_reg(unw_cursor_t *, unw_regnum_t, unw_word_t *);
int unw_get_fpreg(unw_cursor_t *, unw_regnum_t, unw_fpreg_t *);
int unw_set_reg(unw_cursor_t *, unw_regnum_t, unw_word_t);
int unw_set_fpreg(unw_cursor_t *, unw_regnum_t, unw_fpreg_t);
int unw_resume(unw_cursor_t *);

unw_addr_space_t unw_local_addr_space;
unw_addr_space_t unw_create_addr_space(unw_accessors_t, int);
void unw_destroy_addr_space(unw_addr_space_t);
unw_accessors_t unw_get_accessors(unw_addr_space_t);
void unw_flush_cache(unw_addr_space_t, unw_word_t, unw_word_t);
int unw_set_caching_policy(unw_addr_space_t, unw_caching_policy_t);

const char *unw_regname(unw_regnum_t);
int unw_get_proc_info(unw_cursor_t *, unw_proc_info_t *);
int unw_get_save_loc(unw_cursor_t *, int, unw_save_loc_t *);
int unw_is_fpreg(unw_regnum_t);
int unw_is_signal_frame(unw_cursor_t *);
int unw_get_proc_name(unw_cursor_t *, char *, size_t, unw_word_t *);

void _U_dyn_register(unw_dyn_info_t *);
void _U_dyn_cancel(unw_dyn_info_t *);
