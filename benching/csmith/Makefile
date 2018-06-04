CSMITH=/home/tobast/root/bin/csmith
CC=gcc
CCFLAGS=-O3 -w  # Remove warnings: these are not meaningful
CCLIBS=-L../benchlib -I../benchlib -I/usr/include/csmith-2.3.0/
CC_UNWIND=-lbench.unwind
CC_EH_ELF=-lbench.eh_elf -L../../stack_walker -lstack_walker.global
REMOTE=seneve
SH=bash

.SECONDARY:
.PHONY: tests/%.allbin
tests/%.allbin: tests/%.eh_elf.bin tests/%.unwind.bin ;

tests/%.raw.c:
	while \
		( ssh seneve $(CSMITH) --max-funcs 100 > $@ ) ;\
		! ./validate_csmith.py "$@" ; \
		do :; done

tests/%.c: tests/%.raw.c
	cat $< \
		| sed 's/#include "csmith.h"/#include <bench.h>\n#include <csmith.h>/g' \
		| sed 's/return /bench_unwinding(); return /g' \
		| head -n $$(expr 1 + $$(grep -n "func_1();$$" $< | cut -f1 -d':')) \
		> $@
	echo -e "\tbench_dump_data();\n\treturn 0;\n}\n" \
		>> $@
	rm -f $<

tests/%.unwind.bin: tests/%.c
	LD_RUN_PATH=$$(readlink -f "../benchlib") \
		$(CC) $(CCFLAGS) $(CCLIBS) \
		$(CC_UNWIND) \
		$^ -o $@

tests/%.eh_elf.bin: tests/%.c
	LD_RUN_PATH=$$(readlink -f "../benchlib"):$$(readlink -f "../../stack_walker"):eh_elfs \
		$(CC) $(CCFLAGS) $(CCLIBS) \
		$(CC_UNWIND) \
		$^ -o $@
	mkdir -p tests/eh_elfs
	../../generate_eh_elf.py --remote seneve --deps -o tests/eh_elfs \
		-O3 --global-switch $@


clean:
	rm -f tests/*c tests/*bin tests/eh_elfs/*.eh_elf.bin.eh_elf.so
