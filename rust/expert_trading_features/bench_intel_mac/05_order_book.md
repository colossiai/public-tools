# Bench report — 05 Array-indexed order book

Source: [`../examples/05_order_book.rs`](../examples/05_order_book.rs) ·
Harness: [`../benches/bench_all.rs`](../benches/bench_all.rs) (`bench_05_order_book`) ·
C++: [`cpp/.../05_order_book.cpp`](../../../cpp/expert_trading_features/05_order_book.cpp) ·
Machine: see [README](README.md).

## What is measured

An identical op stream of 5,000,000 ops on both structures: touch a resting level at
a random nearby tick (`+1`), read the top, then take it back (`-1`). Both books are
**pre-seeded** across a ±1,000-tick band so they stay populated (the regime these run
in). Flat `Vec<u64>` indexed by tick vs `BTreeMap<i32, u64>`. ns/op, best of 7.

## Results

| run | array (ns/op) | `BTreeMap` (ns/op) | speedup |
|----:|--------------:|-------------------:|--------:|
| 1 | 0.86 | 91.61 | 107× |
| 2 | 0.83 | 94.68 | 114× |
| **representative** | **~0.85** | **~93** | **~110×** |

## Interpretation

- Steady state, the flat array is ~**110× faster** per op: an O(1) index + cached-best
  read vs the tree's O(log n) lookup that **chases pointers** through red-black nodes
  scattered on the heap — a cache miss per hop. This matches the C++ array-vs-tree
  result.
- Honest trade-offs (same as C++): the array costs ~one slot per tick in range
  (memory for speed), and `reduce` can walk down if the top level *empties* — O(1)
  amortized for a populated book, but it can spike if the book drains. Real systems
  window the array around the touch and recenter.
- **What Rust adds:** the flat grid is a heap `Vec` sized at construction (no risk of
  a huge stack array), with bounds checks in debug and elided in release where
  provably safe.

## Reproduce

```sh
cargo bench   # see the 05_order_book line
```
