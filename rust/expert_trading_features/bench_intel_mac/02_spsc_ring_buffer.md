# Bench report — 02 Lock-free SPSC ring buffer

Source: [`../examples/02_spsc_ring_buffer.rs`](../examples/02_spsc_ring_buffer.rs) ·
Harness: [`../benches/bench_all.rs`](../benches/bench_all.rs) (`bench_02_spsc`) ·
C++: [`cpp/.../02_spsc_ring_buffer.cpp`](../../../cpp/expert_trading_features/02_spsc_ring_buffer.cpp) ·
Machine: see [README](README.md).

## What is measured

End-to-end throughput: one producer thread pushes 5,000,000 `u64`s through a
capacity-1024 lock-free queue, one consumer pops them all. Wall-clock over the whole
hand-off, reported as ns/tick and M ticks/s. Best of 7. Steady-state (spin-on-full /
spin-on-empty), so this is throughput, not isolated op latency.

## Results

| run | ns/tick | M ticks/s |
|----:|--------:|----------:|
| 1 | 6.60 | 152 |
| 2 | 4.35 | 230 |
| **representative** | **~5** | **~190** |

## Interpretation

- ~5 ns/tick (≈190M ticks/s) for a single producer/consumer pair, **no locks, no
  allocation** — the same design as the C++ version: two `acquire`/`release` atomics
  (no CAS loop), `CachePadded` head/tail on separate cache lines, power-of-two mask,
  and each side caching the other's index. Throughput is in the same ballpark as the
  C++ demo (the spin-backoff and thread scheduling dominate the variance).
- **What Rust adds over the C++ version:** the single-producer/single-consumer
  contract is *encoded in the types*. `channel()` hands back one `Producer` and one
  `Consumer`; neither is `Clone`, only `Producer` has `push`, only `Consumer` has
  `pop`, and `&mut self` means each side is owned by one thread. In C++ "single
  producer" is a comment you must not violate; here the borrow checker enforces it.
- The unsafe is confined to slot read/write behind a 100% safe API; `unsafe impl
  Send`/`Sync` document the exact ordering invariant that makes it sound.
- Variance (4.4–6.6 ns) is scheduler/turbo jitter on a laptop; pin threads and
  disable turbo for a stable figure.

## Reproduce

```sh
cargo bench                                       # see the 02_spsc_ring line
cargo run --release --example 02_spsc_ring_buffer  # the demo (checksum)
```
