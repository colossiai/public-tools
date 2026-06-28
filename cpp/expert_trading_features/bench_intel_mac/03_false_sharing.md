# Bench report — 03 False sharing

Source: [`../03_false_sharing.cpp`](../03_false_sharing.cpp) ·
Technique: put each hot, independently-written counter on its own cache line with
`alignas(64)` to stop MESI line ping-pong between cores.

## Environment

| | |
|---|---|
| CPU | Intel Core i7-9750H @ 2.60 GHz (Coffee Lake, 6C/12T, turbo to ~4.5 GHz) |
| OS / arch | macOS (Darwin 25.5), x86_64 |
| Compiler | Apple clang 21.0.0, libc++ |
| Flags | `-std=c++20 -O2 -Wall -Wextra -pthread` |

> Laptop, turbo + frequency scaling left on, threads not pinned. The *ratio* is the
> robust signal here; absolutes jitter with scheduling.

## What is measured

Two threads each `fetch_add` their own atomic counter `kIters = 100,000,000` times,
in two layouts:

- **packed** — `a` and `b` adjacent in a struct → almost certainly the **same** 64 B line.
- **padded** — each counter `alignas(64)` → its **own** line.

Wall-clock per layout, reported as ns/op (divided by `2 × kIters`, both threads).

## Results (3 runs)

| run | packed ns/op | padded ns/op | speedup |
|----:|-------------:|-------------:|--------:|
| 1 | 15.27 | 2.37 | 6.43× |
| 2 | 13.88 | 2.30 | 6.03× |
| 3 | 14.87 | 2.29 | 6.48× |
| **representative** | **~14.7** | **~2.3** | **~6.3×** |

`sizeof(Packed) = 16`, `sizeof(Padded) = 128`.

## Interpretation

- The two threads write **different** variables, so this *should* be embarrassingly
  parallel. In the packed layout they share a cache line, so every increment by one
  core invalidates the other core's copy — the line ping-pongs over the coherence
  fabric and throughput collapses (~6× slower here).
- The fix costs only memory: `alignas(64)` (here 16 B → 128 B) buys ~6× throughput.
- This is the exact reason the SPSC ring ([report 02](02_spsc_ring_buffer.md)) puts
  head and tail on separate lines. The same trap hits per-thread stats, per-symbol
  sequence numbers, and any shared-struct hot counter.
- On a machine with more cores or a costlier inter-core path, the packed penalty is
  typically larger.

## Reproduce

```sh
make bin/03_false_sharing && bin/03_false_sharing
```
