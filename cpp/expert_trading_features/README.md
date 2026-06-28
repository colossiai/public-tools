# Expert C++ for Financial Trading

Runnable demos of the C++ techniques that show up again and again in low-latency
trading systems (market-data handlers, matching engines, execution strategies).
Each file is self-contained, compiles cleanly, and prints — or *measures* — what
it teaches. Several include micro-benchmarks so you see the effect on your box.

> These are teaching demos, not a production trading stack. The point is the
> *technique* and *why it matters*, with honest notes on when it does and doesn't pay off.

## Demos

Every demo now includes a **micro-benchmark** and a matching **bench report** under
[`bench_intel_mac/`](bench_intel_mac/) with numbers measured on the reference box (see
each report for the methodology, caveats, and how to reproduce; see the
[folder README](bench_intel_mac/README.md) for the full machine spec).

| # | File | Technique | Benchmark | Report |
|---|------|-----------|-----------|--------|
| 01 | [`01_fixed_point_price.cpp`](01_fixed_point_price.cpp) | **Fixed-point prices** | integer-tick vs `double` add/compare (~5× on a latency-bound chain) | [report](bench_intel_mac/01_fixed_point_price.md) |
| 02 | [`02_spsc_ring_buffer.cpp`](02_spsc_ring_buffer.cpp) | **Lock-free SPSC queue** | throughput: ns/tick, M ticks/s (~260M/s) | [report](bench_intel_mac/02_spsc_ring_buffer.md) |
| 03 | [`03_false_sharing.cpp`](03_false_sharing.cpp) | **False sharing** | packed vs `alignas(64)` counters (~6× faster padded) | [report](bench_intel_mac/03_false_sharing.md) |
| 04 | [`04_object_pool.cpp`](04_object_pool.cpp) | **Object pool / free list** | pool vs `new`/`delete` acquire/release (~16×) | [report](bench_intel_mac/04_object_pool.md) |
| 05 | [`05_order_book.cpp`](05_order_book.cpp) | **Array-indexed order book** | flat tick array vs `std::map` (~78×) | [report](bench_intel_mac/05_order_book.md) |
| 06 | [`06_branch_and_prefetch.cpp`](06_branch_and_prefetch.cpp) | **Branch hints / branchless / prefetch** | branchy vs branchless vs prefetch (a reality check — ~tie) | [report](bench_intel_mac/06_branch_and_prefetch.md) |
| 07 | [`07_low_latency_timestamp.cpp`](07_low_latency_timestamp.cpp) | **Cycle-accurate timing** | `rdtscp` latency **percentiles** (p50/p99/p99.9/max) | [report](bench_intel_mac/07_low_latency_timestamp.md) |
| 08 | [`08_static_dispatch_crtp.cpp`](08_static_dispatch_crtp.cpp) | **Static dispatch** | CRTP vs `virtual` per-tick callback (~1.8×) | [report](bench_intel_mac/08_static_dispatch_crtp.md) |

> Benchmark numbers in the reports are from an Intel i7-9750H MacBook Pro (Apple clang
> 21, `-O2`, turbo/HT on, threads not pinned). They are **illustrative ratios**, not
> absolute spec figures — re-run on your box. Numbers from a different machine belong
> in a sibling folder (e.g. `bench_<arch>_<os>`).

## Building

```sh
make run                 # build + run all demos (binaries -> ./bin, git-ignored)
make                     # build all
make 03_false_sharing    # build one
make clean
```

Verified with **Apple clang 21 / libc++** on **x86_64** (`-std=c++20 -O2`).
Override the compiler if needed: `make CXX=/opt/homebrew/opt/llvm/bin/clang++`.

### Portability notes
- **x86-only intrinsics**: demo 07 uses `rdtscp`/`lfence` and is guarded by
  `#if defined(__x86_64__)`, falling back to `std::chrono` elsewhere. Demo 06 uses
  `__builtin_prefetch` (portable on clang/gcc).
- Benchmarks are **machine-dependent**. Absolute ns and speedups vary with CPU,
  load, frequency scaling, and what else is running. Pin threads and disable
  turbo/HT for stable numbers in a real evaluation.

## The recurring themes

1. **Determinism beats average speed.** Trading cares about the *tail* (p99.9 /
   max), not the mean. Avoid anything with an unbounded tail on the hot path:
   `malloc`, locks, syscalls, page faults, exceptions, branchy I/O. (Demos 02, 04, 07.)
2. **Mechanical sympathy.** Lay data out for the cache and the coherence protocol:
   contiguous arrays, one writer per cache line, prefetch known strides. (Demos 03, 05, 06.)
3. **Push work to compile time.** `constexpr`, templates/CRTP and closed type sets
   let the compiler inline and specialize the hot path instead of dispatching at
   runtime. (Demos 01, 08.)
4. **Exact integer math for money.** Prices live on an integer tick grid — never a
   binary float. (Demo 01.)
5. **Measure, don't guess.** Modern compilers already do a lot (auto-cmov,
   vectorization); confirm wins with cycle-accurate timing and the generated asm. (Demos 06, 07.)

## Beyond these demos (production directions)
- **Kernel bypass networking** (Solarflare/ef_vi, DPDK, `io_uring`) and busy-poll
  receive — the biggest latency lever is usually getting the packet to userspace.
- **CPU isolation**: `isolcpus`, thread pinning, NUMA-local allocation, disabling
  C-states / turbo for jitter-free cores.
- **Huge pages** to cut TLB misses on large books/pools.
- **Seqlocks** for one-writer/many-reader snapshots (e.g. publishing top-of-book).
- **Custom serialization** (fixed-layout, zero-copy) instead of general frameworks.
