# Build & run the C++ version-feature demos.
#
#   make            # build all demos
#   make run        # build + run all demos
#   make cpp20      # build a single demo (cpp14/cpp17/cpp20/cpp23/cpp26)
#   make run-cpp20  # build + run a single demo
#   make clean
#
# Binaries are written to ./bin (git-ignored).
# Override the compiler if your system clang/gcc is too old, e.g.:
#   make CXX=/opt/homebrew/opt/llvm/bin/clang++

CXX      ?= clang++
WARN     := -Wall -Wextra
BIN      := bin
DEMOS    := cpp14 cpp17 cpp20 cpp23 cpp26

cpp14: STD := c++14
cpp17: STD := c++17
cpp20: STD := c++20
cpp23: STD := c++23
cpp26: STD := c++26

.PHONY: all run clean $(addprefix run-,$(DEMOS))

all: $(DEMOS)

$(DEMOS): %: %.cpp | $(BIN)
	$(CXX) -std=$(STD) $(WARN) $< -o $(BIN)/$@

$(BIN):
	mkdir -p $(BIN)

run: all
	@for d in $(DEMOS); do \
	  echo "==================== $$d ===================="; \
	  $(BIN)/$$d; echo; \
	done

$(addprefix run-,$(DEMOS)): run-%: %
	@echo "==================== $* ===================="; $(BIN)/$*

clean:
	rm -rf $(BIN)
