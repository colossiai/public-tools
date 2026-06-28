# Build & run the expert trading C++ demos.
#
#   make            # build all demos into ./bin (git-ignored)
#   make run        # build + run all demos
#   make 03_false_sharing   # build one demo by name
#   make clean
#
# Override the compiler if needed:
#   make CXX=/opt/homebrew/opt/llvm/bin/clang++

CXX   ?= clang++
STD   ?= c++20
OPT   ?= -O2
WARN  := -Wall -Wextra
LIBS  := -pthread
BIN   := bin

SRCS  := $(sort $(wildcard *.cpp))
BINS  := $(patsubst %.cpp,$(BIN)/%,$(SRCS))
NAMES := $(patsubst %.cpp,%,$(SRCS))

.PHONY: all run clean $(NAMES)

all: $(BINS)

# Allow `make 03_false_sharing` (bare name) as a shortcut for `bin/03_false_sharing`,
# otherwise the bare name falls through to make's built-in rule (no -std=c++20).
$(NAMES): %: $(BIN)/%

$(BIN)/%: %.cpp | $(BIN)
	$(CXX) -std=$(STD) $(OPT) $(WARN) $< -o $@ $(LIBS)

$(BIN):
	mkdir -p $(BIN)

run: all
	@for b in $(BINS); do \
	  echo "==================== $$b ===================="; \
	  $$b; echo; \
	done

clean:
	rm -rf $(BIN)
