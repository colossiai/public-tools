# Bench report — 10 Fearless concurrency

Source: [`../examples/10_concurrency.rs`](../examples/10_concurrency.rs) ·
Harness: [`../benches/bench_all.rs`](../benches/bench_all.rs) (`bench_10_concurrency`) ·
Machine: see [README](README.md).

## What is measured

Speedup from splitting a sum of 50,000,000 `u64`s across scoped threads: 1 vs 4 vs 8
workers (chunks summed in parallel, then combined). Best of 7. The machine has 6
physical cores / 12 threads.

## Results

| run | 1 thread (ms) | 4 threads (ms) | speedup | 8 threads (ms) | speedup |
|----:|--------------:|---------------:|--------:|---------------:|--------:|
| 1 | 24.62 | 16.84 | 1.46× | 17.89 | 1.38× |
| 2 | 27.06 | 14.89 | 1.82× | 18.59 | 1.46× |
| **representative** | **~26** | **~16** | **~1.6×** | **~18** | **~1.4×** |

## Interpretation

- Real speedup (~1.6× at 4 threads), but **sub-linear, and 8 threads is no better
  than 4** — and that's the honest lesson, not a measurement bug. Summing a 400 MB
  array is **memory-bandwidth-bound**: a few cores already saturate the memory bus,
  so adding more gives diminishing returns. CPU-bound work (per-element compute)
  would scale much closer to linear.
- What's notable for *Rust* is what you **don't** see: no data races, no locks needed
  here. `thread::scope` lets the workers borrow the input slice directly because the
  scope guarantees they finish before it returns — the borrow checker proves it safe
  with zero `Arc`/clone overhead.
- For shared mutable state you'd add `Arc<Mutex<_>>` (demo 10's other example) or go
  lock-free with atomics (demo 11) — each with its own cost profile.

## Reproduce

```sh
cargo bench   # see the 10_concurrency line
```
