# Bench report — 05 Generics & traits

Source: [`../examples/05_generics_and_traits.rs`](../examples/05_generics_and_traits.rs) ·
Harness: [`../benches/bench_all.rs`](../benches/bench_all.rs) (`bench_05_generics`) ·
Machine: see [README](README.md).

## What is measured

A generic function `sum_generic<T: Add + Copy + Default>(&[T])` vs a hand-written
`sum_i64(&[i64])`, both summing 20,000,000 `i64`s. Best of 7. This checks whether
the generic abstraction costs anything once instantiated at `T = i64`.

## Results

| run | generic (ms) | specialized (ms) | ratio |
|----:|-------------:|-----------------:|------:|
| 1 | 9.49 | 9.68 | 0.98× |
| 2 | 9.92 | 9.52 | 1.04× |
| **representative** | **~9.7** | **~9.6** | **~1.0×** |

## Interpretation

- **~1.0×** — the generic and the specialized function are the *same machine code*.
  Rust **monomorphizes**: for each concrete `T` actually used, the compiler stamps
  out a dedicated copy and optimizes it exactly as if you'd written it by hand. The
  trait bound (`T: Add`) is resolved at compile time — no runtime lookup.
- This is "static dispatch", and it's the default. The cost is **compile time and
  code size** (one copy per type), not runtime speed.
- The trade-off appears in demo 06: when you erase the type behind `dyn Trait`
  instead, you get one shared copy of the code at the price of a vtable call that
  can't inline (~2.2× here).

## Reproduce

```sh
cargo bench   # see the 05_generics line
```
