# Bench report — 13 Declarative macros

Source: [`../examples/13_macros.rs`](../examples/13_macros.rs) ·
Harness: [`../benches/bench_all.rs`](../benches/bench_all.rs) (`bench_13_macros`) ·
Machine: see [README](README.md).

## What is measured

Whether a `macro_rules!` invocation adds any *runtime* cost over writing the same
code by hand. We build 2,000,000 small `Vec`s via the demo's `myvec![a, b, c, d]`
macro vs the **exact code it expands to** (`let mut v = Vec::new(); v.push(..); …`).
Best of 7.

> **Why not compare to `vec![]`?** Std's `vec!` preallocates exact capacity, so it
> beats a naive push-loop — but that's a *different implementation*, not a
> macro-vs-no-macro difference. To measure the macro itself, the baseline must be
> the code the macro expands into. (An earlier version compared to `vec!` and
> misleadingly showed 47×.)

## Results

| run | `myvec!` (ms) | hand-written expansion (ms) | ratio |
|----:|--------------:|----------------------------:|------:|
| 1 | 100.62 | 100.58 | 1.00× |
| 2 | 96.65 | 98.34 | 0.98× |
| **representative** | **~98** | **~99** | **~1.0×** |

## Interpretation

- **~1.0× — identical.** A declarative macro is expanded into ordinary tokens
  *before* type-checking and codegen, so the generated program is exactly what you'd
  have typed. There is no runtime macro machinery, no indirection, nothing to
  measure. Macros are a **compile-time** tool (cost: compile time and, if abused,
  readability).
- Macros earn their keep by doing what functions can't: variadic/mixed-type
  arguments, generating items (the demo stamps out `struct Price(i64)` etc.), and
  capturing syntax — all resolved at compile time.
- Corollary: if your macro's expansion is slow (e.g. a push-loop without
  preallocation), *that code* is slow — fix the expansion, not "the macro".

## Reproduce

```sh
cargo bench   # see the 13_macros line
```
