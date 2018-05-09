CXX=g++
CXXFLAGS=-Wall -Wextra -O0 -g -I../stack_walker -rdynamic

all: stack_walked.per_func.bin stack_walked.global.bin

stack_walked.%.bin: stack_walked.cpp
	LD_RUN_PATH=eh_elfs.$* $(CXX) $(CXXFLAGS) -o $@ $^ \
				-L../stack_walker -ldl -lstack_walker.$*

eh_elfs.per_func: stack_walked.per_func.bin
	../generate_eh_elf.py --remote seneve --deps -o $@ --switch-per-func $<
.PHONY: eh_elfs.per_func

eh_elfs.global: stack_walked.global.bin
	../generate_eh_elf.py --remote seneve --deps -o $@ --global-switch $<
.PHONY: eh_elfs.global

clean:
	rm -f *.bin
