# Bench report — 11 Atomics & Send/Sync

Source: [`../examples/11_atomics_and_send_sync.rs`](../examples/11_atomics_and_send_sync.rs) ·
Harness: [`../benches/bench_all.rs`](../benches/bench_all.rs) (`bench_11_atomics`) ·
Machine: see [README](README.md).

## What is measured

A shared counter incremented 8,000,000 times total (8 threads × 1,000,000) under
**heavy contention**, two ways:

- **lock-free** — `AtomicU64::fetch_add(1, Relaxed)`.
- **mutex** — `*Mutex<u64>::lock().unwrap() += 1`.

Best of 7. Reported as total ms and ns per increment.

## Results

| run | Atomic (ms) | Atomic ns/op | Mutex (ms) | Mutex ns/op | Mutex / Atomic |
|----:|------------:|-------------:|-----------:|------------:|---------------:|
| 1 | 133.39 | 16.7 | 446.03 | 55.8 | 3.3× |
| 2 | 131.19 | 16.4 | 452.45 | 56.6 | 3.4× |
| **representative** | **~132** | **~16.5** | **~449** | **~56** | **~3.3×** |

## Interpretation

- Under contention the atomic counter is **~3.3× faster** than a mutex. `fetch_add`
  is a single locked read-modify-write instruction; the mutex adds lock/unlock,
  potential syscalls when contended, and serializes threads through a critical
  section. Both numbers are inflated by all 8 threads hammering one cache line
  (coherence traffic) — that's the contention being measured.
- `Relaxed` ordering is correct here because we only need the *final total* to be
  exact, not any ordering relative to other memory. Publishing data alongside a flag
  would need `Acquire`/`Release` (the spinlock in the demo) or `SeqCst`.
- The deeper point is **`Send`/`Sync`**: the compiler only let us share `AtomicU64`
  and `Mutex` across threads because they implement `Sync`. Trying to share an `Rc`
  or a bare `u64` `&mut` across threads is a **compile error**, not a runtime race.

## Reproduce

```sh
cargo bench   # see the 11_atomics line
```
