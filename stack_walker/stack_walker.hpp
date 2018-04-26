/** Provides stack walking facilities exploiting the eh_elf objects, that can
 * be loaded at runtime. */


#pragma once

#include <cstdint>
#include <functional>

#include "../shared/context_struct.h"


/** Initialize the stack walker. This must be called only once.
 *
 * \return true iff everything was correctly initialized.
 */
bool stack_walker_init();

/** Deallocate everything that was allocated by the stack walker */
void stack_walker_close();

/** Get the unwind context of the point from which this function was called.
 *
 * This context must then be exploited straight away: it is unsafe to alter the
 * call stack before using it, in particular by returning from the calling
 * function. */
unwind_context_t get_context();

/** Unwind the passed context once, in place.
 *
 * Returns `true` if the context was actually unwinded, or `false` if the end
 * of the call stack was reached. */
bool unwind_context(unwind_context_t& ctx);

/** Call the passed function once per frame in the call stack, most recent
 * frame first, with the current context as its sole argument. */
void walk_stack(const std::function<void(const unwind_context_t&)>& mapped);
