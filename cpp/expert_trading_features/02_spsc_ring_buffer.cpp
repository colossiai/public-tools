// ============================================================================
// 02 — Lock-free SPSC ring buffer: the workhorse queue of a trading stack
// Compile:  clang++ -std=c++20 -O2 02_spsc_ring_buffer.cpp -o bin/02 && bin/02
// ----------------------------------------------------------------------------
// Pattern: one producer thread (e.g. the NIC/feed-handler) hands messages to
// one consumer thread (e.g. the strategy) with NO locks and NO allocation.
//
// Key low-latency techniques shown:
//   * Single-producer / single-consumer => only two atomics, no CAS loop.
//   * acquire/release memory ordering (not seq_cst) for the cheapest correct sync.
//   * head and tail live on SEPARATE cache lines (alignas) to avoid false sharing
//     between producer and consumer.
//   * Power-of-two capacity => index wrap is a bitmask, not a modulo.
//   * Cached opposite-index: each side caches the other pointer to avoid hammering
//     a shared atomic on every operation.
// ============================================================================

#include <atomic>
#include <array>
#include <cstdint>
#include <thread>
#include <iostream>
#include <format>
#include <chrono>
#include <new>

inline constexpr std::size_t kCacheLine = 64;   // std::hardware_destructive_interference_size

template <typename T, std::size_t Capacity>
class SpscRing {
    static_assert((Capacity & (Capacity - 1)) == 0, "Capacity must be a power of two");
    static constexpr std::size_t kMask = Capacity - 1;

    std::array<T, Capacity> buf_{};

    // Producer-owned and consumer-owned indices, each on its own cache line so the
    // two threads never invalidate each other's line ("false sharing").
    alignas(kCacheLine) std::atomic<std::size_t> head_{0};   // next write slot (producer)
    alignas(kCacheLine) std::atomic<std::size_t> tail_{0};   // next read slot  (consumer)

    // Per-thread caches of the other side's index (no sharing, plain members).
    alignas(kCacheLine) std::size_t cached_tail_{0};         // producer's view of tail
    std::size_t cached_head_{0};                             // consumer's view of head

public:
    // Producer side.
    bool try_push(const T& v) {
        const std::size_t head = head_.load(std::memory_order_relaxed);
        const std::size_t next = head + 1;
        if (next - cached_tail_ > Capacity) {               // maybe full? refresh cache
            cached_tail_ = tail_.load(std::memory_order_acquire);
            if (next - cached_tail_ > Capacity) return false;   // genuinely full
        }
        buf_[head & kMask] = v;
        head_.store(next, std::memory_order_release);       // publish the slot
        return true;
    }

    // Consumer side.
    bool try_pop(T& out) {
        const std::size_t tail = tail_.load(std::memory_order_relaxed);
        if (tail == cached_head_) {                          // maybe empty? refresh cache
            cached_head_ = head_.load(std::memory_order_acquire);
            if (tail == cached_head_) return false;          // genuinely empty
        }
        out = buf_[tail & kMask];
        tail_.store(tail + 1, std::memory_order_release);    // free the slot
        return true;
    }
};

// A market-data tick, kept small & trivially copyable so push/pop is a memcpy.
struct Tick {
    std::uint64_t seq;
    std::int64_t  price;     // fixed-point ticks
    std::uint32_t qty;
};

int main() {
    static SpscRing<Tick, 1024> ring;        // static => no heap, lives for program
    constexpr std::uint64_t N = 5'000'000;

    std::uint64_t checksum = 0;
    auto t0 = std::chrono::steady_clock::now();
    std::thread consumer([&] {
        std::uint64_t got = 0;
        Tick t;
        while (got < N) {
            if (ring.try_pop(t)) { checksum += t.price; ++got; }
            else std::this_thread::yield();  // queue empty: back off
        }
    });

    std::thread producer([&] {
        for (std::uint64_t i = 0; i < N; ++i) {
            Tick t{i, static_cast<std::int64_t>(100'0000 + (i % 50)), 100};
            while (!ring.try_push(t)) std::this_thread::yield();  // queue full: back off
        }
    });

    producer.join();
    consumer.join();
    auto t1 = std::chrono::steady_clock::now();

    // --- Throughput benchmark -------------------------------------------------
    // End-to-end: one push + one pop per tick handed across the cache-coherence
    // fabric. ns/tick is the amortized producer+consumer cost; the spin-yield on
    // full/empty means this is steady-state throughput, not isolated op latency.
    double ns = std::chrono::duration<double, std::nano>(t1 - t0).count();
    double per_tick = ns / N;
    double mtps = (N / ns) * 1000.0;     // million ticks per second
    std::cout << std::format("SPSC ring: passed {} ticks lock-free, checksum={}\n",
                             N, checksum);
    std::cout << std::format("bench: {:.2f} ns/tick   {:.1f}M ticks/s   (wall {:.1f} ms)\n",
                             per_tick, mtps, ns / 1e6);
    return 0;
}
