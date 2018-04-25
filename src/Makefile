CXX=g++
CXXLOCS?=-L. -I.
CXXFLAGS=$(CXXLOCS) -Wall -Wextra -std=c++14 -O2 -g
CXXLIBS=-lelf -ldwarf -ldwarfpp -lsrk31c++ -lc++fileno

TARGET=dwarf-assembly
OBJS=DwarfReader.o SimpleDwarf.o CodeGenerator.o main.o

###############################################################################

all: $(TARGET)

$(TARGET): gen_context_struct.hpp $(OBJS)
	$(CXX) -o $@ $(CXXFLAGS) $^ $(CXXLIBS)

gen_context_struct.hpp: ../shared/context_struct.h
	echo "static const char* CONTEXT_STRUCT_STR =" > $@
	sed 's/"/\\"/g' $< | sed 's/^\(.*\)$$/"\1\\n"/g' >> $@
	echo ";" >> $@

%.o: %.cpp
	$(CXX) -o $@ $(CXXFLAGS) -c $<


.PHONY: clean
clean:
	rm -f $(TARGET) *.o gen_*.hpp
