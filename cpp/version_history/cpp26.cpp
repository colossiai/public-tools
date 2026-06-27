// ============================================================================
// C++26 feature tour  (WORK IN PROGRESS standard — needs a bleeding-edge toolchain)
// Compile:  clang++ -std=c++26 cpp26.cpp -o cpp26 && ./cpp26
// ----------------------------------------------------------------------------
// C++26 is not finalized; compiler support is partial and varies a lot. The
// features below are the ones that already compile on a recent clang/libc++.
// Other landmark C++26 features (reflection, contracts, std::execution senders/
// receivers, hazard pointers/RCU) are described in the README but not demoed
// because no shipping compiler implements them end-to-end yet.
//
//   Language: pack indexing (pack...[N]), #embed, `= delete("reason")`,
//             the `_` placeholder, structured bindings in conditions
//   Library:  (mostly carried forward; reflection/std::execution pending)
// ============================================================================

#include <print>
#include <tuple>
#include <string>
#include <array>

// --- 1. Pack indexing: directly index into a parameter pack ------------------
// Before C++26 you needed std::tuple/recursion to get "the Nth pack element".
template <typename... Ts>
auto first(Ts... args) { return args...[0]; }            // 0th element

template <typename... Ts>
auto last(Ts... args) { return args...[sizeof...(Ts) - 1]; }

// Type pack indexing works too: pick the type of the Nth parameter.
template <typename... Ts>
using second_type = Ts...[1];

// --- 2. `= delete("reason")`: deletion with a human-readable diagnostic ------
void use_safe_api();
void unsafe_api() = delete("unsafe_api was removed; call use_safe_api() instead");
void use_safe_api() { std::println("called the safe API"); }

int main() {
    // 1. Pack indexing.
    std::println("pack first(10,20,30)={}, last=...{}", first(10, 20, 30), last(10, 20, 30));
    static_assert(std::is_same_v<second_type<int, double, char>, double>);
    std::println("pack type indexing: second_type<int,double,char> is double");

    // 2. The `_` placeholder: a "don't care" name you may redeclare freely.
    auto _ = 1;          // first throwaway
    auto _ = 2;          // legal: redeclaring `_` is allowed, no shadow warning
    std::println("placeholder `_` can be declared multiple times in one scope");

    // Common real use: ignore some structured-binding members without warnings.
    auto [keep, _] = std::tuple{42, 999};
    std::println("structured binding ignoring the 2nd with `_`: keep={}", keep);

    // 3. = delete("reason") — calling unsafe_api() would now emit that message.
    use_safe_api();

    // 4. #embed: pull a file's bytes straight into the program at compile time.
    //    Here we embed THIS source file and report how it starts.
    static constexpr unsigned char self_head[] = {
        #embed __FILE__ limit(16)        // first 16 bytes of this file
    };
    std::print("#embed first 16 bytes of this file: ");
    for (unsigned char b : self_head) std::print("{:02x} ", b);
    std::println("");
    std::println("first byte as char = '{}'", static_cast<char>(self_head[0]));

    return 0;
}
