# Bench report — 04 Object pool / free list

Source: [`../examples/04_object_pool.rs`](../examples/04_object_pool.rs) ·
Harness: [`../benches/bench_all.rs`](../benches/bench_all.rs) (`bench_04_object_pool`) ·
C++: [`cpp/.../04_object_pool.cpp`](../../../cpp/expert_trading_features/04_object_pool.cpp) ·
Machine: see [README](README.md).

## What is measured

The hot-path pattern **acquire → touch → release**, 20,000,000 iterations, two ways:
the pre-allocated free-list pool vs `Box::new(...)` / `drop`. Both touch the object;
the `Box` is `black_box`-ed so the allocation can't be elided. ns/op, best of 7.

## Results

| run | pool (ns/op) | `Box::new`/drop (ns/op) | speedup |
|----:|-------------:|------------------------:|--------:|
| 1 | 1.36 | 43.58 | 32.0× |
| 2 | 1.36 | 43.17 | 31.8× |
| **representative** | **~1.36** | **~43** | **~32×** |

## Interpretation

- The pool is ~32× faster on the mean — but the bigger story for trading is the
  **tail**: the global allocator can lock, hit arena contention, or fault a page,
  producing rare multi-microsecond spikes. The pool is the same O(1) index flip
  every time → bounded latency. (`Box::new`/drop here exercises the real allocator;
  without the `black_box` LLVM would delete the alloc/free pair entirely.)
- **What Rust adds over the C++ version:** the pool hands out a typed `Handle` (an
  index), not a raw `T*`, and `release(handle)` *consumes* the handle by value — so a
  use-after-free or double-free is far harder to write than with raw pointers. The
  `unsafe` is confined to `get`/`release`; storage is `Vec<MaybeUninit<T>>`.

## Reproduce

```sh
cargo bench   # see the 04_object_pool line
```
