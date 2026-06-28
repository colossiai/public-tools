// ============================================================================
// 06 — Branch hints, branchless code & software prefetch
// Compile:  clang++ -std=c++20 -O2 06_branch_and_prefetch.cpp -o bin/06 && bin/06
// ----------------------------------------------------------------------------
// On the hot path a single mispredicted branch (~15-20 cycles) or an L2/L3 cache
// miss (tens to hundreds of cycles) dwarfs the actual work. Three tools:
//
//   1. [[likely]] / [[unlikely]]  — tell the compiler which way a branch goes so
//      it lays out the hot path as the fall-through (e.g. "message is valid" is
//      likely; "risk breach" is unlikely).
//   2. Branchless selection       — replace an unpredictable data-dependent branch
//      with arithmetic/cmov so there is nothing to mispredict.
//   3. __builtin_prefetch         — pull the next record into cache while we work
//      on the current one, hiding memory latency when you know the access pattern.
//
// We benchmark a branchy vs branchless inner loop over random data.
// ============================================================================

#include <cstdint>
#include <vector>
#include <random>
#include <chrono>
#include <iostream>
#include <format>

// A risk check that the compiler should treat as almost-always-passing.
inline bool passes_risk(std::int64_t notional, std::int64_t limit) {
    if (notional <= limit) [[likely]] {
        return true;
    } else [[unlikely]] {
        return false;     // breach: rare, cold path
    }
}

int main() {
    constexpr std::size_t N = 1 << 22;        // ~4M samples
    std::vector<std::int32_t> data(N);

    std::mt19937 rng(12345);                  // fixed seed: reproducible
    std::uniform_int_distribution<int> dist(0, 100);
    for (auto& x : data) x = dist(rng);

    // --- Branchy: data-dependent, unpredictable branch (threshold in the middle).
    auto t0 = std::chrono::steady_clock::now();
    std::int64_t sum_branchy = 0;
    for (std::size_t i = 0; i < N; ++i) {
        if (data[i] >= 50)                     // ~50/50 => worst case for the predictor
            sum_branchy += data[i];
    }
    auto t1 = std::chrono::steady_clock::now();

    // --- Branchless: turn the condition into a 0/-1 mask, no branch to mispredict.
    std::int64_t sum_branchless = 0;
    for (std::size_t i = 0; i < N; ++i) {
        std::int32_t v = data[i];
        std::int32_t mask = -(v >= 50);        // 0 or 0xFFFFFFFF
        sum_branchless += (v & mask);          // adds v or 0, no branch
    }
    auto t2 = std::chrono::steady_clock::now();

    double ns_branchy    = std::chrono::duration<double, std::nano>(t1 - t0).count() / N;
    double ns_branchless = std::chrono::duration<double, std::nano>(t2 - t1).count() / N;

    std::cout << std::format("branchy    : {:.3f} ns/elem  sum={}\n", ns_branchy, sum_branchy);
    std::cout << std::format("branchless : {:.3f} ns/elem  sum={}  (speedup {:.2f}x)\n",
                             ns_branchless, sum_branchless, ns_branchy / ns_branchless);

    // --- Software prefetch over a pointer-chasing-ish stride -------------------
    // Sum every record but prefetch a few iterations ahead to hide the miss.
    std::int64_t sum_pf = 0;
    constexpr std::size_t kAhead = 16;         // tune to your latency/IPC
    auto t3 = std::chrono::steady_clock::now();
    for (std::size_t i = 0; i < N; ++i) {
        if (i + kAhead < N)
            __builtin_prefetch(&data[i + kAhead], 0 /*read*/, 1 /*low temporal locality*/);
        sum_pf += data[i];
    }
    auto t4 = std::chrono::steady_clock::now();
    std::cout << std::format("prefetched : {:.3f} ns/elem  sum={}\n",
                             std::chrono::duration<double, std::nano>(t4 - t3).count() / N, sum_pf);

    // [[likely]] demo result (kept from being optimized away).
    std::int64_t accepted = 0;
    for (std::size_t i = 0; i < N; ++i)
        accepted += passes_risk(data[i], 1'000'000);   // always passes here
    std::cout << std::format("risk-check accepted {} / {} orders (hot path = fall-through)\n",
                             accepted, N);

    std::cout <<
        "\nreality check: at -O2 clang often compiles the 'branchy' loop to a\n"
        "branchless cmov already, so the two can tie — always check the asm/measure.\n"
        "Prefetch only wins when the data is COLD and the access is far enough ahead;\n"
        "here the array is already hot in cache, so the prefetch can even cost a little.\n";
    return 0;
}
