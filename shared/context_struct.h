#include <stdint.h>

typedef struct {
    uintptr_t rip, rsp, rbp;
} unwind_context_t;

typedef uintptr_t (*deref_func_t)(uintptr_t);

typedef unwind_context_t (*_fde_func_t)(unwind_context_t, uintptr_t);
typedef unwind_context_t (*_fde_func_with_deref_t)(
        unwind_context_t,
        uintptr_t,
        deref_func_t);
