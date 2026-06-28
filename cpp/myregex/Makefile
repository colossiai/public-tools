# Build & run the myregex demo and tests.
#
#   make            # build demo + tests into ./bin (git-ignored)
#   make test       # build + run the test suite
#   make demo       # build + run the showcase
#   make clean
#
# Override the compiler/standard if needed:
#   make CXX=g++ STD=c++23

CXX  ?= clang++
STD  ?= c++20
OPT  ?= -O2
WARN := -Wall -Wextra
BIN  := bin

.PHONY: all test demo clean

all: $(BIN)/tests $(BIN)/demo

$(BIN)/tests: tests.cpp myregex.hpp | $(BIN)
	$(CXX) -std=$(STD) $(OPT) $(WARN) tests.cpp -o $@

$(BIN)/demo: demo.cpp myregex.hpp | $(BIN)
	$(CXX) -std=$(STD) $(OPT) $(WARN) demo.cpp -o $@

$(BIN):
	mkdir -p $(BIN)

test: $(BIN)/tests
	@$(BIN)/tests

demo: $(BIN)/demo
	@$(BIN)/demo

clean:
	rm -rf $(BIN)
