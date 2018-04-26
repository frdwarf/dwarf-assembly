#include <cstdio>
#include <dlfcn.h>

#include "../stack_walker/stack_walker.hpp"

int main() {
    Dl_info main_info;
    int rc = dladdr((void*)&main, &main_info);

    printf("I'm in %s!\n", (rc != 0) ? main_info.dli_sname : "[No data]");

    stack_walker_init();

    return 0;
}
