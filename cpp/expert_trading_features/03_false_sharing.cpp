// ============================================================================
// 03 — False sharing: the silent latency killer (and how alignas kills it)
// Compile:  clang++ -std=c++20 -O2 03_false_sharing.cpp -o bin/03 && bin/03
// ----------------------------------------------------------------------------
// Two threads writing two DIFFERENT variables should be independent. But if both
// variables sit on the SAME 64-byte cache line, every write by one core
// invalidates the line in the other core's cache => the cache-coherence protocol
// (MESI) ping-pongs the line back and forth. Throughput collapses.
//
// Fix: put each hot, independently-written counter on its OWN cache line with
// `alignas(64)`. This is everywhere in trading code: per-thread stats, the
// head/tail of an SPSC queue (see demo 02), per-symbol sequence numbers, etc.
//
// This program measures both layouts so you can see the difference live.
// ============================================================================

#include <atomic>
#include <thread>
#include <chrono>
#include <cstdint>
#include <iostream>
#include <format>

inline constexpr std::size_t kCacheLine = 64;
constexpr std::uint64_t kIters = 100'000'000;

// PACKED: two counters adjacent -> almost certainly same cache line.
struct Packed {
    std::atomic<std::uint64_t> a{0};
    std::atomic<std::uint64_t> b{0};
};

// PADDED: each counter forced onto its own cache line.
struct Padded {
    alignas(kCacheLine) std::atomic<std::uint64_t> a{0};
    alignas(kCacheLine) std::atomic<std::uint64_t> b{0};
};

template <typename Counters>
double bench(const char* label) {
    Counters c;
    auto hammer = [](std::atomic<std::uint64_t>& x) {
        for (std::uint64_t i = 0; i < kIters; ++i)
            x.fetch_add(1, std::memory_order_relaxed);
    };

    auto t0 = std::chrono::steady_clock::now();
    std::thread t1([&] { hammer(c.a); });
    std::thread t2([&] { hammer(c.b); });
    t1.join(); t2.join();
    auto t1d = std::chrono::steady_clock::now();

    double ns = std::chrono::duration<double, std::nano>(t1d - t0).count();
    double per_op = ns / (2.0 * kIters);
    std::cout << std::format("{:<8} {:>6.2f} ns/op   (a={}, b={})\n",
                             label, per_op, c.a.load(), c.b.load());
    return per_op;
}

int main() {
    std::cout << std::format("cache line = {} bytes, {} increments per thread\n\n",
                             kCacheLine, kIters);
    double packed = bench<Packed>("packed");   // false sharing
    double padded = bench<Padded>("padded");   // isolated lines
    std::cout << std::format("\npadding speedup: {:.2f}x  (sizeof Packed={}, Padded={})\n",
                             packed / padded, sizeof(Packed), sizeof(Padded));
    return 0;
}
