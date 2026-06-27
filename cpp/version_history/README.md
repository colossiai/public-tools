# C++ Version History — feature demos

Self-contained, runnable demo programs for the major modern C++ standards.
Each `cppNN.cpp` compiles and runs on its own and prints what each feature does.

| File | Standard | Run |
|------|----------|-----|
| [`cpp14.cpp`](cpp14.cpp) | C++14 | `make run-cpp14` |
| [`cpp17.cpp`](cpp17.cpp) | C++17 | `make run-cpp17` |
| [`cpp20.cpp`](cpp20.cpp) | C++20 | `make run-cpp20` |
| [`cpp23.cpp`](cpp23.cpp) | C++23 | `make run-cpp23` |
| [`cpp26.cpp`](cpp26.cpp) | C++26 (draft) | `make run-cpp26` |

## Building

```sh
make run            # build + run all demos
make run-cpp20      # build + run one demo
make                # build all
make clean
```

The demos were verified with **Apple clang 21 / libc++** (`clang++ --version`).
If your system compiler is older, point `make` at a newer one:

```sh
make CXX=/opt/homebrew/opt/llvm/bin/clang++ run     # Homebrew LLVM
make CXX=g++-14 run                                 # GCC 14+
```

Editor note: a [`.clangd`](.clangd) file sets the correct `-std=` per file so
clangd doesn't flag newer-standard syntax as errors.

---

## What each standard added

### C++14 — polishing C++11
- **Generic lambdas** — `auto` lambda parameters.
- **Lambda init-capture** — `[p = std::move(ptr)]`, capture move-only types / expressions.
- **Return-type deduction** — `auto f() { ... }` with no trailing return type.
- **`decltype(auto)`** — deduce a type *preserving* references and cv-qualifiers.
- **Variable templates** — `template<class T> constexpr T pi = ...;`.
- **Relaxed `constexpr`** — loops, locals, and mutation inside `constexpr` functions.
- **Binary literals & digit separators** — `0b1010'1100`, `1'000'000`.
- **`std::make_unique`**, **`[[deprecated]]`**, **`std::integer_sequence`**.

### C++17 — big batch of conveniences
- **Structured bindings** — `auto [a, b] = pair;`.
- **`if`/`switch` with initializer** — `if (auto it = m.find(k); it != m.end())`.
- **`if constexpr`** — compile-time branch pruning in templates.
- **Fold expressions** — `(args + ...)` over parameter packs.
- **CTAD** — class template argument deduction (`std::pair p{1, 2.5}`).
- **`inline` variables**, **nested namespaces** `a::b::c`, **guaranteed copy elision**.
- **Attributes** — `[[nodiscard]]`, `[[maybe_unused]]`, `[[fallthrough]]`.
- **Library** — `std::optional`, `std::variant`, `std::any`, `std::string_view`,
  `std::apply` / `std::invoke`, `std::filesystem`, parallel STL algorithms.

### C++20 — the second-biggest release ever
The "big four": **Concepts**, **Ranges**, **Coroutines**, **Modules**.
- **Concepts / `requires`** — named, checkable template constraints.
- **Abbreviated function templates** — `auto` parameters in normal functions.
- **Three-way comparison `<=>`** ("spaceship") — `= default` gives all six operators.
- **Designated initializers** — `Point{.x = 1, .y = 2}`.
- **`consteval`** (immediate functions) and **`constinit`**.
- **`using enum`**, templated/`[=, this]` lambdas.
- **Library** — Ranges & views, `std::format`, `std::span`, `<bit>`,
  calendar/time-zone `<chrono>`, `std::jthread` + `stop_token`.
- *Not demoed here* (need extra build setup):
  - **Modules** — `export module foo;` / `import foo;` (replaces headers).
  - **Coroutines** — `co_await` / `co_yield` / `co_return` (the language plumbing;
    a usable `std::generator` arrived in C++23).

### C++23 — incremental, very usable
- **Deducing `this`** — explicit object parameter `void f(this Self&& self)`;
  collapses const/ref overloads and gives CRTP-free static polymorphism.
- **`std::print` / `std::println`** — fast, `std::format`-based output.
- **`std::expected<T, E>`** — error handling without exceptions, with monadic
  `and_then` / `transform` / `or_else`.
- **`std::mdspan`** + **multidimensional `operator[]`** — `grid[i, j]`.
- **`std::ranges::to`** — materialize a view into a container.
- **More views** — `std::views::zip` (and `adjacent`, `slide`, `chunk_by`…; note
  `enumerate`/`chunk` aren't in every libc++ yet).
- **`if consteval`**, **`static operator()`**, **`[[assume]]`**, size literals `5uz`/`5z`.
- *Not demoed here* — **`std::generator`** (coroutine generator): the header
  `<generator>` isn't shipped by every libc++ yet.

### C++26 — draft / partial support
The standard isn't final; compiler coverage is uneven. **Demoed** (compile today
on recent clang):
- **Pack indexing** — `pack...[N]` for both values and types.
- **`#embed`** — embed a file's bytes at compile time (also a C23 feature).
- **`= delete("reason")`** — deletion with a custom diagnostic message.
- **`_` placeholder** — a redeclarable "don't care" name for ignored bindings.

**Landmark features still landing** (described, not demoed — no end-to-end
shipping implementation yet):
- **Static reflection** (`^^` / `std::meta`) — introspect & generate code.
- **Contracts** — `pre`/`post`/`contract_assert`.
- **`std::execution`** (P2300 senders/receivers) — structured async.
- **Concurrency** — hazard pointers, RCU, `std::text_encoding`.

> Feature availability depends entirely on your compiler/standard-library
> version. Check [cppreference compiler support](https://en.cppreference.com/w/cpp/compiler_support)
> for the current state, and probe your toolchain with the
> [feature-test macros](https://en.cppreference.com/w/cpp/feature_test) in
> `<version>` (e.g. `__cpp_lib_expected`, `__cpp_pack_indexing`).
