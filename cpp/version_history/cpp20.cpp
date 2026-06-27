// ============================================================================
// C++20 feature tour
// Compile:  clang++ -std=c++20 cpp20.cpp -o cpp20 && ./cpp20
// ----------------------------------------------------------------------------
// C++20 is one of the biggest releases since C++11. The "big four" are:
//   Concepts, Ranges, Coroutines, Modules.
// This file demos everything that is convenient to show in a single TU
// (Modules and Coroutines need extra build setup, so they're described in the
//  README rather than demoed here).
//   Language: concepts/requires, abbreviated templates, three-way <=>,
//             designated initializers, consteval, constinit, using enum,
//             templated & [=,this] lambdas
//   Library:  ranges & views, std::format, std::span, <bit>
// ============================================================================

#include <iostream>
#include <vector>
#include <span>
#include <ranges>
#include <format>
#include <compare>
#include <bit>
#include <cstdint>
#include <string>

// --- 1. Concepts: named, checkable constraints on template params -----------
template <typename T>
concept Numeric = std::integral<T> || std::floating_point<T>;

template <Numeric T>                 // constrained template
T square(T x) { return x * x; }

// requires-clause with an ad-hoc requirement.
template <typename T>
    requires requires(T a, T b) { a + b; }   // "T must support a + b"
T add(T a, T b) { return a + b; }

// --- 2. Abbreviated function template: `auto` params = implicit template ----
auto max_of(const auto& a, const auto& b) { return a > b ? a : b; }

// --- 3. Three-way comparison (spaceship) ------------------------------------
struct Version {
    int major, minor, patch;
    auto operator<=>(const Version&) const = default; // gives <,<=,>,>=,==,!=
};

// --- 4. consteval: must run at compile time ---------------------------------
consteval int compile_time_pow(int base, int exp) {
    int r = 1;
    while (exp-- > 0) r *= base;
    return r;
}

// --- 5. constinit: guaranteed constant initialization (no static-init order)
constinit int g_value = compile_time_pow(2, 10); // 1024

// --- 6. using enum ----------------------------------------------------------
enum class Color { Red, Green, Blue };
const char* name(Color c) {
    using enum Color;                  // bring enumerators into scope
    switch (c) { case Red: return "Red"; case Green: return "Green"; case Blue: return "Blue"; }
    return "?";
}

int main() {
    // 1. Concepts in action.
    std::cout << "square(9)=" << square(9) << ", add(1.5,2.5)=" << add(1.5, 2.5) << "\n";

    // 2. Abbreviated template.
    std::cout << "max_of(3,7)=" << max_of(3, 7)
              << ", max_of(\"a\",\"b\")=" << max_of(std::string("a"), std::string("b")) << "\n";

    // 3. Spaceship: all six relational operators for free.
    Version v1{1, 2, 0}, v2{1, 3, 0};
    std::cout << std::format("v1<v2 = {}, v1==v1 = {}\n", v1 < v2, v1 == v1);

    // 4./5. consteval + constinit.
    static_assert(compile_time_pow(3, 4) == 81);
    std::cout << "constinit g_value (2^10)=" << g_value << "\n";

    // 6. using enum.
    std::cout << "color: " << name(Color::Green) << "\n";

    // 7. Ranges & views: lazy, composable pipelines.
    std::vector<int> nums{1, 2, 3, 4, 5, 6, 7, 8, 9, 10};
    auto pipeline = nums
                  | std::views::filter([](int n) { return n % 2 == 0; })
                  | std::views::transform([](int n) { return n * n; })
                  | std::views::take(3);
    std::cout << "ranges even^2 take3:";
    for (int x : pipeline) std::cout << ' ' << x;     // 4 16 36
    std::cout << "\n";

    // 8. std::format: type-safe, Python-like formatting.
    std::cout << std::format("format: {0} + {0} = {1}, hex={2:#06x}, pad={3:>6}\n",
                             21, 42, 255, "hi");

    // 9. std::span: non-owning view over contiguous memory.
    int raw[] = {10, 20, 30, 40};
    std::span<int> sp{raw};
    auto sum = [](std::span<const int> s) { int t = 0; for (int v : s) t += v; return t; };
    std::cout << "span sum=" << sum(sp) << ", subspan(1,2) sum=" << sum(sp.subspan(1, 2)) << "\n";

    // 10. <bit>: portable bit utilities.
    std::uint32_t bits = 0b0010'1100;
    std::cout << std::format("popcount={}, has_single_bit(16)={}, bit_width(255)={}\n",
                             std::popcount(bits), std::has_single_bit(16u), std::bit_width(255u));

    // 11. Designated initializers (C-style, now standard in C++).
    Version v3{.major = 2, .minor = 0, .patch = 1};
    std::cout << std::format("designated init: {}.{}.{}\n", v3.major, v3.minor, v3.patch);

    return 0;
}
