CXX=g++
CXXLIBS=-lunwind -lunwind-x86_64
CXXFLAGS=-O2 -fPIC -Wall -Wextra -rdynamic

TARGET=libstack_walker.so
OBJS=stack_walker.o

all: $(TARGET)

$(TARGET): $(OBJS)
	$(CXX) $(CXXFLAGS) -shared $< $(CXXLIBS) -o $@

%.o: %.cpp
	$(CXX) $(CXXFLAGS) -c $< -o $@

.PHONY: clean
clean:
	rm -f $(OBJS) $(TARGET_BASE)*.so
