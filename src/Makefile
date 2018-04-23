CXX=g++
CXXLOCS?=-L. -I.
CXXFLAGS=$(CXXLOCS) -Wall -Wextra -std=c++14 -O2 -g
CXXLIBS=-lelf -ldwarf -ldwarfpp -lsrk31c++ -lc++fileno

TARGET=dwarf-assembly
OBJS=DwarfReader.o SimpleDwarf.o

###############################################################################

all: $(TARGET)

$(TARGET): $(OBJS)
	$(CXX) -o $@ $(CXXFLAGS) $^ $(CXXLIBS)

%.o: %.cpp
	$(CXX) -o $@ $(CXXFLAGS) -c $<


.PHONY: clean
clean:
	rm -f $(TARGET) *.o
