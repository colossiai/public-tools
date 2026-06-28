# Bench report — 09 Smart pointers

Source: [`../examples/09_smart_pointers.rs`](../examples/09_smart_pointers.rs) ·
Harness: [`../benches/bench_all.rs`](../benches/bench_all.rs) (`bench_09_smart_pointers`) ·
Machine: see [README](README.md).

## What is measured

Three costs that matter when choosing a smart pointer:

- **`Rc::clone`** — bump a reference count (a non-atomic increment), share the same
  allocation. 5,000,000 ops.
- **deep clone** — `Vec::clone` of the same 2 KiB payload (allocate + copy).
- **`RefCell`** runtime borrow check — `borrow_mut()` + `borrow()` per iteration vs a
  direct `&mut` to a plain value.

Best of 7.

## Results

| run | `Rc::clone` (ns) | deep clone 2 KiB (ns) | `RefCell` (ns/iter) | `&mut` (ns/iter) |
|----:|-----------------:|----------------------:|--------------------:|-----------------:|
| 1 | 3.2 | 72.4 | 1.23 | 1.12 |
| 2 | 2.5 | 72.7 | 1.48 | 1.20 |
| **representative** | **~2.8** | **~72** | **~1.35** | **~1.15** |

## Interpretation

- **`Rc::clone` (~2.8 ns) is ~25× cheaper than deep-cloning** the same data: it
  shares the allocation and only increments a counter. That's the whole point of
  `Rc`/`Arc` — cheap shared ownership instead of copying. (`Arc` is the same idea
  with an *atomic* counter for cross-thread use; see demo 11.)
- **`RefCell` borrow checking is nearly free** (~0.2 ns over a raw `&mut`): each
  `borrow*()` is a flag check/update. You move the borrow rule from compile time to
  runtime to get interior mutability, and the runtime cost is a single integer
  compare — the risk is a *panic* on violation, not slowness.
- Rule of thumb: prefer plain ownership/borrows; reach for `Rc<RefCell<T>>` only when
  you genuinely need shared, mutable, single-threaded state (graphs, observer lists).

## Reproduce

```sh
cargo bench   # see the 09_smart_pointers line
```
