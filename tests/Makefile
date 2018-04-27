CXX=g++
CXXFLAGS=-Wall -Wextra -O0 -g -I../stack_walker -rdynamic

stack_walked.bin: stack_walked.cpp
	$(CXX) $(CXXFLAGS) -o $@ $^ -L../stack_walker -ldl -lstack_walker

clean:
	rm *.bin
