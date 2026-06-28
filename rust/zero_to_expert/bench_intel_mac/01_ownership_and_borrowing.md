# Bench report — 01 Ownership & borrowing

Source: [`../examples/01_ownership_and_borrowing.rs`](../examples/01_ownership_and_borrowing.rs) ·
Harness: [`../benches/bench_all.rs`](../benches/bench_all.rs) (`bench_01_ownership`) ·
Machine: see [README](README.md) (Intel i7-9750H, rustc 1.96, `cargo bench`).

## What is measured

The cost a **move** avoids. A move transfers ownership of a heap buffer by copying
only the `Vec` header (ptr/len/cap) — the heap data is never touched. A `.clone()`
must allocate a new buffer and `memcpy` the bytes. We time both over an 8 KiB
`Vec<u64>` (1024 elements), 2000 ops per trial, best of 7.

## Results

| run | clone 8 KiB (ns/op) | move (ns/op) |
|----:|--------------------:|-------------:|
| 1 | 125.9 | 0.08 |
| 2 | 153.9 | 0.10 |
| **representative** | **~140** | **~0.1** |

## Interpretation

- A move is **effectively free** (~0.1 ns — it's just a register/stack shuffle the
  optimizer mostly elides). A clone of the same buffer is ~**140 ns** because it
  allocates and copies 8 KiB.
- This is why Rust moves by default and makes you write `.clone()` explicitly: the
  expensive operation is never silent. "Pass by value" in Rust does not mean "deep
  copy" — it means "transfer ownership", which is cheap.
- The borrow checker lets you avoid even the move when you only need temporary
  access: a `&T`/`&mut T` borrow is also just a pointer, with no ownership transfer.

## Reproduce

```sh
cargo bench   # see the 01_ownership line
```
