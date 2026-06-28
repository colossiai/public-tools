# Bench report — 06 Branchless & prefetch

Source: [`../examples/06_branchless_and_prefetch.rs`](../examples/06_branchless_and_prefetch.rs) ·
Harness: [`../benches/bench_all.rs`](../benches/bench_all.rs) (`bench_06_branchless`) ·
C++: [`cpp/.../06_branch_and_prefetch.cpp`](../../../cpp/expert_trading_features/06_branch_and_prefetch.cpp) ·
Machine: see [README](README.md).

## What is measured

A sum over 2^22 ≈ 4M pseudo-random values in `[0,100)` (fixed seed), summing only
those ≥ 50, two ways: a data-dependent `if` (branchy) vs a 0/-1 arithmetic mask
(branchless). ns/element, best of 7. (The demo also shows software prefetch.)

## Results

| run | branchy (ns/el) | branchless (ns/el) | ratio (branchy/branchless) |
|----:|----------------:|-------------------:|---------------------------:|
| 1 | 0.333 | 0.381 | 0.87× |
| 2 | 0.412 | 0.437 | 0.94× |
| **representative** | **~0.37** | **~0.41** | **~0.9× (a tie)** |

## Interpretation

- This demo is intentionally a **reality check**, and the numbers deliver it: the
  hand-written branchless version is **no faster** — slightly slower here. At
  `-O3`, LLVM already compiles the "branchy" loop to a branchless `cmov`, so there's
  nothing left to mispredict and the manual bit-twiddling just adds work. Same lesson
  as the C++ demo: measure, don't guess.
- Software prefetch (`_mm_prefetch`, in the demo) is *slower* on this hot array —
  it only pays when data is genuinely cold and the access is far enough ahead.
- **What Rust adds/differs:** prefetch is `core::arch::x86_64::_mm_prefetch` behind
  `unsafe` + `#[cfg(target_arch)]` with a portable no-op fallback; branch-likelihood
  hints (`[[likely]]`) have no stable Rust surface, so you lean on the optimizer and
  `#[cold]`. The branchless-max helper is verified correct against `i32::max` in tests.

## Reproduce

```sh
cargo bench                                          # see the 06_branchless line
cargo run --release --example 06_branchless_and_prefetch
```
