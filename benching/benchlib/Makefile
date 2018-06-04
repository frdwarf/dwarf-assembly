TARGETS=libbench.eh_elf.so libbench.unwind.so
COMMON_OBJS=bench.o
EH_ELF_OBJS=DwBenchmark.eh_elf.o
UNWIND_OBJS=DwBenchmark.unwind.o
CXX=g++
CXXFLAGS=-Wall -Wextra -O2 -std=c++14
CXXLIBS=


all: $(TARGETS)

libbench.eh_elf.so: $(EH_ELF_OBJS) $(COMMON_OBJS)
	$(CXX) $(CXXFLAGS) -shared -o $@ $^ $(CXXLIBS) \
		-L../../stack_walker -lstack_walker.global

libbench.unwind.so: $(UNWIND_OBJS) $(COMMON_OBJS)
	$(CXX) $(CXXFLAGS) -shared -o $@ $^ $(CXXLIBS) \
		-lunwind -lunwind-x86_64

%.eh_elf.o: %.cpp
	$(CXX) $(CXXFLAGS) -fPIC -DUNWIND_EH_ELF -o $@ -c $<

%.unwind.o: %.cpp
	$(CXX) $(CXXFLAGS) -fPIC -DUNWIND_LIBUNWIND -o $@ -c $<

%.o: %.cpp
	$(CXX) $(CXXFLAGS) -fPIC -o $@ -c $<


.PHONY: clean
clean:
	rm *.o $(TARGETS)
