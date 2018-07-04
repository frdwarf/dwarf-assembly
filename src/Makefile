CXX=g++
CXXLOCS?=-L. -I.
CXXFL?=
CXXFLAGS=$(CXXLOCS) -Wall -Wextra -std=c++14 -O2 -g $(CXXFL)
CXXLIBS=-lelf -ldwarf -ldwarfpp -lsrk31c++ -lc++fileno

TARGET=dwarf-assembly
OBJS=\
	DwarfReader.o \
	SimpleDwarf.o \
	CodeGenerator.o \
	PcListReader.o \
	SimpleDwarfFilter.o \
	PcHoleFiller.o \
	EmptyFdeDeleter.o \
	ConseqEquivFilter.o \
	SwitchStatement.o \
	NativeSwitchCompiler.o \
	FactoredSwitchCompiler.o \
	settings.o \
	main.o

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
