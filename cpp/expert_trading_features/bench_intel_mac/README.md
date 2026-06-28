# Bench reports — Intel Mac

Benchmark numbers for the [expert trading demos](../README.md), measured on the
machine specified below. Each demo has its own report here:

| # | Report |
|---|--------|
| 01 | [Fixed-point prices](01_fixed_point_price.md) |
| 02 | [Lock-free SPSC ring buffer](02_spsc_ring_buffer.md) |
| 03 | [False sharing](03_false_sharing.md) |
| 04 | [Object pool / free list](04_object_pool.md) |
| 05 | [Array-indexed order book](05_order_book.md) |
| 06 | [Branch hints / branchless / prefetch](06_branch_and_prefetch.md) |
| 07 | [Cycle-accurate timestamps & latency tail](07_low_latency_timestamp.md) |
| 08 | [Static dispatch (CRTP vs virtual)](08_static_dispatch_crtp.md) |

> Results are **machine-specific**. This folder is named for its box
> (`bench_intel_mac`); numbers from a different CPU/OS/compiler belong in a sibling
> folder (e.g. `bench_<arch>_<os>`) with its own copy of this spec.

## Machine spec

| | |
|---|---|
| **Model** | MacBook Pro (15-inch, 2019) |
| **CPU** | Intel Core i7-9750H @ 2.60 GHz (Coffee Lake-H), 6 cores / 12 threads, turbo to ~4.5 GHz |
| **Caches** | L2 256 KB/core · L3 12 MB shared |
| **RAM** | 16 GB |
| **OS** | macOS 26.5 (build 25F71), Darwin 25.5.0, x86_64 |
| **Compiler** | Apple clang 21.0.0 (clang-2100.1.1.101), libc++ |
| **Build flags** | `-std=c++20 -O2 -Wall -Wextra -pthread` |
| **TSC** | invariant, ~2.59 ticks/ns (used by demo 07) |

## Measurement conditions & caveats

- **Laptop, not a tuned server.** Turbo and frequency scaling were **left on**,
  Hyper-Threading enabled, and threads were **not pinned** to cores. No `isolcpus`,
  no C-state/turbo disabling.
- Consequently the figures are best read as **illustrative ratios** (this technique vs
  that one) rather than absolute spec numbers. Run-to-run jitter is expected,
  especially in tail latencies (demo 07's `max`) which are dominated by OS scheduling
  and interrupts.
- Each report lists 3 runs plus a representative value, and a one-line reproduce
  command. Re-run on your own box — absolute ns and speedups will differ.

## Reproduce all

```sh
cd ..              # the demo directory
make run           # build + run every demo (binaries -> ./bin, git-ignored)
```
