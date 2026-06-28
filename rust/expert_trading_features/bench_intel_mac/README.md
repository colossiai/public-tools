# Bench reports — Intel Mac

Benchmark numbers for the [expert_trading_features demos](../README.md), measured on
the machine below. All numbers come from one std-only harness,
[`../benches/bench_all.rs`](../benches/bench_all.rs), run with `cargo bench`. Each
demo has its own report here:

| # | Report | Headline |
|---|--------|----------|
| 01 | [Fixed-point price](01_fixed_point_price.md) | int vs f64 add/compare: **~1.8×** (exact *and* faster) |
| 02 | [Lock-free SPSC ring](02_spsc_ring_buffer.md) | **~5 ns/tick, ~190M ticks/s** |
| 03 | [False sharing](03_false_sharing.md) | padded vs packed: **~6.4×** |
| 04 | [Object pool](04_object_pool.md) | pool vs `Box::new`/drop: **~32×** |
| 05 | [Array order book](05_order_book.md) | flat array vs `BTreeMap`: **~110×** |
| 06 | [Branchless & prefetch](06_branchless_and_prefetch.md) | branchy vs branchless: **~0.9× (a tie)** |
| 07 | [Cycle-accurate timestamps](07_low_latency_timestamp.md) | encode `p50 ≈ 18 ns`, `max ≈ 15–27 µs` |
| 08 | [Static dispatch](08_static_dispatch.md) | `Box<dyn>` vs enum: **~2.1×** |
| 09 | [Seqlock](09_seqlock.md) | seqlock vs `Mutex` read: **~15×** |
| 10 | [Type-state order lifecycle](10_order_state_typestate.md) | type-state vs runtime FSM: **~1.0×** (free safety) |
| 11 | [Zero-copy wire decode](11_zero_copy_wire.md) | view vs owned-copy parse: **~1.15×** + no alloc |

> Results are **machine-specific**. This folder is named for its box
> (`bench_intel_mac`); numbers from a different CPU/OS/compiler belong in a sibling
> folder (e.g. `bench_<arch>_<os>`). The same box ran the C++ collection's
> [`cpp/.../bench_intel_mac`](../../../cpp/expert_trading_features/bench_intel_mac),
> so the Rust and C++ numbers are directly comparable.

## Machine spec

| | |
|---|---|
| **Model** | MacBook Pro (15-inch, 2019) |
| **CPU** | Intel Core i7-9750H @ 2.60 GHz (Coffee Lake-H), 6 cores / 12 threads, turbo to ~4.5 GHz |
| **Caches** | L2 256 KB/core · L3 12 MB shared |
| **RAM** | 16 GB |
| **OS** | macOS 26.5 (build 25F71), Darwin 25.5.0, x86_64 (TSC ~2.59 GHz) |
| **Toolchain** | rustc / cargo 1.96.0 (stable), LLVM backend |
| **Build** | `cargo bench` → release, `opt-level = 3`, `codegen-units = 1`, no external crates |

## Methodology

- One harness, [`benches/bench_all.rs`](../benches/bench_all.rs), one section per demo.
- **Best of 7 trials** per measurement: the minimum filters scheduler and
  frequency-scaling jitter (we want the floor, not a noisy laptop's average).
- **`std::hint::black_box`** wraps inputs and outputs so the optimizer can't hoist
  work out of the timed loop or constant-fold the answer — and, for the dispatch
  demo, so it can't devirtualize the trait-object call back into a direct one.
- Comparisons are **like-for-like**: the abstraction is timed against the
  hand-written baseline doing the same work, so a ~1.0× ratio genuinely means "free".

## How to read these

The results split into two groups:

- **Real performance levers** — where mechanical sympathy pays off: false sharing
  (03), the object pool (04), the flat order book (05), the seqlock (09), and
  static vs dynamic dispatch (08). These mirror the C++ collection's findings.
- **Safety that costs ~nothing** — the places Rust's type system buys correctness
  for free: the fixed-point newtype (01), the type-state order lifecycle (10), and
  the zero-copy decoder (11). Their ~1.0× (or *faster*) ratio is the point: you get
  compile-time guarantees the C++ versions enforce by convention, at no runtime cost.

## Caveats

- **Laptop, not a tuned server.** Turbo and frequency scaling left on, HT enabled,
  threads not pinned, no `isolcpus`. Read these as **illustrative ratios**, not
  absolute spec numbers. Expect ±10–20% run-to-run, especially on the tail
  latencies (07's `max`) and the threaded demos (02 throughput).
- The seqlock (09) and SPSC ring (02) numbers are single-writer / single-pair; the
  seqlock's `max` tail under a live writer is what a real deployment would harden.

## Reproduce

```sh
cd ..            # the crate root
cargo bench      # runs benches/bench_all.rs, prints one line per demo
```
