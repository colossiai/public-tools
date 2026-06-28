# Bench report — 07 Cycle-accurate timestamps & latency tail

Source: [`../07_low_latency_timestamp.cpp`](../07_low_latency_timestamp.cpp) ·
Technique: `rdtscp` + `lfence` for ~ns-resolution timing, TSC calibration, and a
latency histogram to recover **percentiles** — because the tail is what hurts.

## Environment

| | |
|---|---|
| CPU | Intel Core i7-9750H @ 2.60 GHz (Coffee Lake, 6C/12T, turbo to ~4.5 GHz) |
| OS / arch | macOS (Darwin 25.5), x86_64 (TSC available, ~2.59 ticks/ns) |
| Compiler | Apple clang 21.0.0, libc++ |
| Flags | `-std=c++20 -O2 -Wall -Wextra -pthread` |

> Laptop, turbo + frequency scaling left on, threads not pinned. The **max** below is
> dominated by OS scheduling/interrupts — exactly the jitter a real deployment isolates
> away (isolcpus, no turbo/C-states, pinning).

## What is measured

`encode_order()` (a tiny `[[gnu::noinline]]` FNV-style mix — stand-in for an
order-encode step) is timed `N = 200,000` times. Each sample brackets the call with
`rdtscp` + `lfence` so surrounding work can't reorder into the timed region. Samples
are converted to ns via a calibrated ticks/ns and sorted for percentiles.

This demo **is** the benchmark — it reports the latency distribution, not a single mean.

## Results (3 runs)

| run | p50 (ns) | p99 (ns) | p99.9 (ns) | max (ns) |
|----:|---------:|---------:|-----------:|---------:|
| 1 | 18.52 | 20.06 | 62.50 | 27,651 |
| 2 | 19.29 | 20.83 | 23.92 | 13,548 |
| 3 | 16.98 | 17.75 | 17.75 | 16,394 |
| **representative** | **~18** | **~20** | **~20–60** | **~14–28 µs** |

## Interpretation

- **The mean would lie.** p50/p99 sit around ~18–20 ns, but the **max is ~1,000× larger**
  (tens of microseconds). That single outlier — a context switch, interrupt, or
  frequency transition — is the loss-making tail trading actually fears. Averaging it
  away hides the risk.
- `rdtscp`+`lfence` gives the resolution to even *see* an 18 ns operation; a
  syscall-backed clock (tens of ns of overhead, with its own jitter) could not measure
  this reliably.
- The wide swing in **p99.9 and max** across runs is the measurement working as
  intended: it surfaces system jitter. On an isolated, pinned core with turbo/C-states
  disabled the tail tightens dramatically — that hardening is the production lever, and
  this histogram is how you verify it.
- The technique generalizes: measure the **distribution** of any hot-path operation,
  and watch p99.9/max, not the mean.

## Reproduce

```sh
make bin/07_low_latency_timestamp && bin/07_low_latency_timestamp
```
