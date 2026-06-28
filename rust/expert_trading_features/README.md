# Expert trading features in Rust

Low-latency trading techniques as **runnable, self-contained demos** — the companion
to the C++ collection in [`cpp/expert_trading_features`](../../cpp/expert_trading_features).
Demos **01–08 mirror the C++ ones** so you can read them side by side; **09–11 cover
patterns where Rust's type system specifically pays off** in a trading stack. Each
file is heavily commented, prints what it teaches, and carries its own `#[test]`s.

The hook in every header is the same question: **what does Rust change versus the C++
version?** Zero external dependencies — everything is `std` only.

> Teaching demos, not a production trading stack. The point is the technique and
> *why it matters*, with honest notes on when it does and doesn't pay off — and
> benchmarks you can reproduce.

## The demos

| # | File | Technique | What Rust changes | C++ |
|---|------|-----------|-------------------|-----|
| 01 | [`01_fixed_point_price.rs`](examples/01_fixed_point_price.rs) | **Fixed-point price** | `repr(transparent)` newtype: `Px` ≠ `Qty` ≠ `i64`, checked overflow | [✓](../../cpp/expert_trading_features/01_fixed_point_price.cpp) |
| 02 | [`02_spsc_ring_buffer.rs`](examples/02_spsc_ring_buffer.rs) | **Lock-free SPSC ring** | SP/SC contract encoded in types (one `Producer`, one `Consumer`) | [✓](../../cpp/expert_trading_features/02_spsc_ring_buffer.cpp) |
| 03 | [`03_false_sharing.rs`](examples/03_false_sharing.rs) | **False sharing** | `#[repr(align(64))]` as a reusable `CachePadded<T>` | [✓](../../cpp/expert_trading_features/03_false_sharing.cpp) |
| 04 | [`04_object_pool.rs`](examples/04_object_pool.rs) | **Object pool / free list** | typed `Handle` consumed by `release` — no raw-pointer UAF | [✓](../../cpp/expert_trading_features/04_object_pool.cpp) |
| 05 | [`05_order_book.rs`](examples/05_order_book.rs) | **Array-indexed order book** | flat `Vec` grid, bounds-checked in debug, vs `BTreeMap` | [✓](../../cpp/expert_trading_features/05_order_book.cpp) |
| 06 | [`06_branchless_and_prefetch.rs`](examples/06_branchless_and_prefetch.rs) | **Branchless & prefetch** | `core::arch` `_mm_prefetch` + cfg fallback; a reality check | [✓](../../cpp/expert_trading_features/06_branch_and_prefetch.cpp) |
| 07 | [`07_low_latency_timestamp.rs`](examples/07_low_latency_timestamp.rs) | **Cycle-accurate timing** | `rdtscp`/`lfence` via `core::arch` + `cfg`, latency percentiles | [✓](../../cpp/expert_trading_features/07_low_latency_timestamp.cpp) |
| 08 | [`08_static_dispatch.rs`](examples/08_static_dispatch.rs) | **Static dispatch** | `enum` + `match` as the idiomatic CRTP analog; vs `Box<dyn>` | [✓](../../cpp/expert_trading_features/08_static_dispatch_crtp.cpp) |
| 09 | [`09_seqlock.rs`](examples/09_seqlock.rs) | **Seqlock top-of-book** | unsafe protocol behind a safe generic `SeqLock<T>` | — |
| 10 | [`10_order_state_typestate.rs`](examples/10_order_state_typestate.rs) | **Type-state order lifecycle** | illegal transitions are *compile errors*, zero-cost | — |
| 11 | [`11_zero_copy_wire.rs`](examples/11_zero_copy_wire.rs) | **Zero-copy wire decode** | `repr(C)` view, lifetime-tied to the buffer, no alloc | — |

## Running

```sh
cargo run --release --example 02_spsc_ring_buffer   # run one demo (release = real numbers)
cargo test --examples                               # run the embedded tests (29 of them)
cargo bench                                         # micro-benchmarks (see below)
```

Each file's header lists its exact run command. Verified with **Rust 1.96** on
**x86_64 macOS**. The `rdtscp`/prefetch demos (06, 07) use `core::arch::x86_64`
intrinsics behind `#[cfg(target_arch = "x86_64")]`, with portable fallbacks.

## Benchmarks

A std-only harness, [`benches/bench_all.rs`](benches/bench_all.rs), measures every
demo (`cargo bench`). Per-demo **bench reports** with measured numbers, methodology,
and the "what does Rust change?" interpretation live in
[`bench_intel_mac/`](bench_intel_mac/) — run on the **same machine** as the C++
collection's reports, so the two are directly comparable.

The results split into two groups:

- **Real performance levers** (same as C++): false sharing **~6×** (03), object pool
  **~32×** (04), array book vs `BTreeMap` **~110×** (05), seqlock vs mutex read
  **~15×** (09), static vs dynamic dispatch **~2.1×** (08).
- **Safety that costs ~nothing** — where Rust's type system buys correctness for
  free: the fixed-point newtype (01, actually ~1.8× *faster*), the type-state order
  lifecycle **~1.0×** (10), the zero-copy decoder **~1.15×** + zero allocation (11).

## The recurring themes (and how Rust expresses them)

1. **Determinism beats average speed.** Avoid unbounded tails on the hot path:
   no allocation (04 pool, 11 zero-copy), no locks (02 SPSC, 09 seqlock). Measure the
   tail, not the mean (07).
2. **Mechanical sympathy.** Lay data out for the cache: contiguous arrays (05),
   one writer per cache line (03 `CachePadded`, reused by 02).
3. **Push work to compile time.** `const fn` pricing (01), `enum`/generics for static
   dispatch (08), type-state for the order lifecycle (10).
4. **Make illegal states unrepresentable.** Distinct unit types (01 `Px`/`Qty`),
   typed pool handles (04), the type-state machine (10), lifetime-bound views (11) —
   Rust turns "don't do that" comments into compile errors.
5. **Unsafe is a small, audited core behind a safe API.** The SPSC ring (02), object
   pool (04), seqlock (09), and zero-copy decoder (11) all confine `unsafe` to a few
   lines and expose a 100%-safe surface — the way `std` itself is built.
