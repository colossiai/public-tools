# Bench report — 14 Async executor

Source: [`../examples/14_async_executor.rs`](../examples/14_async_executor.rs) ·
Harness: [`../benches/bench_all.rs`](../benches/bench_all.rs) (`bench_14_async`) ·
Machine: see [README](README.md).

## What is measured

The per-`await` overhead of the hand-built, zero-dependency executor. We `block_on`
an `async` block that awaits a self-waking `Yield` future 2,000,000 times. Each
yield is a full round-trip: `poll` → return `Pending` → `wake_by_ref` → re-`poll` →
`Ready`. Best of 7, reported as ns per yield.

## Results

| run | total (ms) | ns per poll/await round-trip |
|----:|-----------:|-----------------------------:|
| 1 | 42.06 | 21.0 |
| 2 | 41.86 | 20.9 |
| **representative** | **~42** | **~21** |

## Interpretation

- **~21 ns per await round-trip** for the whole machinery: the compiler-generated
  state machine resuming, the `Waker` vtable's `wake_by_ref`, and the re-poll. In
  this microbench the future wakes *itself* immediately, so `block_on` never actually
  parks the thread — it just re-polls, which is the cheapest possible path and a fair
  measure of the per-suspension bookkeeping.
- That ~21 ns is the floor; a real workload's await cost is dominated by whatever
  it's waiting on (IO, a timer, another task), not this bookkeeping.
- The takeaway is conceptual: `async`/`.await` compiles to a `poll`-driven state
  machine, and an "executor" is just a loop that polls and parks. A production
  runtime (tokio/async-std) adds a multi-task scheduler, timers, and IO reactors on
  top of exactly this loop — there is no hidden magic, and no runtime unless you add
  one.

## Reproduce

```sh
cargo bench                                    # see the 14_async line
cargo run --example 14_async_executor          # the demo itself (counts polls)
```
