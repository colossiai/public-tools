# Bench report — 02 Structs, enums & pattern matching

Source: [`../examples/02_structs_enums_matching.rs`](../examples/02_structs_enums_matching.rs) ·
Harness: [`../benches/bench_all.rs`](../benches/bench_all.rs) (`bench_02_match`) ·
Machine: see [README](README.md).

## What is measured

The per-element cost of dispatching on an `enum` via `match`. We build 4,000,000
values of a 4-variant enum and run a `match` that does a small arithmetic op per
variant, reporting ns per match (best of 7).

> This demo is about **modeling data so illegal states don't compile**, not about
> speed — but it's worth confirming that the safety has no runtime price.

## Results

| run | enum match dispatch (ns/op) |
|----:|----------------------------:|
| 1 | 1.106 |
| 2 | 1.181 |
| **representative** | **~1.15** |

## Interpretation

- ~1.1 ns/op: a `match` on an enum compiles to a **branch or jump table** on the
  discriminant — the same machine code you'd get from a hand-written `switch` in C.
  There is no vtable, no allocation, no boxing.
- Exhaustiveness (the compiler forcing you to handle every variant) and payload
  destructuring are **compile-time** features: they cost nothing at runtime.
- Contrast with demo 06: dispatching over an *open* set of types (`dyn Trait`) costs
  a vtable indirection. A closed set of variants (`enum` + `match`) does not.

## Reproduce

```sh
cargo bench   # see the 02_match line
```
