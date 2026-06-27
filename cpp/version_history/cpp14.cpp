// ============================================================================
// C++14 feature tour
// Compile:  clang++ -std=c++14 cpp14.cpp -o cpp14 && ./cpp14
// ----------------------------------------------------------------------------
// C++14 was a "small" release that polished C++11. Highlights:
//   - generic (polymorphic) lambdas
//   - lambda init-capture (capture by move / capture an expression)
//   - function return-type deduction (auto)
//   - decltype(auto)
//   - variable templates
//   - relaxed constexpr (loops, multiple statements, local mutation)
//   - binary literals & digit separators
//   - std::make_unique
//   - [[deprecated]] attribute
//   - std::integer_sequence
// ============================================================================

#include <iostream>
#include <memory>
#include <utility>
#include <tuple>
#include <string>

// --- 1. Variable templates --------------------------------------------------
template <typename T>
constexpr T pi = T(3.1415926535897932385L);

// --- 2. Function return-type deduction (auto) -------------------------------
// No trailing return type needed; the compiler deduces it from `return`.
auto add(int a, int b) { return a + b; }

// --- 3. decltype(auto): perfect forwarding of the *exact* type --------------
// `auto` strips references/cv; `decltype(auto)` preserves them.
int  global = 42;
int& ref_to_global() { return global; }
decltype(auto) keeps_reference() { return ref_to_global(); } // returns int&

// --- 4. Relaxed constexpr: loops & mutation allowed inside constexpr --------
constexpr int factorial(int n) {
    int result = 1;
    for (int i = 2; i <= n; ++i) result *= i; // loops now legal in constexpr
    return result;
}

// --- 5. [[deprecated]] attribute -------------------------------------------
[[deprecated("use add() instead")]]
int old_add(int a, int b) { return a + b; }

// --- 6. std::integer_sequence: compile-time index packs ---------------------
template <typename Tuple, std::size_t... Is>
void print_tuple_impl(const Tuple& t, std::index_sequence<Is...>) {
    // Fold-ish trick using initializer list (no fold expressions until C++17).
    (void)std::initializer_list<int>{
        ((std::cout << (Is == 0 ? "" : ", ") << std::get<Is>(t)), 0)...};
}
template <typename... Ts>
void print_tuple(const std::tuple<Ts...>& t) {
    print_tuple_impl(t, std::index_sequence_for<Ts...>{});
}

int main() {
    // 1. Generic lambda: `auto` parameters => works for any type.
    auto twice = [](auto x) { return x + x; };
    std::cout << "generic lambda: " << twice(21) << ", " << twice(std::string("ab")) << "\n";

    // 2. Lambda init-capture: move a unique_ptr into the lambda.
    auto owned = std::make_unique<int>(99);             // make_unique is C++14
    auto consumer = [p = std::move(owned)] { return *p; };
    std::cout << "init-capture (moved): " << consumer() << "\n";

    // 3. Variable template.
    std::cout << "pi<float>=" << pi<float> << ", pi<double>=" << pi<double> << "\n";

    // 4. Return-type deduction + decltype(auto).
    keeps_reference() = 7;                               // mutate through int&
    std::cout << "decltype(auto) reference write -> global=" << global
              << ", add()=" << add(2, 3) << "\n";

    // 5. Relaxed constexpr evaluated at compile time.
    constexpr int f5 = factorial(5);
    static_assert(f5 == 120, "5! must be 120");
    std::cout << "constexpr factorial(5)=" << f5 << "\n";

    // 6. Binary literals + digit separators.
    int flags = 0b1010'1100;                            // 0xAC
    long big  = 1'000'000'000;
    std::cout << "binary 0b1010'1100=" << flags << ", grouped=" << big << "\n";

    // 7. integer_sequence-powered tuple print.
    std::cout << "tuple = (";
    print_tuple(std::make_tuple(1, "two", 3.0));
    std::cout << ")\n";

    return 0;
}
