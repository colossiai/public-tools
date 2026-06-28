# Bench report — 08 Static dispatch (enum vs `dyn`)

Source: [`../examples/08_static_dispatch.rs`](../examples/08_static_dispatch.rs) ·
Harness: [`../benches/bench_all.rs`](../benches/bench_all.rs) (`bench_08_dispatch`) ·
C++: [`cpp/.../08_static_dispatch_crtp.cpp`](../../../cpp/expert_trading_features/08_static_dispatch_crtp.cpp) ·
Machine: see [README](README.md).

## What is measured

A momentum strategy processes a feed of 20,000,000 ticks, two ways: through a
`Box<dyn Strategy>` (vtable call) vs an `enum Strat` dispatched by `match` (static).
The trait object is built by an `#[inline(never)]` factory with two arms returning
different concrete types, so the compiler **cannot devirtualize** the call. ns/tick,
best of 7.

## Results

| run | `dyn` (ns/tick) | enum (ns/tick) | dyn / enum |
|----:|----------------:|---------------:|-----------:|
| 1 | 2.572 | 1.239 | 2.08× |
| 2 | 2.608 | 1.240 | 2.10× |
| **representative** | **~2.6** | **~1.24** | **~2.1×** |

## Interpretation

- Dynamic dispatch costs **~2.1×** here: a `dyn` call is an indirect jump the CPU
  can't inline across, which also blocks the surrounding loop optimizations. The
  enum's `match` arm inlines straight into the loop.
- **What Rust adds over C++ (CRTP):** C++ reaches for CRTP to get static dispatch;
  Rust's idiomatic equivalent is an `enum` over the closed strategy set + `match` —
  fully known to the compiler, so each arm inlines, *and* you can still hold a
  heterogeneous `Vec<Strat>` that dispatches statically. This mirrors the C++
  CRTP-vs-virtual gap (~1.8–2×).
- **Measurement note:** without the opaque factory, LLVM (especially at
  `codegen-units = 1`) sees the single concrete type and devirtualizes the `dyn`
  call, collapsing the gap to ~1.0× — a misleading result. The two-arm
  `#[inline(never)]` factory + `black_box` is what keeps the comparison honest.

## Reproduce

```sh
cargo bench                                     # see the 08_dispatch line
cargo run --release --example 08_static_dispatch
```
