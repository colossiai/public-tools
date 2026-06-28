# Bench reports — Intel Mac

Benchmark numbers for the [zero_to_expert demos](../README.md), measured on the
machine specified below. The numbers come from one std-only harness,
[`../benches/bench_all.rs`](../benches/bench_all.rs), run with `cargo bench`.
Each demo has its own report here:

| # | Report | Headline |
|---|--------|----------|
| 01 | [Ownership & borrowing](01_ownership_and_borrowing.md) | clone 8 KiB ≈ **140 ns**, move ≈ **0.1 ns** |
| 02 | [Structs, enums, match](02_structs_enums_matching.md) | enum match ≈ **1.1 ns/op** (jump, ~free) |
| 03 | [Error handling](03_error_handling.md) | `Result`+`?` vs bare: **~1.03×** (free Ok path) |
| 04 | [Collections & iterators](04_collections_and_iterators.md) | iterator chain vs loop: **~1.1×** |
| 05 | [Generics & traits](05_generics_and_traits.md) | generic vs specialized: **~1.0×** (monomorphized) |
| 06 | [Static vs dynamic dispatch](06_trait_objects_and_dispatch.md) | `dyn` vs generic: **~2.2× slower** |
| 07 | [Closures](07_closures.md) | `Box<dyn Fn>` vs generic `Fn`: **~2.1× slower** |
| 08 | [Lifetimes](08_lifetimes.md) | owned `String` vs borrowed `&str`: **~3.7× slower** |
| 09 | [Smart pointers](09_smart_pointers.md) | `Rc::clone` ≈ **2.8 ns** vs deep clone ≈ **72 ns** |
| 10 | [Concurrency](10_concurrency.md) | 4-thread sum speedup **~1.6×** (bandwidth-bound) |
| 11 | [Atomics & Send/Sync](11_atomics_and_send_sync.md) | atomic vs `Mutex` under contention: **~3.3×** |
| 12 | [Unsafe & FFI](12_unsafe_and_ffi.md) | `MaybeUninit` vs zero-then-write: **~1.3×** |
| 13 | [Macros](13_macros.md) | macro vs hand-written: **~1.0×** (compile-time) |
| 14 | [Async executor](14_async_executor.md) | hand-built executor ≈ **21 ns / await** |
| 15 | [Type-state & zero-cost](15_typestate_and_zerocost.md) | newtype vs raw `i64`: **~1.0×** |

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
| **Toolchain** | rustc / cargo 1.96.0 (stable), LLVM backend |
| **Build** | `cargo bench` → release, `opt-level = 3`, no external crates |

## Methodology

- One harness, [`benches/bench_all.rs`](../benches/bench_all.rs), one section per demo.
- **Best of 7 trials** per measurement: the minimum filters out scheduler and
  frequency-scaling jitter (we want the floor, not the average of a noisy laptop).
- **`std::hint::black_box`** wraps inputs and outputs so the optimizer can't hoist
  work out of the timed loop or constant-fold the answer — the classic way a
  micro-benchmark accidentally measures *nothing*.
- Comparisons are **like-for-like**: the abstraction (iterator, generic, `Result`,
  macro, newtype) is timed against the hand-written baseline that produces the
  *same* work, so a ratio of ~1.0 genuinely means "the abstraction is free" rather
  than "I compared two different algorithms".

## How to read these

Many of these demos teach **correctness / type-system** features, not performance
techniques. For those the honest, expected result is a ratio of **~1.0× — i.e. the
abstraction compiles away** (demos 03, 04, 05, 13, 15). That ~1.0 is the finding,
and it's why Rust can offer the safety without asking you to pay for it.

The genuine performance *trade-offs* show up where you'd expect: indirection that
can't inline (06 `dyn`, 07 boxed closures), allocation (08 owned strings, 01 clone,
09 deep clone), and lock contention (11 mutex vs atomic).

## Caveats

- **Laptop, not a tuned server.** Turbo and frequency scaling left on,
  Hyper-Threading enabled, threads not pinned. Read these as **illustrative ratios**,
  not absolute spec numbers. Run-to-run variation of ±10% on the near-1.0 ratios is
  expected (you'll see ratios land anywhere in ~0.95–1.11× across runs).
- The bandwidth-bound demos (10 parallel sum) don't scale linearly with cores —
  summing a 50M-element array saturates memory bandwidth long before 8 cores, so the
  speedup plateaus. That's a real lesson, not a measurement artifact.

## Reproduce

```sh
cd ..            # the crate root
cargo bench      # runs benches/bench_all.rs, prints one line per demo
```
