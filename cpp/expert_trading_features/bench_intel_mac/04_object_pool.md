# Bench report — 04 Object pool / free list

Source: [`../04_object_pool.cpp`](../04_object_pool.cpp) ·
Technique: pre-allocate all objects once, hand them out from an intrusive free list —
zero allocation on the hot path, O(1) acquire/release, deterministic latency.

## Environment

| | |
|---|---|
| CPU | Intel Core i7-9750H @ 2.60 GHz (Coffee Lake, 6C/12T, turbo to ~4.5 GHz) |
| OS / arch | macOS (Darwin 25.5), x86_64 |
| Compiler | Apple clang 21.0.0, libc++ |
| Flags | `-std=c++20 -O2 -Wall -Wextra -pthread` |

> Laptop, turbo + frequency scaling left on, threads not pinned. Numbers are
> *illustrative*. `malloc` behavior in particular varies a lot by allocator/OS.

## What is measured

The hot-path pattern **acquire → touch → release**, `N = 20,000,000` iterations,
run two ways:

- **object pool** — `bp.acquire(...)` (placement-new into a recycled slot) / `bp.release(o)`.
- **new/delete** — `new Order{...}` / `delete o`.

Each iteration touches the object (`sink += id ^ price`, printed at the end).

> **Measurement note.** Without an escape barrier, clang proves the `new`/`delete`
> pair is dead and removes the allocation entirely (heap-allocation elision), making
> the heap path look *instant* and the comparison a lie. The benchmark forces the
> pointer to escape each iteration —
> `asm volatile("" : : "g"(p) : "memory")` — so the allocator actually runs.

## Results (3 runs)

| run | object pool ns/op | new/delete ns/op | speedup |
|----:|------------------:|-----------------:|--------:|
| 1 | 3.046 | 47.252 | 15.51× |
| 2 | 2.888 | 45.919 | 15.90× |
| 3 | 2.609 | 44.060 | 16.89× |
| **representative** | **~2.8** | **~46** | **~16×** |

## Interpretation

- The pool is ~16× faster on the **mean** — but the bigger story for trading is the
  **tail**. `new`/`delete` can take a lock, hit allocator-arena contention, or fault
  a page; those produce rare multi-microsecond spikes. The pool is the same handful
  of instructions every time → **bounded latency**.
- The pool's win also comes from locality: recycled slots are contiguous and stay hot
  in cache, vs. `malloc` returning scattered addresses.
- Caveat: this is a single-threaded loop with a recycling-friendly allocator; absolute
  `new`/`delete` cost varies widely across allocators (libc++/system malloc here),
  threads, and fragmentation — another reason to not depend on it on the hot path.

## Reproduce

```sh
make bin/04_object_pool && bin/04_object_pool
```
