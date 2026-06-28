# Bench report — 02 Lock-free SPSC ring buffer

Source: [`../02_spsc_ring_buffer.cpp`](../02_spsc_ring_buffer.cpp) ·
Technique: single-producer/single-consumer lock-free queue, acquire/release atomics,
cache-line-separated head/tail, cached opposite index.

## Environment

| | |
|---|---|
| CPU | Intel Core i7-9750H @ 2.60 GHz (Coffee Lake, 6C/12T, turbo to ~4.5 GHz) |
| OS / arch | macOS (Darwin 25.5), x86_64 |
| Compiler | Apple clang 21.0.0, libc++ |
| Flags | `-std=c++20 -O2 -Wall -Wextra -pthread` |

> Laptop, turbo + frequency scaling left on, threads not pinned. Numbers are
> *illustrative*, not absolute spec figures.

## What is measured

Two threads: a producer pushes `N = 5,000,000` `Tick`s (24 B each), a consumer pops
them all. We wall-clock the whole hand-off (thread spawn → both joined) and report:

- **ns/tick** — amortized producer + consumer cost per message.
- **M ticks/s** — steady-state throughput.

This is **steady-state throughput**, not isolated op latency: on full/empty the threads
`std::this_thread::yield()`, and the timing includes thread startup. A `checksum` of all
prices is printed to prove every tick crossed correctly.

## Results (3 runs)

| run | ns/tick | M ticks/s | wall (ms) |
|----:|--------:|----------:|----------:|
| 1 | 3.99 | 250.9 | 19.9 |
| 2 | 3.88 | 257.7 | 19.4 |
| 3 | 3.56 | 281.1 | 17.8 |
| **representative** | **~3.8** | **~260** | **~19** |

## Interpretation

- ~3.8 ns/tick ≈ **a few hundred million ticks/sec** on one producer/consumer pair,
  with **no locks and no allocation** — the queue's storage is `static` and fixed.
- The design choices that make this fast: only two atomics (no CAS loop), `acquire`/
  `release` (not `seq_cst`), head and tail on **separate cache lines** (no false
  sharing — see [report 03](03_false_sharing.md)), power-of-two mask instead of
  modulo, and each side caching the other's index to avoid hammering a shared atomic.
- This number includes yield-based backoff and thread startup; a pinned, busy-poll
  benchmark on isolated cores would report a lower and far more stable per-op cost.
  For production you also care about the **latency tail** of a single push/pop, which
  this throughput figure hides.

## Reproduce

```sh
make bin/02_spsc_ring_buffer && bin/02_spsc_ring_buffer
```
