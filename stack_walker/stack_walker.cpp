#include "stack_walker.hpp"

#include <ucontext.h>
#include <unistd.h>
#include <link.h>
#include <cstring>
#include <cassert>
#include <cstdio>
#include <string>
#include <map>


typedef void* dl_handle_t;

/** Describes a line in the memory map (which SO is loaded where) */
struct MemoryMapEntry {
    MemoryMapEntry():
        beg(0), end(0), offset(0), obj_path(), eh_dl_handle(nullptr)
    {}

    uintptr_t beg, end;
    int offset;
    std::string obj_path;

    dl_handle_t eh_dl_handle;
};

/** `MemoryMapEntry`es mapped by their `beg` */
typedef std::map<
    uintptr_t,
    MemoryMapEntry,
    std::greater<uintptr_t> > MemoryMap;
// here, std::greater is used because it allows easy access to the
// corresponding segment by using lower_bound

static MemoryMap memory_map;


/** Equivalent to a shell command `readlink -f` */
std::string readlink_rec(const char* path) {
    char buf[2][1024];
    int parity = 1;
    strcpy(buf[1], path);

    do {
        int rc = readlink(buf[parity], buf[1-parity], 1024);
        parity = 1 - parity;
        if(rc < 0) {
            if(errno == EINVAL)
                break;
        }
    } while(true);

    return std::string(buf[1 - parity]);
}

/** Called by `dl_iterate_phdr` later, initializes `memory_map` */
int fill_memory_map_callback(
        struct dl_phdr_info* info,
        size_t /*size*/,
        void* /*data*/)
{
    for(int sec = 0; sec < info->dlpi_phnum; ++sec) {
        const ElfW(Phdr)& cur_hdr = info->dlpi_phdr[sec];
        if(cur_hdr.p_type != PT_LOAD || (cur_hdr.p_flags & PF_X) == 0)
            continue;
        if(std::string(info->dlpi_name).find("linux-vdso")
                != std::string::npos)
        {
            continue;
        }

        MemoryMapEntry entry;
        entry.beg = info->dlpi_addr + cur_hdr.p_vaddr;
        entry.obj_path = std::string(info->dlpi_name);
        entry.offset = cur_hdr.p_offset;

        entry.end = entry.beg + cur_hdr.p_memsz;

        if(entry.obj_path.empty()) { // The source binary itself
            entry.obj_path = readlink_rec("/proc/self/exe");
        }

        memory_map.insert(std::make_pair(entry.beg, entry));
    }
    return 0;
}

void stack_walker_close() {
    for(auto& mmap_entry_pair: memory_map) {
        auto& mmap_entry = mmap_entry_pair.second;

        if(mmap_entry.eh_dl_handle != nullptr)
            dlclose(mmap_entry.eh_dl_handle);
    }
}

bool stack_walker_init() {
    if(dl_iterate_phdr(&fill_memory_map_callback, nullptr) != 0) {
        stack_walker_close();
        return false;
    }

    for(const auto& mmap_entry: memory_map) {
        printf("%012lx-%012lx %08x    %s\n",
                mmap_entry.second.beg,
                mmap_entry.second.end,
                mmap_entry.second.offset,
                mmap_entry.second.obj_path.c_str());
    }

    // Call `dlopen` on the `eh_elf.so` maching every entry in `memory_map`
    for(auto& mmap_entry_pair: memory_map) {
        auto& mmap_entry = mmap_entry_pair.second;

        // Find SO's basename
        size_t last_slash = mmap_entry.obj_path.rfind("/");
        if(last_slash == std::string::npos)
            last_slash = 0;
        else
            last_slash++;
        std::string basename(mmap_entry.obj_path, last_slash);

        // Load the SO
        std::string eh_elf_name = basename + ".eh_elf.so";
        mmap_entry.eh_dl_handle = dlopen(eh_elf_name.c_str(), RTLD_LAZY);

        if(mmap_entry.eh_dl_handle == nullptr) {
            fprintf(stderr,
                    "Error: cannot load shared object %s.\ndlerror: %s\n",
                    eh_elf_name.c_str(),
                    dlerror());
            stack_walker_close();
            return false;
        }
    }

    return true;
}

unwind_context_t get_context() {
    unwind_context_t out;
    ucontext_t uctx;

    if(getcontext(&uctx) < 0) {
        assert(0);  // Cleaner code will come later — TODO
    }

    out.rip = uctx.uc_mcontext.gregs[REG_RIP];
    out.rsp = uctx.uc_mcontext.gregs[REG_RSP];
    out.rbp = uctx.uc_mcontext.gregs[REG_RBP];

    unwind_context(out);
    return out;
}

/** Get the `fde_func_t` function handling the given program counter — it may
 * be by calling a lookup function, or by directly looking into the ELF
 * symbols, depending on the state of the experiment. This is an abstraction
 * function. */
_fde_func_t fde_handler_for_pc(uintptr_t pc) {
    // Get the memory_map entry
    auto mmap_entry_it = memory_map.lower_bound(pc);
    if(mmap_entry_it == memory_map.end()) {
        return nullptr;
    }
    MemoryMapEntry& mmap_entry = mmap_entry_it->second;
    if(!(mmap_entry.beg <= pc && pc <= mmap_entry.end))
        return nullptr;

    // Get the lookup function
    _fde_func_t (*lookup)(uintptr_t) =
        (_fde_func_t (*)(uintptr_t)) (
                dlsym(mmap_entry.eh_dl_handle, "_fde_lookup"));

    // Get the translated pc
    uintptr_t tr_pc = pc - mmap_entry.beg;

    // Get the actual function
    _fde_func_t rfunc = lookup(tr_pc);

    return rfunc;
}

bool unwind_context(unwind_context_t& ctx) {
    _fde_func_t fde_func = fde_handler_for_pc(ctx.rip);
    if(fde_func == nullptr)
        return false;

    ctx = fde_func(ctx, ctx.rip);
    return true;
}

void walk_stack(const std::function<void(const unwind_context_t&)>& mapped) {
    unwind_context_t ctx = get_context();
    do {
        mapped(ctx);
    } while(unwind_context(ctx));
}
