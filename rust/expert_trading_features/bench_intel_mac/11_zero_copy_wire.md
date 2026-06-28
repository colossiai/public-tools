# Bench report — 11 Zero-copy wire decoding

Source: [`../examples/11_zero_copy_wire.rs`](../examples/11_zero_copy_wire.rs) ·
Harness: [`../benches/bench_all.rs`](../benches/bench_all.rs) (`bench_11_zero_copy`) ·
C++: none (the cpp README lists custom zero-copy serialization as a "production direction") ·
Machine: see [README](README.md).

## What is measured

Decoding a buffer of 2,000,000 fixed-layout 22-byte "add order" messages laid
end-to-end, summing notional (`price * qty`), two ways: a **zero-copy view** (overlay
`&AddOrder` on the bytes, read fields in place) vs an **owned-copy parse** (decode
each message into an owned struct first). Best of 7.

## Results

| run | view (ms) | owned-copy (ms) | ratio |
|----:|----------:|----------------:|------:|
| 1 | 3.16 | 3.77 | 1.19× |
| 2 | 3.41 | 3.86 | 1.13× |
| **representative** | **~3.3** | **~3.8** | **~1.15×** |

## Interpretation

- The zero-copy view is **~1.15× faster** here *and*, more importantly, allocates
  **nothing** — it reads fields directly out of the receive buffer. For small fixed
  records the parse cost is similar; the real win is avoiding per-message struct
  construction/allocation entirely, which matters at feed rates of millions of
  messages/second and for keeping the hot path allocation-free (see demo 04).
- **Why it's a Rust showcase:** the message is `#[repr(C)]` with byte-array fields, so
  `align_of == 1` and a view can be cast from *any* `&[u8]` of the right length with
  only a length check — no alignment hazard. The `unsafe` cast is wrapped behind a
  safe `parse() -> Option<&AddOrder>`, and the returned reference's **lifetime is tied
  to the buffer**: the borrow checker makes it impossible to keep the view past the
  bytes it points into (the demo shows the dangling-view attempt failing to compile).
- Network byte order is handled by `from_be_bytes` accessors — still no copy of the
  record itself.

## Reproduce

```sh
cargo bench                                    # see the 11_zero_copy line
cargo run --release --example 11_zero_copy_wire
```
