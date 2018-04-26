CXX=g++
CXXLIBS=-ldl
CXXFLAGS=-O0 -g -fPIC -Wall -Wextra

TARGET=libstack_walker.so
OBJS=stack_walker.o

all: $(TARGET)

$(TARGET): $(OBJS)
	$(CXX) $(CXXFLAGS) -shared $< $(CXXLIBS) -o $@

%.o: %.cpp
	$(CXX) $(CXXFLAGS) -c $< -o $@


clean:
	rm -f $(OBJS) $(TARGET)
