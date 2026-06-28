# Bench report — 01 Fixed-point price

Source: [`../examples/01_fixed_point_price.rs`](../examples/01_fixed_point_price.rs) ·
Harness: [`../benches/bench_all.rs`](../benches/bench_all.rs) (`bench_01_fixed_point`) ·
C++: [`cpp/.../01_fixed_point_price.cpp`](../../../cpp/expert_trading_features/01_fixed_point_price.cpp) ·
Machine: see [README](README.md).

## What is measured

A tight **add + compare** dependency chain, 100,000,000 iterations, run two ways:
integer ticks (`i64`) vs `f64`, each accumulating and comparing against a step value
(`black_box`-ed so the chain can't be constant-folded). Best of 7.

## Results

| run | int (ms) | f64 (ms) | ratio (f64 / int) |
|----:|---------:|---------:|------------------:|
| 1 | 55.95 | 101.40 | 1.81× |
| 2 | 55.56 | 100.73 | 1.81× |
| **representative** | **~55.7** | **~101** | **~1.81×** |

## Interpretation

- **The headline reason for fixed-point is correctness, not speed** — the demo shows
  `0.1 + 0.2 != 0.3` in `f64` but exact in `Px`. But here integer is also **~1.8×
  faster**: this is a latency-bound dependent chain, and an integer add (~1 cycle)
  has lower latency than an `f64` add (~3–4 cycles). You give up nothing on speed to
  gain exactness.
- **What Rust adds over the C++ version:** `Px` is a `#[repr(transparent)]` newtype,
  so it's a *distinct type* from a bare `i64` and from `Qty` — mixing a price and a
  quantity is a compile error, at zero layout cost (`size_of::<Px>() == 8`). Overflow
  is explicit (`checked_add`) and debug builds panic rather than silently wrapping.
- The win is specific to dependent arithmetic; a vectorizable throughput loop would
  narrow the gap. The point stands: exact integer prices are free (or faster).

## Reproduce

```sh
cargo bench   # see the 01_fixed_point line
```
