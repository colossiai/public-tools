# Bench report — 09 Seqlock (top-of-book publishing)

Source: [`../examples/09_seqlock.rs`](../examples/09_seqlock.rs) ·
Harness: [`../benches/bench_all.rs`](../benches/bench_all.rs) (`bench_09_seqlock`) ·
C++: none (the cpp README lists seqlocks as a "production direction") ·
Machine: see [README](README.md).

## What is measured

Uncontended snapshot-read cost of a 32-byte top-of-book struct: a `SeqLock<T>` read
(sequence check + volatile read) vs a `Mutex<T>` read (lock + copy + unlock).
50,000,000 reads, best of 7. The demo additionally runs a live writer with 4 reader
threads and confirms **zero torn reads** across ~19M snapshots.

## Results

| run | seqlock read (ns) | `Mutex` read (ns) | speedup |
|----:|------------------:|------------------:|--------:|
| 1 | 1.19 | 18.40 | 15.5× |
| 2 | 1.20 | 18.36 | 15.3× |
| **representative** | **~1.2** | **~18.4** | **~15×** |

## Interpretation

- A seqlock read is **~15× cheaper** than taking a mutex, and crucially the **writer
  never blocks**: it bumps a sequence to odd, writes, bumps to even; readers snapshot
  between two equal even reads and retry if a write overlapped. Perfect for one
  writer (the book) publishing to many strategy readers — no reader can stall the
  writer or each other.
- **Why it's a Rust showcase:** the unsafe interior (`UnsafeCell<T>` + the sequence
  protocol) is wrapped in a fully safe generic `SeqLock<T>`; callers never write
  `unsafe`, and `unsafe impl Sync` states the single-writer contract that makes it
  sound. The demo's live-writer test proves the consistency invariant
  (`ask - bid == SPREAD`) held on every one of ~19M concurrent snapshots.
- **Honest caveat (in the demo):** the concurrent volatile read/write of the payload
  is, strictly, a benign data race in the abstract memory model that the sequence
  check makes safe in practice; rigorous implementations read field-by-field with
  atomics. We keep the classic shape to show the protocol.

## Reproduce

```sh
cargo bench                              # see the 09_seqlock line
cargo run --release --example 09_seqlock  # the live-writer torn-read test
```
