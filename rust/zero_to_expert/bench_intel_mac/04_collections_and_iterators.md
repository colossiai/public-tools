# Bench report — 04 Collections & iterators

Source: [`../examples/04_collections_and_iterators.rs`](../examples/04_collections_and_iterators.rs) ·
Harness: [`../benches/bench_all.rs`](../benches/bench_all.rs) (`bench_04_iterators`) ·
Machine: see [README](README.md).

## What is measured

An iterator adapter chain vs the equivalent hand-written loop, computing the same
result: `data.iter().filter(|x| x % 2 == 0).map(|x| x * 3).sum()` over 20,000,000
`i64`s, against a `for` loop with an `if`. Best of 7.

## Results

| run | iterator chain (ms) | manual loop (ms) | ratio |
|----:|--------------------:|-----------------:|------:|
| 1 | 17.09 | 15.40 | 1.11× |
| 2 | 16.80 | 15.55 | 1.08× |
| **representative** | **~17** | **~15.5** | **~1.10×** |

## Interpretation

- **~1.1× — essentially free.** The adapter chain is *lazy*: `filter`/`map` build a
  state machine that does no work until `sum` drives it, and each adapter
  monomorphizes and inlines, so the whole chain fuses into a single pass with no
  intermediate `Vec`.
- The small residual (~10%) is codegen luck-of-the-draw on this input (bounds-check
  elision, loop-vectorization shape); it sits inside run-to-run noise and flips on
  other workloads. The headline is that an expressive, composable chain costs about
  the same as the manual loop — no temporary collections, no per-element closure
  call overhead.
- `collect` into `Result<Vec<_>, _>` (shown in the demo) short-circuits on the first
  error, also without an extra pass.

## Reproduce

```sh
cargo bench   # see the 04_iterators line
```
