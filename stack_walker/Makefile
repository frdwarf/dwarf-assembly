CXX=g++
CXXLIBS=-ldl
CXXFLAGS=-O2 -fPIC -Wall -Wextra

TARGET_BASE=libstack_walker
TARGETS=$(TARGET_BASE).global.so $(TARGET_BASE).per_func.so
OBJS=stack_walker.o

all: $(TARGETS)

$(TARGET_BASE).%.so: $(OBJS:.o=.%.o)
	$(CXX) $(CXXFLAGS) -shared $< $(CXXLIBS) -o $@

%.global.o: %.cpp
	$(CXX) $(CXXFLAGS) -DSGP_GLOBAL_SWITCH -c $< -o $@

%.per_func.o: %.cpp
	$(CXX) $(CXXFLAGS) -DSGP_SWITCH_PER_FUNC -c $< -o $@


clean:
	rm -f $(OBJS) $(TARGET_BASE)*.so
