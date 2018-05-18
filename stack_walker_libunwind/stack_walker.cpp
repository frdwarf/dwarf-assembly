#include "../stack_walker/stack_walker.hpp"

#include <libunwind.h>
#include <vector>
#include <cassert>

struct UnwPtrs {
    unw_context_t* ctx;
    unw_cursor_t* cursor;
};

static std::vector<UnwPtrs> to_delete;


bool stack_walker_init() {
    return true;
}

void stack_walker_close() {
    for(auto& del: to_delete) {
        delete del.ctx;
        delete del.cursor;
    }
}

static unw_cursor_t* get_cursor(const unwind_context_t& context) {
    // This is subtly dirty.
    // unwind_context_t::rip is uint64_t, thus suitable for a pointer.
    return (unw_cursor_t*) context.rip;
}

static void set_cursor(unwind_context_t& context, unw_cursor_t* unw_cursor) {
    // This is subtly dirty.
    // unwind_context_t::rip is uint64_t, thus suitable for a pointer.
    context.rip = (uintptr_t) unw_cursor;
}

unwind_context_t get_context() {
    int rc;
    unw_context_t* unw_context = new unw_context_t;
    rc = unw_getcontext(unw_context);
    if(rc < 0)
        assert(0);

    unw_cursor_t* cursor = new unw_cursor_t;
    rc = unw_init_local(cursor, unw_context);
    if(rc < 0)
        assert(0);

    rc = unw_step(cursor);
    if(rc < 0)
        assert(0);

    unwind_context_t out;

    set_cursor(out, cursor);

    to_delete.push_back(UnwPtrs({unw_context, cursor}));

    return out;
}

bool unwind_context(unwind_context_t& ctx) {
    int rc = unw_step(get_cursor(ctx));
    return rc > 0;
}

void walk_stack(const std::function<void(const unwind_context_t&)>& mapped) {
    unwind_context_t context = get_context();
    do {
        mapped(context);
    } while(unwind_context(context));
}

uintptr_t get_register(const unwind_context_t& ctx, StackWalkerRegisters reg) {
    unw_cursor_t* cursor = get_cursor(ctx);
    unw_regnum_t regnum = 0;

    switch(reg) {
        case SW_REG_RIP:
            regnum = UNW_X86_64_RIP;
            break;
        case SW_REG_RSP:
            regnum = UNW_X86_64_RSP;
            break;
        case SW_REG_RBP:
            regnum = UNW_X86_64_RBP;
            break;
    }

    uintptr_t out;
    int rc = unw_get_reg(cursor, regnum, &out);
    if(rc < 0)
        assert(false);
    return out;
}
