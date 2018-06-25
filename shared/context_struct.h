#include <stdint.h>

typedef enum {
    UNWF_RIP=0,
    UNWF_RSP=1,
    UNWF_RBP=2,
    UNWF_RBX=3,

    UNWF_ERROR=7
} unwind_flags_t;

typedef struct {
    uint8_t flags;
    uintptr_t rip, rsp, rbp, rbx;
} unwind_context_t;

typedef uintptr_t (*deref_func_t)(uintptr_t);

typedef unwind_context_t (*_fde_func_t)(unwind_context_t, uintptr_t);
typedef unwind_context_t (*_fde_func_with_deref_t)(
        unwind_context_t,
        uintptr_t,
        deref_func_t);
