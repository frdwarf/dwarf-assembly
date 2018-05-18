#include <cstdio>
#include <dlfcn.h>

#include "../stack_walker/stack_walker.hpp"

void fill_my_stack1(volatile int&);
void fill_my_stack2(volatile int&);

void stack_filled() {
    int frame_id = 0;
    walk_stack([&frame_id](const unwind_context_t& ctx) {
            Dl_info func_info;
            int dl_rc = dladdr((void*) ctx.rip, &func_info);
            printf("#%d - %s — %%rip = 0x%lx, %%rbp = 0x%lx, %%rsp = 0x%lx\n",
                    ++frame_id,
                    (dl_rc != 0) ? func_info.dli_sname : "[Unknown func]",
                    get_register(ctx, SW_REG_RIP),
                    get_register(ctx, SW_REG_RBP),
                    get_register(ctx, SW_REG_RSP));
        });
}

void fill_my_stack2(volatile int& depth) {
    if(depth == 0)
        stack_filled();
    else {
        --depth;
        fill_my_stack1(depth);
    }
}

void fill_my_stack1(volatile int& depth) {
    if(depth == 0)
        stack_filled();
    else {
        --depth;
        fill_my_stack2(depth);
    }
}

int main() {
    Dl_info main_info;
    int rc = dladdr((void*)&main, &main_info);

    printf("I'm in %s!\n", (rc != 0) ? main_info.dli_sname : "[No data]");

    stack_walker_init();

    printf("Stack walker init'd!\n");
    volatile int depth = 10;
    fill_my_stack1(depth);

    return 0;
}
