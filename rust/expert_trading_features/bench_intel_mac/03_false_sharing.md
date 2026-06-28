# Bench report — 03 False sharing

Source: [`../examples/03_false_sharing.rs`](../examples/03_false_sharing.rs) ·
Harness: [`../benches/bench_all.rs`](../benches/bench_all.rs) (`bench_03_false_sharing`) ·
C++: [`cpp/.../03_false_sharing.cpp`](../../../cpp/expert_trading_features/03_false_sharing.cpp) ·
Machine: see [README](README.md).

## What is measured

Two threads each `fetch_add` their own atomic counter 100,000,000 times, in two
layouts: **packed** (two `AtomicU64` adjacent → same cache line) vs **padded** (each
wrapped in `CachePadded`, i.e. `#[repr(align(64))]` → its own line). ns/op, best of 3
inner timings.

## Results

| run | packed (ns/op) | padded (ns/op) | speedup |
|----:|---------------:|---------------:|--------:|
| 1 | 15.36 | 2.28 | 6.72× |
| 2 | 14.03 | 2.30 | 6.11× |
| **representative** | **~14.7** | **~2.3** | **~6.4×** |

## Interpretation

- The two threads write *different* variables, so this should be embarrassingly
  parallel. Packed, they share a line, so every increment invalidates the other
  core's copy and the line ping-pongs over the coherence fabric — ~6.4× slower.
- The fix costs only memory: `CachePadded<AtomicU64>` (16 B → 128 B for the pair).
- **What Rust adds over the C++ version:** `alignas(64)` becomes
  `#[repr(align(64))]`, wrapped once as a reusable `CachePadded<T>` in the crate's
  `lib.rs` — the *same* type the SPSC ring (demo 02) uses for its head/tail. Same
  idea, same ~6× effect as the C++ demo.

## Reproduce

```sh
cargo bench                                    # see the 03_false_sharing line
cargo run --release --example 03_false_sharing  # the demo prints its own numbers too
```
