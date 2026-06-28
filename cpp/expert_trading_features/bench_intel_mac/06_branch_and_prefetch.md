# Bench report — 06 Branch hints / branchless / prefetch

Source: [`../06_branch_and_prefetch.cpp`](../06_branch_and_prefetch.cpp) ·
Technique: `[[likely]]`/`[[unlikely]]`, mask-based branchless select, and
`__builtin_prefetch` — **with a reality check**.

## Environment

| | |
|---|---|
| CPU | Intel Core i7-9750H @ 2.60 GHz (Coffee Lake, 6C/12T, turbo to ~4.5 GHz) |
| OS / arch | macOS (Darwin 25.5), x86_64 |
| Compiler | Apple clang 21.0.0, libc++ |
| Flags | `-std=c++20 -O2 -Wall -Wextra -pthread` |

> Laptop, turbo + frequency scaling left on, threads not pinned. These deltas are
> **small and noisy** — that is itself the lesson.

## What is measured

A sum over `N = 2^22 ≈ 4M` random values in `[0,100]` (fixed seed), three ways:

- **branchy** — `if (data[i] >= 50) sum += data[i];` — a ~50/50, **unpredictable** branch.
- **branchless** — `mask = -(v >= 50); sum += v & mask;` — no branch to mispredict.
- **prefetched** — sum every element, `__builtin_prefetch` 16 iterations ahead.

Reported as ns/elem. Sums are printed so nothing is optimized away.

## Results (3 runs)

| run | branchy ns/elem | branchless ns/elem | speedup (branchy/branchless) | prefetched ns/elem |
|----:|----------------:|-------------------:|-----------------------------:|-------------------:|
| 1 | 0.344 | 0.407 | 0.85× | 0.790 |
| 2 | 0.357 | 0.344 | 1.04× | 0.691 |
| 3 | 0.407 | 0.389 | 1.05× | 0.729 |
| **representative** | **~0.37** | **~0.38** | **~1.0× (a tie)** | **~0.74 (slower)** |

## Interpretation

This demo is intentionally a **reality check**, and the numbers deliver it:

- **Branchy ≈ branchless.** At `-O2`, clang already compiles the "branchy" loop to a
  branchless `cmov`, so there's nothing left to mispredict — the two tie, and which one
  edges ahead flips run to run. Hand-written branchless tricks often buy **nothing**
  over a modern optimizer; always check the asm and measure before contorting code.
- **Prefetch is *slower* here (~2×).** The array is small and already **hot in L1/L2**,
  so the prefetch instructions are pure overhead with no miss to hide. Software
  prefetch only pays when data is genuinely **cold** and the access is far enough ahead
  to cover the miss latency.
- `[[likely]]`/`[[unlikely]]` still matter for **code layout** (keeping the hot path as
  the fall-through, cold path out of line) even when they don't move this microbench.
- Takeaway: these are situational tools, not free wins. The honest result is "measure,
  don't guess."

## Reproduce

```sh
make bin/06_branch_and_prefetch && bin/06_branch_and_prefetch
```
