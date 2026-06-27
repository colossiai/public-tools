// ============================================================================
// C++23 feature tour
// Compile:  clang++ -std=c++23 cpp23.cpp -o cpp23 && ./cpp23
// ----------------------------------------------------------------------------
// C++23 is an "incremental but valuable" release focused on usability:
//   Language: deducing this (explicit object parameter), if consteval,
//             multidimensional subscript operator[], static operator(),
//             [[assume]], size_t literals (uz/z)
//   Library:  std::print / std::println, std::expected, std::mdspan,
//             std::ranges::to, std::views::zip, std::byteswap, std::unreachable
//
// NOTE: <generator> (std::generator coroutine) is part of C++23 but the header
//       is not yet shipped by every libc++; it's described in the README.
// ============================================================================

#include <print>
#include <expected>
#include <mdspan>
#include <ranges>
#include <vector>
#include <string>
#include <string_view>
#include <cstddef>
#include <bit>
#include <cstdint>

// --- 1. Deducing this: write one member, get const/ref/value overloads ------
// The explicit object parameter `self` replaces the implicit `this`.
struct Counter {
    int value = 0;
    // `auto&& self` deduces the value category & constness of the object.
    auto&& get(this auto&& self) { return self.value; }
};

// CRTP without the boilerplate base: deducing this knows the derived type.
struct Widget {
    std::string label;
    auto describe(this const auto& self) {
        return std::string("Widget{") + self.label + "}";
    }
};

// --- 2. static operator(): stateless function objects with no `this` cost ----
struct Plus {
    static int operator()(int a, int b) { return a + b; }
};

// --- 3. if consteval: branch on "are we in a constant evaluation?" ----------
constexpr int clamp_nonneg(int x) {
    if consteval {
        return x < 0 ? 0 : x;          // path taken during constexpr evaluation
    } else {
        return x < 0 ? 0 : x;          // (could use a faster runtime intrinsic)
    }
}

// --- 4. std::expected-returning function: errors without exceptions ---------
enum class ParseError { Empty, NotANumber };

std::expected<int, ParseError> parse_int(std::string_view s) {
    if (s.empty()) return std::unexpected(ParseError::Empty);
    int result = 0;
    for (char c : s) {
        if (c < '0' || c > '9') return std::unexpected(ParseError::NotANumber);
        result = result * 10 + (c - '0');
    }
    return result;
}

int main() {
    // 1. std::print / std::println: fast, std::format-style I/O, newline built in.
    std::println("std::println works without iostream — {} + {} = {}", 2, 3, 5);

    // 2. Deducing this.
    Counter c{41};
    c.get() += 1;                      // get() returns int& on an lvalue
    std::println("deducing this: counter={}", c.value);
    std::println("deducing this CRTP-free: {}", Widget{"ok"}.describe());

    // 3. static operator().
    std::println("static operator(): {}", Plus{}(20, 22));

    // 4. if consteval (verified at compile time).
    static_assert(clamp_nonneg(-5) == 0);
    std::println("if consteval clamp_nonneg(-5)={}", clamp_nonneg(-5));

    // 5. std::expected: the monadic-style happy path + error path.
    for (std::string_view in : {"123", "", "12x"}) {
        auto r = parse_int(in);
        if (r) std::println("parse(\"{}\") = {}", in, *r);
        else   std::println("parse(\"{}\") FAILED ({})", in,
                            r.error() == ParseError::Empty ? "empty" : "not-a-number");
    }
    // and_then / transform / value_or compose without nested ifs:
    int doubled = parse_int("21").transform([](int v) { return v * 2; }).value_or(-1);
    std::println("expected monadic transform: {}", doubled);

    // 6. std::mdspan + multidimensional subscript m[i, j].
    std::vector<int> storage(2 * 3);
    std::mdspan grid(storage.data(), 2, 3);            // 2x3 view over flat memory
    for (std::size_t i = 0; i < grid.extent(0); ++i)
        for (std::size_t j = 0; j < grid.extent(1); ++j)
            grid[i, j] = static_cast<int>(i * 10 + j); // multidim operator[]
    std::println("mdspan grid[1,2]={}, extents={}x{}", grid[1, 2],
                 grid.extent(0), grid.extent(1));

    // 7. std::ranges::to: materialize a lazy view into a container.
    auto squares = std::views::iota(1, 6)
                 | std::views::transform([](int n) { return n * n; })
                 | std::ranges::to<std::vector>();
    std::print("ranges::to vector:");
    for (int x : squares) std::print(" {}", x);
    std::println("");

    // 8. std::views::zip: iterate multiple ranges in lockstep.
    std::vector<std::string> names{"a", "b", "c"};
    std::vector<int>         vals{1, 2, 3};
    for (auto&& [n, v] : std::views::zip(names, vals))
        std::println("zip: {} -> {}", n, v);

    // 9. size_t / signed-size literals + [[assume]] for optimization hints.
    auto idx = 3uz;                                    // std::size_t literal
    auto sz  = 5z;                                     // signed size literal
    [[assume(idx < 10)]];                              // promise to the optimizer
    std::println("uz literal={}, z literal={}, byteswap(0x1234)={:#06x}",
                 idx, sz, std::byteswap(std::uint16_t{0x1234}));

    return 0;
}
