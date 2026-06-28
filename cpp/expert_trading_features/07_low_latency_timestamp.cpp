// ============================================================================
// 07 — Cycle-accurate timestamps & a latency histogram (HdR-style tail measurement)
// Compile:  clang++ -std=c++20 -O2 07_low_latency_timestamp.cpp -o bin/07 && bin/07
// ----------------------------------------------------------------------------
// You cannot optimize what you cannot measure, and in trading the TAIL is what
// matters (the 99.9th percentile loss-making outlier, not the mean).
//
// Techniques shown:
//   * rdtsc / rdtscp — read the CPU's time-stamp counter directly (~5-10 ns)
//     instead of a syscall-backed clock. On modern x86 the TSC is invariant
//     (constant rate regardless of frequency scaling), so it's a stable tick.
//   * Compiler/CPU fence around the measurement so instructions don't reorder
//     out of the timed region (rdtscp + lfence).
//   * A simple latency histogram to recover percentiles (p50/p99/p99.9/max),
//     because averages hide the tail that actually hurts.
// ============================================================================

#include <cstdint>
#include <vector>
#include <algorithm>
#include <chrono>
#include <iostream>
#include <format>

#if defined(__x86_64__) || defined(_M_X64)
#include <x86intrin.h>
inline std::uint64_t cpu_ticks() {
    unsigned aux;
    _mm_lfence();                  // don't let earlier work drift past the read
    std::uint64_t t = __rdtscp(&aux);
    _mm_lfence();
    return t;
}
inline constexpr bool kHasTsc = true;
#else
inline std::uint64_t cpu_ticks() {
    return std::chrono::steady_clock::now().time_since_epoch().count();
}
inline constexpr bool kHasTsc = false;
#endif

// Estimate TSC ticks-per-nanosecond by timing a fixed wall-clock interval.
static double calibrate_ticks_per_ns() {
    auto w0 = std::chrono::steady_clock::now();
    std::uint64_t c0 = cpu_ticks();
    while (std::chrono::steady_clock::now() - w0 < std::chrono::milliseconds(50)) { /*spin*/ }
    std::uint64_t c1 = cpu_ticks();
    auto w1 = std::chrono::steady_clock::now();
    double ns = std::chrono::duration<double, std::nano>(w1 - w0).count();
    return static_cast<double>(c1 - c0) / ns;
}

// The "work" we want to profile: a tiny order-encode step.
[[gnu::noinline]] std::uint64_t encode_order(std::uint64_t id, std::int64_t px, std::uint32_t qty) {
    std::uint64_t h = id * 1099511628211ull;   // FNV-ish mix, just to do real work
    h ^= static_cast<std::uint64_t>(px); h *= 1099511628211ull;
    h ^= qty;
    return h;
}

int main() {
    const double tpns = kHasTsc ? calibrate_ticks_per_ns() : 1.0;
    std::cout << std::format("TSC available: {}   (~{:.3f} ticks/ns)\n", kHasTsc, tpns);

    constexpr std::size_t N = 200'000;
    std::vector<std::uint64_t> samples;
    samples.reserve(N);

    std::uint64_t sink = 0;
    for (std::size_t i = 0; i < N; ++i) {
        std::uint64_t start = cpu_ticks();
        sink ^= encode_order(i, 100'0000 + static_cast<std::int64_t>(i % 7), 100);
        std::uint64_t end = cpu_ticks();
        samples.push_back(end - start);
    }

    // Convert to ns and recover percentiles by sorting (fine for an offline report).
    std::vector<double> ns(samples.size());
    for (std::size_t i = 0; i < samples.size(); ++i)
        ns[i] = kHasTsc ? samples[i] / tpns : static_cast<double>(samples[i]);
    std::sort(ns.begin(), ns.end());

    auto pct = [&](double p) { return ns[static_cast<std::size_t>(p / 100.0 * (ns.size() - 1))]; };
    std::cout << std::format("encode_order latency over {} samples (sink={:#x}):\n", N, sink);
    std::cout << std::format("  p50   = {:7.2f} ns\n", pct(50));
    std::cout << std::format("  p99   = {:7.2f} ns\n", pct(99));
    std::cout << std::format("  p99.9 = {:7.2f} ns\n", pct(99.9));
    std::cout << std::format("  max   = {:7.2f} ns   <-- the tail you actually fear\n", ns.back());
    return 0;
}
