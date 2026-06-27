// ============================================================================
// C++17 feature tour
// Compile:  clang++ -std=c++17 cpp17.cpp -o cpp17 && ./cpp17
// ----------------------------------------------------------------------------
// C++17 added a large batch of language + library conveniences:
//   Language: structured bindings, if/switch init statements, constexpr if,
//             fold expressions, class template argument deduction (CTAD),
//             inline variables, nested namespaces, guaranteed copy elision,
//             [[nodiscard]] / [[maybe_unused]] / [[fallthrough]]
//   Library:  std::optional, std::variant, std::any, std::string_view,
//             std::apply / std::invoke, std::filesystem
// ============================================================================

#include <iostream>
#include <optional>
#include <variant>
#include <any>
#include <string>
#include <string_view>
#include <map>
#include <tuple>
#include <functional>
#include <type_traits>

// --- inline variable: one definition across TUs, defined in a header is OK --
inline int g_counter = 0;

// --- nested namespace shorthand ---------------------------------------------
namespace app::config::detail {
    constexpr int kVersion = 17;
}

// --- constexpr if: compile-time branch pruning ------------------------------
template <typename T>
std::string describe(const T& v) {
    if constexpr (std::is_integral_v<T>) {
        return "integer:" + std::to_string(v);
    } else if constexpr (std::is_floating_point_v<T>) {
        return "float:" + std::to_string(v);
    } else {
        return std::string("other:") + v; // only compiled for the matching branch
    }
}

// --- fold expressions: variadic sum without recursion -----------------------
template <typename... Args>
auto sum(Args... args) { return (args + ... + 0); }

template <typename... Args>
void print_all(Args&&... args) {
    ((std::cout << args << ' '), ...);   // unary fold over the comma operator
    std::cout << '\n';
}

// --- CTAD: a class template whose args are deduced from the constructor -----
template <typename A, typename B>
struct Pair {
    A first; B second;
    Pair(A a, B b) : first(a), second(b) {}
};

// --- [[nodiscard]]: warn if the return value is ignored ---------------------
[[nodiscard]] int must_use() { return 42; }

// std::variant visitor via overload set (the classic "overloaded" trick).
template <class... Ts> struct overloaded : Ts... { using Ts::operator()...; };
template <class... Ts> overloaded(Ts...) -> overloaded<Ts...>; // CTAD guide

int main() {
    // 1. Structured bindings: unpack a pair/tuple/struct into named vars.
    std::map<std::string, int> ages{{"alice", 30}, {"bob", 25}};
    for (const auto& [name, age] : ages)
        std::cout << name << " is " << age << "\n";

    // 2. if with initializer: scope a variable to the condition.
    if (auto it = ages.find("alice"); it != ages.end())
        std::cout << "found alice=" << it->second << "\n";

    // 3. constexpr if.
    std::cout << describe(7) << " | " << describe(2.5) << " | "
              << describe(std::string("x")) << "\n";

    // 4. Fold expressions.
    std::cout << "sum=" << sum(1, 2, 3, 4, 5) << "  ";
    print_all("fold", "over", "comma");

    // 5. CTAD: no <int,double> needed.
    Pair p{1, 2.5};
    std::cout << "CTAD Pair: " << p.first << ", " << p.second << "\n";

    // 6. std::optional: a value that may be absent.
    std::optional<int> maybe = ages.count("carol") ? std::optional<int>{1} : std::nullopt;
    std::cout << "optional has_value=" << maybe.has_value()
              << " value_or=" << maybe.value_or(-1) << "\n";

    // 7. std::variant + visitor.
    std::variant<int, double, std::string> var = std::string("hello");
    std::visit(overloaded{
        [](int i)                { std::cout << "variant int " << i << "\n"; },
        [](double d)             { std::cout << "variant double " << d << "\n"; },
        [](const std::string& s) { std::cout << "variant string " << s << "\n"; },
    }, var);

    // 8. std::any: type-erased single value.
    std::any a = 3.14;
    std::cout << "any<double>=" << std::any_cast<double>(a) << "\n";

    // 9. std::string_view: non-owning, allocation-free substring.
    std::string_view sv = "the quick brown fox";
    std::cout << "string_view first word: " << sv.substr(0, sv.find(' ')) << "\n";

    // 10. std::apply: call a function with a tuple of args.
    auto add3 = [](int a, int b, int c) { return a + b + c; };
    std::cout << "apply: " << std::apply(add3, std::make_tuple(10, 20, 30)) << "\n";

    // 11. [[nodiscard]] + [[maybe_unused]].
    [[maybe_unused]] int used = must_use();
    std::cout << "nodiscard value=" << used << ", ns version=" << app::config::detail::kVersion << "\n";

    return 0;
}
