# Bench report — 12 Unsafe & FFI

Source: [`../examples/12_unsafe_and_ffi.rs`](../examples/12_unsafe_and_ffi.rs) ·
Harness: [`../benches/bench_all.rs`](../benches/bench_all.rs) (`bench_12_unsafe`) ·
Machine: see [README](README.md).

## What is measured

A representative win from dropping into `unsafe`: skipping redundant
zero-initialization. We build a 4096-element `Vec<u64>` and fill every slot,
200,000 times, two ways:

- **safe baseline** — `vec![0u64; LEN]` (allocates **and zeroes**), then overwrite
  every element. The zeroing is wasted work since we write all of it.
- **`MaybeUninit`** — allocate uninitialized capacity, `set_len`, then write every
  slot exactly once (no zeroing pass).

Best of 7.

## Results

| run | zero-init + write (ms) | `MaybeUninit` (ms) | ratio |
|----:|-----------------------:|-------------------:|------:|
| 1 | 187.70 | 142.49 | 1.32× |
| 2 | 190.65 | 144.67 | 1.32× |
| **representative** | **~189** | **~143** | **~1.32×** |

## Interpretation

- Skipping the redundant zeroing is **~1.3× faster** for this write-everything
  pattern — the memory only gets touched once instead of twice. This is the kind of
  hot-path win `unsafe` unlocks when you can prove you'll initialize every byte.
- The cost is responsibility: reading a `MaybeUninit` slot before writing it is
  **undefined behavior**. The discipline (and what the demo shows) is to keep the
  `unsafe` block tiny, document the invariant (`// SAFETY: every element written`),
  and expose a safe API — exactly how `Vec`/`split_at_mut` are built in `std`.
- `unsafe` does **not** turn off the borrow checker; it only unlocks five extra
  powers (raw-pointer deref, FFI calls, etc.). The demo also calls libc `abs` via
  `extern "C"` and lays out a `#[repr(C)]` struct for FFI.

## Reproduce

```sh
cargo bench   # see the 12_unsafe line
```
