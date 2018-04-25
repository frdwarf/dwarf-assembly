#include <stdint.h>

typedef struct {
    uintptr_t rip, rsp, rbp;
} unwind_context_t;
