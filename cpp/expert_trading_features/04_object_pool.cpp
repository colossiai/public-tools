// ============================================================================
// 04 — Object pool / free list: zero allocation on the hot path
// Compile:  clang++ -std=c++20 -O2 04_object_pool.cpp -o bin/04 && bin/04
// ----------------------------------------------------------------------------
// `new`/`malloc` are forbidden on a trading hot path: they take a lock, can
// touch the kernel, and have a long, unpredictable tail latency (page faults,
// arena contention). Instead, pre-allocate ALL objects up front and hand them
// out from an intrusive free list.
//
// Techniques shown:
//   * Contiguous storage reserved once at startup (cache-friendly, no heap churn).
//   * Intrusive free list: a freed slot stores the index of the next free slot,
//     so acquire()/release() are O(1) pointer flips with no metadata allocation.
//   * Deterministic latency: every acquire is the same handful of instructions.
// ============================================================================

#include <cstdint>
#include <vector>
#include <array>
#include <iostream>
#include <format>
#include <chrono>
#include <cassert>

// A resting order in the book — what we want to allocate millions of times/day.
struct Order {
    std::uint64_t id;
    std::int64_t  price;     // fixed-point
    std::uint32_t qty;
    char          side;      // 'B' or 'S'
};

template <typename T, std::size_t N>
class ObjectPool {
    // union-like storage: a slot is either a live T or a "next free index".
    struct Slot {
        alignas(T) unsigned char storage[sizeof(T)];
        std::size_t next_free;
    };
    std::vector<Slot> slots_;            // one big contiguous block, allocated once
    std::size_t free_head_;
    std::size_t in_use_ = 0;
    static constexpr std::size_t kNil = ~std::size_t{0};

public:
    ObjectPool() : slots_(N) {
        for (std::size_t i = 0; i < N; ++i) slots_[i].next_free = i + 1;
        slots_[N - 1].next_free = kNil;
        free_head_ = 0;
    }

    // O(1), no heap. Returns nullptr when exhausted (caller decides policy).
    template <typename... Args>
    T* acquire(Args&&... args) {
        if (free_head_ == kNil) return nullptr;
        std::size_t idx = free_head_;
        free_head_ = slots_[idx].next_free;
        ++in_use_;
        return new (slots_[idx].storage) T{std::forward<Args>(args)...};  // placement new
    }

    // O(1) return to the pool.
    void release(T* p) {
        p->~T();
        auto* slot = reinterpret_cast<Slot*>(reinterpret_cast<unsigned char*>(p));
        std::size_t idx = static_cast<std::size_t>(slot - slots_.data());
        assert(idx < N);
        slots_[idx].next_free = free_head_;
        free_head_ = idx;
        --in_use_;
    }

    std::size_t in_use() const { return in_use_; }
    static constexpr std::size_t capacity() { return N; }
};

int main() {
    static ObjectPool<Order, 1 << 16> pool;     // 65,536 orders, reserved at startup
    std::cout << std::format("pool capacity = {} orders, allocated once up front\n",
                             pool.capacity());

    // Simulate a churn of resting orders: acquire, then cancel half.
    std::array<Order*, 1000> live{};
    for (std::size_t i = 0; i < live.size(); ++i)
        live[i] = pool.acquire(Order{1000 + i, 100'0000 + static_cast<std::int64_t>(i),
                                     100, (i & 1) ? 'B' : 'S'});

    std::cout << std::format("after 1000 acquires: in_use={}\n", pool.in_use());

    std::uint64_t notional = 0;
    for (std::size_t i = 0; i < live.size(); i += 2) {   // cancel the even ones
        notional += static_cast<std::uint64_t>(live[i]->price) * live[i]->qty;
        pool.release(live[i]);
        live[i] = nullptr;
    }
    std::cout << std::format("after cancelling 500: in_use={} (slots recycled, no free())\n",
                             pool.in_use());

    // Reacquire — the freed slots come right back, hot in cache.
    for (std::size_t i = 0; i < live.size(); i += 2)
        live[i] = pool.acquire(Order{9000 + i, 200'0000, 50, 'S'});
    std::cout << std::format("after reacquiring 500: in_use={}, cancelled notional={}\n",
                             pool.in_use(), notional);

    // --- Benchmark: pool acquire/release vs new/delete ------------------------
    // The hot-path pattern is acquire -> use -> release, repeated. We time an
    // identical acquire/touch/release loop against `new`/`delete`. The pool wins
    // not just on the mean but — the part that matters for trading — by removing
    // malloc's unbounded tail (locks, arena contention, page faults).
    //
    // NOTE: we force the pointer to "escape" each iteration. Without this, clang
    // happily proves the new/delete pair is dead and deletes it outright (heap
    // allocation elision), making the heap path look instant and the bench a lie.
    static ObjectPool<Order, 1 << 16> bp;     // its own pool for the bench
    constexpr std::size_t N = 20'000'000;
    std::uint64_t sink = 0;
    auto escape = [](void* p) { asm volatile("" : : "g"(p) : "memory"); };

    auto t0 = std::chrono::steady_clock::now();
    for (std::size_t i = 0; i < N; ++i) {
        Order* o = bp.acquire(Order{i, 100'0000 + static_cast<std::int64_t>(i & 1023),
                                    100, (i & 1) ? 'B' : 'S'});
        escape(o);
        sink += o->id ^ static_cast<std::uint64_t>(o->price);   // touch it
        bp.release(o);
    }
    auto t1 = std::chrono::steady_clock::now();

    for (std::size_t i = 0; i < N; ++i) {
        Order* o = new Order{i, 100'0000 + static_cast<std::int64_t>(i & 1023),
                             100, (i & 1) ? 'B' : 'S'};
        escape(o);
        sink += o->id ^ static_cast<std::uint64_t>(o->price);
        delete o;
    }
    auto t2 = std::chrono::steady_clock::now();

    double ns_pool = std::chrono::duration<double, std::nano>(t1 - t0).count() / N;
    double ns_heap = std::chrono::duration<double, std::nano>(t2 - t1).count() / N;
    std::cout << std::format(
        "\nbench acquire/touch/release over {} iters (sink={:#x}):\n"
        "  object pool : {:.3f} ns/op\n"
        "  new/delete  : {:.3f} ns/op  (speedup {:.2f}x, and no allocator tail)\n",
        N, sink, ns_pool, ns_heap, ns_heap / ns_pool);
    return 0;
}
