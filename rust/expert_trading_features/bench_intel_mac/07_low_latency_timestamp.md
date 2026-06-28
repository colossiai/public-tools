# Bench report — 07 Cycle-accurate timestamps & latency tail

Source: [`../examples/07_low_latency_timestamp.rs`](../examples/07_low_latency_timestamp.rs) ·
Harness: [`../benches/bench_all.rs`](../benches/bench_all.rs) (`bench_07_timestamp`) ·
C++: [`cpp/.../07_low_latency_timestamp.cpp`](../../../cpp/expert_trading_features/07_low_latency_timestamp.cpp) ·
Machine: see [README](README.md).

## What is measured

`encode_order()` (a tiny `#[inline(never)]` FNV-style mix) timed 200,000 times, each
call bracketed by `rdtscp` + `lfence` so surrounding work can't reorder into the timed
region. Samples are TSC-calibrated to ns and sorted for percentiles. This demo *is*
the benchmark — it reports the distribution, not a mean.

## Results

| run | p50 (ns) | p99 (ns) | p99.9 (ns) | max (ns) |
|----:|---------:|---------:|-----------:|---------:|
| 1 | 17.0 | 17.7 | 20.1 | 27,197 |
| 2 | 21.6 | 23.1 | 27.0 | 15,141 |
| **representative** | **~18** | **~20** | **~20–27** | **~15–27 µs** |

## Interpretation

- **The mean would lie.** p50/p99 sit around ~18–23 ns, but the **max is ~1,000×
  larger** (tens of microseconds) — a context switch / interrupt / frequency
  transition. That outlier is the loss-making tail trading actually fears; averaging
  hides it. Same finding, same technique as the C++ demo.
- `rdtscp` + `lfence` gives the resolution to even see an 18 ns operation; a
  syscall-backed clock (`Instant::now()`, tens of ns of overhead) can't.
- **What Rust adds/differs:** `__rdtscp`/`_mm_lfence` are `core::arch::x86_64`
  intrinsics behind `unsafe` + `#[cfg(target_arch = "x86_64")]`, with an
  `Instant`-based fallback elsewhere — the portability split is explicit in the
  `cfg`/types rather than `#ifdef`. `#[inline(never)]` keeps the function under test
  from being optimized away.
- The wide p99.9/max swing across runs is the measurement working: it surfaces system
  jitter. On an isolated, pinned core with turbo/C-states off, the tail tightens.

## Reproduce

```sh
cargo bench                                           # see the 07_timestamp line
cargo run --release --example 07_low_latency_timestamp
```
