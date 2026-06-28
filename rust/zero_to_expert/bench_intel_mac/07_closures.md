# Bench report — 07 Closures

Source: [`../examples/07_closures.rs`](../examples/07_closures.rs) ·
Harness: [`../benches/bench_all.rs`](../benches/bench_all.rs) (`bench_07_closures`) ·
Machine: see [README](README.md).

## What is measured

The same closure (`|x| x * k + 1`) applied across 20,000,000 `i64`s two ways:

- **generic `Fn`** — `apply_generic<F: Fn(i64)->i64>(F, …)`: monomorphized, inlines.
- **`Box<dyn Fn>`** — `apply_boxed(&dyn Fn(i64)->i64, …)`: indirect call via vtable.

Best of 7.

## Results

| run | generic `Fn` (ms) | `Box<dyn Fn>` (ms) | boxed / generic |
|----:|------------------:|-------------------:|----------------:|
| 1 | 20.56 | 47.70 | 2.32× |
| 2 | 16.95 | 34.40 | 2.03× |
| **representative** | **~18.7** | **~41** | **~2.1×** |

## Interpretation

- Boxing a closure behind `dyn Fn` costs **~2.1×** — the same story as demo 06: an
  indirect call that can't inline, wrapped around a tiny body. The generic version
  inlines the closure straight into the loop.
- Use a generic `F: Fn(..)` bound (or `impl Fn(..)`) when you can — it's free.
  Use `Box<dyn Fn>` when you need to **store** closures of different types together
  (a `Vec<Box<dyn Fn>>`), return one without naming its type from many branches, or
  break a recursive type — and accept the indirection there.
- A boxed closure also costs a heap allocation to create (not in this hot-loop
  measurement, which reuses one box).

## Reproduce

```sh
cargo bench   # see the 07_closures line
```
