# Bench report — 06 Static vs dynamic dispatch

Source: [`../examples/06_trait_objects_and_dispatch.rs`](../examples/06_trait_objects_and_dispatch.rs) ·
Harness: [`../benches/bench_all.rs`](../benches/bench_all.rs) (`bench_06_dispatch`) ·
Machine: see [README](README.md).

## What is measured

The same trait method (`Signal::score`) called over 20,000,000 prices two ways:

- **static** — `eval_static<S: Signal>(&S, …)`: monomorphized, the call inlines.
- **dynamic** — `eval_dyn(&dyn Signal, …)`: the call goes through a vtable.

Best of 7.

## Results

| run | static (ms) | dyn (ms) | dyn / static |
|----:|------------:|---------:|-------------:|
| 1 | 27.54 | 63.02 | 2.29× |
| 2 | 25.70 | 54.91 | 2.14× |
| **representative** | **~26.6** | **~59** | **~2.2×** |

## Interpretation

- Dynamic dispatch is **~2.2× slower here**. `&dyn Signal` is a fat pointer (data +
  vtable); each call is an indirect jump the compiler **can't inline**, which also
  blocks the surrounding loop optimizations (vectorization, keeping state in
  registers). The tiny `score` body makes the indirection's relative cost large.
- Static dispatch (generics) is the default for a reason: it's free. Reach for `dyn`
  when you genuinely need a **heterogeneous collection** (`Vec<Box<dyn Signal>>`) or
  to erase a type across an API boundary — and accept the call cost there.
- The gap shrinks as the method body grows (the indirect-call overhead becomes a
  smaller fraction). This mirrors the C++ CRTP-vs-virtual result in the sibling
  `cpp/` demos.

## Reproduce

```sh
cargo bench   # see the 06_dispatch line
```
