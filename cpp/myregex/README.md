# myregex

A small, **correct** regular-expression engine in modern C++ — implementing the
subset from [`requirement/requirement.md`](requirement/requirement.md):

| Feature | Example | Meaning |
|---|---|---|
| literal text | `abc` | matches exactly `abc` |
| `.` | `a.c` | any one character |
| `*` | `ab*c` | zero or more of the preceding atom |
| `?` | `colou?r` | zero or one of the preceding atom |
| `{n}` | `a{3}` | exactly `n` copies of the preceding atom |
| `\|` | `cat\|dog` | alternation — either side |

Plus two natural companions, marked as **extensions** (you need them for the listed
features to be usable — alternation/quantifiers want grouping, and literals want a way
to escape metacharacters):

| Extension | Example | Meaning |
|---|---|---|
| `( … )` grouping | `(ab){2}`, `(a\|b)*` | apply a quantifier / alternation to a sub-expression |
| `\` escape | `a\.b`, `\*` | match a metacharacter literally |

> Teaching-quality, not a drop-in `std::regex` replacement. The point is a clean,
> readable engine with **linear-time** matching and honest error reporting.

## Semantics

`matches()` is a **full match**: the entire input must be consumed by the pattern
(the usual "does this whole string match this pattern?"). It is not a substring
search. `.` matches **any** character, including newline.

## Use it

Header-only — `#include "myregex.hpp"`:

```cpp
#include "myregex.hpp"

myregex::Regex re("(cat|dog)s?");
re.matches("dogs");          // true
re.matches("fish");          // false

myregex::matches("a{3}", "aaa");   // true   (one-shot convenience)
```

A malformed pattern throws `myregex::ParseError` (with the offending position):

```cpp
try {
    myregex::Regex bad("a{");
} catch (const myregex::ParseError& e) {
    // "myregex: parse error at position 1: expected a number inside '{n}'"
}
```

## Build & run

```sh
make test     # build + run the test suite (106 checks)
make demo     # build + run a showcase
make          # build both into ./bin (git-ignored)
make clean

# try your own:
bin/demo 'a.*z' az abcz abc
bin/demo '(a|b)*' '' abba abbac
```

Builds clean (`-Wall -Wextra`) and the tests pass under **C++17, C++20, C++23, and
C++26**. Verified with Apple clang 21; override the toolchain with
`make CXX=g++ STD=c++23`.

## How it works

Three small, separable stages (see the comments in
[`myregex.hpp`](myregex.hpp)):

1. **Parser** — recursive descent turns the pattern into an AST. Grammar, lowest
   precedence first:
   ```
   alternation := concat ('|' concat)*
   concat      := repeat*
   repeat      := atom ('*' | '?' | '{' number '}')?
   atom        := '.' | '(' alternation ')' | '\' char | literal
   ```
   So `*`/`?`/`{n}` bind tighter than concatenation, which binds tighter than `|`
   (e.g. `ab|cd` is `(ab)|(cd)`, and `a|b{2}` is `a|(b{2})`).

2. **Compiler** — [Thompson construction](https://en.wikipedia.org/wiki/Thompson%27s_construction)
   turns the AST into an NFA. Each sub-expression becomes a *fragment* with dangling
   out-pointers that the parent patches. `{n}` emits `n` fresh copies of the
   sub-NFA; `{0}` is the empty string.

3. **Simulation** — the NFA is run over the input as a **set of active states**
   (Thompson/Pike simulation). An input of length *n* is matched in
   `O(n × states)` time with **no backtracking**, so adversarial patterns like
   `(a*)*b` don't blow up (they are catastrophic in backtracking engines).

## Design choices & limitations

- **Linear time, by construction.** The set-of-states simulation is the reason
  there's no catastrophic backtracking; the trade-off is no capture groups or
  backreferences (those need a different engine).
- **Full match only.** `search`/`find` aren't provided; you can emulate "contains"
  with `.*pattern.*` if you add nothing else, but anchored full-match keeps the
  semantics unambiguous for this exercise.
- **No `+`, `[...]`, `{n,m}`, anchors.** Not in the requirement. They're each a
  small, local addition (`+` is `xx*`; `{n,m}` is `n` copies then `m-n` optionals;
  `[...]` is a character-class state) — deliberately left out to keep the engine
  focused on the specified subset.
- **`{n}` is capped** at 100,000 copies to avoid pathological memory / integer
  overflow; a larger count is a `ParseError`.

## Files

| File | Purpose |
|---|---|
| [`myregex.hpp`](myregex.hpp) | the engine (header-only) |
| [`tests.cpp`](tests.cpp) | 106-check test suite (literals, each operator, grouping, escaping, combinations, parse errors) |
| [`demo.cpp`](demo.cpp) | CLI: showcase, or `bin/demo '<pattern>' <text>…` |
| [`Makefile`](Makefile) | `make test` / `make demo` |
