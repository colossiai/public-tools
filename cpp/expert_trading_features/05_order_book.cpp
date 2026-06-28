// ============================================================================
// 05 — Array-indexed limit order book: O(1) updates, O(1) best bid/ask
// Compile:  clang++ -std=c++20 -O2 05_order_book.cpp -o bin/05 && bin/05
// ----------------------------------------------------------------------------
// The order book is the central data structure of a matching engine / market-
// data view. A std::map<price, level> is the textbook answer but it is a pointer-
// chasing red-black tree => cache misses on every operation.
//
// The low-latency design: prices live on a bounded integer TICK grid, so use a
// flat array indexed by tick. Then:
//   * add / cancel / execute at a price = O(1) array write (no tree balancing).
//   * best bid / best ask = O(1) amortized by tracking the current best and only
//     scanning when the best level empties.
//   * everything is contiguous => prefetch-friendly, deterministic latency.
//
// Trade-off: memory ~ number of ticks in range. Real systems window this around
// the touch and recenter as the market moves; here we keep a fixed band.
// ============================================================================

#include <cstdint>
#include <array>
#include <vector>
#include <iostream>
#include <format>
#include <map>
#include <random>
#include <chrono>

class OrderBook {
public:
    static constexpr std::int32_t kMinTick = 0;
    static constexpr std::int32_t kMaxTick = 1 << 16;   // 65,536 price levels

private:
    std::array<std::uint64_t, kMaxTick> bid_qty_{};     // resting qty per tick
    std::array<std::uint64_t, kMaxTick> ask_qty_{};
    std::int32_t best_bid_ = -1;                         // -1 => empty side
    std::int32_t best_ask_ = kMaxTick;                   // kMaxTick => empty side

public:
    // Add resting size at a price level — O(1).
    void add_bid(std::int32_t tick, std::uint64_t qty) {
        bid_qty_[tick] += qty;
        if (tick > best_bid_) best_bid_ = tick;          // new top of book
    }
    void add_ask(std::int32_t tick, std::uint64_t qty) {
        ask_qty_[tick] += qty;
        if (tick < best_ask_) best_ask_ = tick;
    }

    // Remove size (cancel/execute) — O(1), with cheap re-scan only if the top empties.
    void reduce_bid(std::int32_t tick, std::uint64_t qty) {
        bid_qty_[tick] -= qty;
        if (tick == best_bid_ && bid_qty_[tick] == 0) {
            while (best_bid_ >= kMinTick && bid_qty_[best_bid_] == 0) --best_bid_;
        }
    }
    void reduce_ask(std::int32_t tick, std::uint64_t qty) {
        ask_qty_[tick] -= qty;
        if (tick == best_ask_ && ask_qty_[tick] == 0) {
            while (best_ask_ < kMaxTick && ask_qty_[best_ask_] == 0) ++best_ask_;
        }
    }

    std::int32_t  best_bid() const { return best_bid_; }
    std::int32_t  best_ask() const { return best_ask_; }
    std::uint64_t bid_size(std::int32_t t) const { return bid_qty_[t]; }
    std::uint64_t ask_size(std::int32_t t) const { return ask_qty_[t]; }
    bool          crossed()  const { return best_bid_ >= best_ask_; }

    // Mid price in ticks (×2 to keep it integer when the spread is odd).
    std::int32_t mid_x2() const { return best_bid_ + best_ask_; }
};

// The textbook alternative: a balanced tree keyed by price. Same semantics
// (erase a level when it empties; best bid = highest key) but every op chases
// pointers through red-black nodes scattered across the heap.
class MapBook {
    std::map<std::int32_t, std::uint64_t> bids_;
public:
    void add_bid(std::int32_t tick, std::uint64_t qty) { bids_[tick] += qty; }
    void reduce_bid(std::int32_t tick, std::uint64_t qty) {
        auto it = bids_.find(tick);
        if (it == bids_.end()) return;
        it->second -= qty;
        if (it->second == 0) bids_.erase(it);     // level gone
    }
    std::int32_t best_bid() const {
        return bids_.empty() ? -1 : bids_.rbegin()->first;   // highest price
    }
};

static void print_top(const OrderBook& b, const char* tag) {
    std::cout << std::format("[{}] best_bid={} ({}) | best_ask={} ({}) | mid2={} | crossed={}\n",
                             tag, b.best_bid(), b.bid_size(b.best_bid()),
                             b.best_ask(), b.ask_size(b.best_ask()),
                             b.mid_x2(), b.crossed());
}

int main() {
    static OrderBook book;   // static: the array is large, keep it off the stack

    // Build a book around tick 10000.
    book.add_bid(9998, 300);
    book.add_bid(9999, 500);
    book.add_bid(10000, 200);     // top bid
    book.add_ask(10002, 400);     // top ask
    book.add_ask(10003, 600);
    print_top(book, "built");

    // Aggressive sell hits the top bid and clears it -> best bid walks down O(1) amortized.
    book.reduce_bid(10000, 200);
    print_top(book, "top bid filled");

    // New tighter ask improves the offer.
    book.add_ask(10001, 150);
    print_top(book, "ask improves");

    // Cancel the resting top ask -> best ask walks up to the next level.
    book.reduce_ask(10001, 150);
    book.reduce_ask(10002, 400);
    print_top(book, "asks cancelled");

    // --- Benchmark: flat array book vs std::map book --------------------------
    // Identical op stream on both: touch a resting level at a random nearby tick
    // (+1), read the top, then take it back (-1). We PRE-SEED a band of resting
    // levels first so the book stays populated around the touch — the regime these
    // books actually run in. (An add/cancel that empties the top makes the array
    // walk to the next level; that O(1)-amortized cost only bites if the book
    // drains, which a real book around the touch doesn't.) This isolates the
    // steady-state per-op cost: O(1) array index vs the tree's log(n) + pointer
    // chasing. Seed is fixed for reproducibility.
    constexpr std::size_t N = 5'000'000;
    constexpr std::int32_t kCenter = 32'768;     // middle of the tick band
    constexpr std::int32_t kBand   = 1'000;      // resting levels each side
    std::mt19937 rng(987654);
    std::uniform_int_distribution<std::int32_t> jitter(-kBand, kBand);

    std::vector<std::int32_t> ticks(N);
    for (auto& t : ticks) t = kCenter + jitter(rng);

    static OrderBook arr;                         // large arrays: keep off stack
    MapBook mb;
    for (std::int32_t t = kCenter - kBand; t <= kCenter + kBand; ++t) {
        arr.add_bid(t, 100);                      // base resting qty so a ±1
        mb.add_bid(t, 100);                       // touch never empties the level
    }

    std::int64_t sink_a = 0;
    auto a0 = std::chrono::steady_clock::now();
    for (std::size_t i = 0; i < N; ++i) {
        arr.add_bid(ticks[i], 1);
        sink_a += arr.best_bid();
        arr.reduce_bid(ticks[i], 1);
    }
    auto a1 = std::chrono::steady_clock::now();

    std::int64_t sink_m = 0;
    for (std::size_t i = 0; i < N; ++i) {
        mb.add_bid(ticks[i], 1);
        sink_m += mb.best_bid();
        mb.reduce_bid(ticks[i], 1);
    }
    auto a2 = std::chrono::steady_clock::now();

    double ns_arr = std::chrono::duration<double, std::nano>(a1 - a0).count() / N;
    double ns_map = std::chrono::duration<double, std::nano>(a2 - a1).count() / N;
    std::cout << std::format(
        "\nbench add+best+reduce over {} ops (sinks {} / {}):\n"
        "  array book : {:.3f} ns/op\n"
        "  std::map   : {:.3f} ns/op  (speedup {:.2f}x)\n",
        N, sink_a, sink_m, ns_arr, ns_map, ns_map / ns_arr);

    return 0;
}
