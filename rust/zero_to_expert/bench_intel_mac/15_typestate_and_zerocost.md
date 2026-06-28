# Bench report — 15 Type-state & zero-cost abstractions

Source: [`../examples/15_typestate_and_zerocost.rs`](../examples/15_typestate_and_zerocost.rs) ·
Harness: [`../benches/bench_all.rs`](../benches/bench_all.rs) (`bench_15_zerocost`) ·
Machine: see [README](README.md).

## What is measured

Whether a `#[repr(transparent)]` newtype (`Ticks(i64)`) costs anything over a bare
`i64`. We sum a 50,000,000-element slice of each: `sum_raw(&[i64])` vs
`sum_newtype(&[Ticks])`. Best of 7. (The demo itself runs the same comparison when
built with `--release`.)

## Results

| run | raw `i64` (ms) | newtype `Ticks` (ms) | ratio |
|----:|---------------:|---------------------:|------:|
| 1 | 26.42 | 24.42 | 0.92× |
| 2 | 24.73 | 24.99 | 1.01× |
| **representative** | **~25** | **~25** | **~1.0×** |

## Interpretation

- **~1.0× — the newtype is free.** `#[repr(transparent)]` guarantees `Ticks` has the
  identical layout/ABI to its single `i64` field, and the wrapper is erased by
  codegen. You get a *distinct type* (the compiler won't let you mix `Ticks` with a
  raw `i64` or a `Qty`) at zero runtime cost.
- The same idea powers the **type-state builder** in the demo: `Set`/`Unset` markers
  carried in `PhantomData` make `build()` exist only when both fields are set, so
  misuse is a *compile error* — and `PhantomData` is zero-sized, so the builder is
  just its data fields (16 bytes here), no bigger than an unchecked one.
- This is the thesis of the whole series: Rust pushes correctness into the type
  system, and a good optimizer means you **don't pay for the safety at runtime**.
- Measurement note: the ratio wanders in ~0.92–1.01× across runs (the two sums are
  bandwidth-bound and sit within laptop noise). Best-of-7 + `black_box` keep it
  honest; a single untimed one-shot once misleadingly showed 2× (see the demo's
  comment).

## Reproduce

```sh
cargo bench                                          # see the 15_zerocost line
cargo run --release --example 15_typestate_and_zerocost
```
