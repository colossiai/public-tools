# Bench report — 01 Fixed-point prices

Source: [`../01_fixed_point_price.cpp`](../01_fixed_point_price.cpp) ·
Technique: store prices as scaled integers (integer tick grid), never `double`.

## Environment

| | |
|---|---|
| CPU | Intel Core i7-9750H @ 2.60 GHz (Coffee Lake, 6C/12T, turbo to ~4.5 GHz) |
| OS / arch | macOS (Darwin 25.5), x86_64 |
| Compiler | Apple clang 21.0.0, libc++ |
| Flags | `-std=c++20 -O2 -Wall -Wextra -pthread` |

> Laptop, turbo + frequency scaling left on, threads not pinned. Numbers are
> *illustrative ratios*, not absolute spec figures. Expect run-to-run jitter.

## What is measured

A tight **add + compare** loop, `N = 100,000,000` iterations, run two ways over an
accumulator dependency chain:

- **fixed-point** — `Price` (`int64` scaled by 10,000): `acc = acc + step; if (acc >= step) ++hits;`
- **double** — the same with `double` and `0.0001`.

Each iteration depends on the previous (`acc` chains), so the loop is **latency-bound**:
it exposes the per-op latency of the arithmetic, not its throughput. `hits` and the
final `acc` are printed so the loop can't be optimized away.

## Results (3 runs)

| run | fixed-point ns/op | double ns/op | ratio (double / fp) |
|----:|------------------:|-------------:|--------------------:|
| 1 | 0.251 | 1.341 | 5.34× |
| 2 | 0.245 | 1.192 | 4.87× |
| 3 | 0.242 | 1.079 | 4.45× |
| **representative** | **~0.25** | **~1.2** | **~4.9×** |

## Interpretation

- **The headline reason for fixed-point is correctness, not speed.** The demo also
  shows `0.1 + 0.2 != 0.3` in `double` but exact in fixed-point.
- The ~5× gap here is real but specific to this **latency-bound dependent chain**:
  an integer add is ~1-cycle latency, a `double` add is ~3-4 cycles. Chaining the
  accumulator serializes those latencies, so the integer path pulls ahead. In a
  *throughput*-bound loop (independent ops, vectorizable) the gap would shrink.
- Takeaway: integer-tick prices give you **exactness, exact equality/ordering, and
  deterministic latency at no throughput cost** — and often a latency win on
  dependent arithmetic. There is no speed argument for `double` prices.

## Reproduce

```sh
make bin/01_fixed_point_price && bin/01_fixed_point_price
```
