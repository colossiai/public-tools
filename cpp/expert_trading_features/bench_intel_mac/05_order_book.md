# Bench report — 05 Array-indexed order book

Source: [`../05_order_book.cpp`](../05_order_book.cpp) ·
Technique: prices live on a bounded integer tick grid, so the book is a flat array
indexed by tick — O(1) update, O(1)-amortized best bid/ask — vs. a `std::map` tree.

## Environment

| | |
|---|---|
| CPU | Intel Core i7-9750H @ 2.60 GHz (Coffee Lake, 6C/12T, turbo to ~4.5 GHz) |
| OS / arch | macOS (Darwin 25.5), x86_64 |
| Compiler | Apple clang 21.0.0, libc++ |
| Flags | `-std=c++20 -O2 -Wall -Wextra -pthread` |

> Laptop, turbo + frequency scaling left on, threads not pinned. Numbers are
> *illustrative ratios*.

## What is measured

An identical op stream of `N = 5,000,000` ops on both structures: **touch a resting
level** at a random nearby tick (`add_bid(t, 1)`), read the top (`best_bid()`), then
take it back (`reduce_bid(t, 1)`). Ticks are drawn (fixed seed) from a ±1,000 band
around the center.

- **array book** — `OrderBook`: flat `std::array` indexed by tick + cached best.
- **std::map** — `std::map<int32, uint64>`, best bid = `rbegin()`.

> **Measurement note.** Both books are **pre-seeded** with resting qty across the whole
> band before timing. This is deliberate: it keeps the book populated around the touch
> — the regime these books actually run in. An add/cancel that *empties the top* makes
> the array walk down to the next non-empty level; that O(1)-amortized cost only bites
> if the book drains, which a real book around the touch doesn't. Without seeding, the
> open-then-immediately-close pattern empties the top every iteration and the array's
> walk-down dominates (measured ~17,000 ns/op — a pathological, unrepresentative case).
> Seeding isolates the **steady-state** per-op cost.

## Results (3 runs)

| run | array book ns/op | std::map ns/op | speedup |
|----:|-----------------:|---------------:|--------:|
| 1 | 1.368 | 117.156 | 85.6× |
| 2 | 1.641 | 110.741 | 67.5× |
| 3 | 1.347 | 107.251 | 79.6× |
| **representative** | **~1.4** | **~112** | **~78×** |

## Interpretation

- Steady state, the array book is ~**78× faster** per op. The array does an O(1) index
  + O(1) cached-best read; the `std::map` does an O(log n) lookup that **chases
  pointers** through red-black nodes scattered on the heap — a cache miss per hop.
- Honest trade-offs:
  - **The array's edge case is real.** If the top level empties, `reduce_bid` scans
    down to the next populated tick. It's O(1) *amortized* for a normal book but can
    spike if the book genuinely drains; production systems window the array around the
    touch and recenter as the market moves.
  - **Memory.** The array costs ~one slot per tick in range; the map only stores live
    levels. The flat layout trades memory for speed and determinism.
- This is "mechanical sympathy": a contiguous, index-addressed layout beats a
  pointer-chasing tree by ~2 orders of magnitude on the hot path.

## Reproduce

```sh
make bin/05_order_book && bin/05_order_book
```
