# Bench report — 03 Error handling

Source: [`../examples/03_error_handling.rs`](../examples/03_error_handling.rs) ·
Harness: [`../benches/bench_all.rs`](../benches/bench_all.rs) (`bench_03_errors`) ·
Machine: see [README](README.md).

## What is measured

Whether the `Result` / `?` machinery costs anything on the success path. Two loops
over 20,000,000 `i64`s, **identical structure and arithmetic**, differing only in
whether the per-element step returns `Result<i64, ()>` (unwrapped with `?`) or a
bare `i64`. The step has no validation branch, so this isolates the `Result`/`?`
overhead itself.

> **Why the careful setup:** an earlier version compared the `?` loop against an
> iterator `.map().sum()`, which auto-vectorizes — that measured vectorization, not
> `Result`, and falsely showed 1.5×. Like-for-like loops give the honest answer.

## Results

| run | Result + `?` (ms) | bare i64 (ms) | ratio |
|----:|------------------:|--------------:|------:|
| 1 | 10.14 | 9.88 | 1.03× |
| 2 | 10.97 | 10.53 | 1.04× |
| **representative** | **~10.5** | **~10.2** | **~1.03×** |

## Interpretation

- **~1.03× — within noise.** On the `Ok` path, `Result<T, E>` is just a tagged value
  in a register/stack slot, and `?` is a predicted branch on the tag. There is no
  unwinding, no allocation, no hidden cost — unlike exceptions in other languages.
- You pay only when an error *actually* occurs (you construct and propagate an `E`),
  which is the rare path. The common path is free.
- This is what makes "errors are values, checked by the type system" practical: you
  get compile-time guarantees that errors are handled, at no steady-state cost.

## Reproduce

```sh
cargo bench   # see the 03_error_handling line
```
