# Bench report — 10 Type-state order lifecycle

Source: [`../examples/10_order_state_typestate.rs`](../examples/10_order_state_typestate.rs) ·
Harness: [`../benches/bench_all.rs`](../benches/bench_all.rs) (`bench_10_typestate`) ·
C++: none (a place Rust's type system specifically shines) ·
Machine: see [README](README.md).

## What is measured

The same order lifecycle — submit → ack → fill — run 50,000,000 times two ways: a
**runtime-tagged FSM** (a `state` enum field, asserted on each transition) vs the
**type-state** version (state lives in the type; transitions are moves; no tag, no
runtime check). Identical arithmetic in both. Best of 7.

## Results

| run | runtime-tagged FSM (ms) | type-state (ms) | ratio |
|----:|------------------------:|----------------:|------:|
| 1 | 48.18 | 48.22 | 1.00× |
| 2 | 48.38 | 48.58 | 1.00× |
| **representative** | **~48.3** | **~48.4** | **~1.00×** |

## Interpretation

- **~1.0× — the safety is free.** Encoding the order's state in its type
  (`Order<PendingNew>`, `Order<Live>`, `Order<Filled>`) means an illegal transition —
  filling a cancelled order, cancelling one the exchange hasn't acked — is a
  **compile error**, not a runtime assert you hope your tests hit. And it costs
  nothing at runtime: the `PhantomData` state marker is zero-sized
  (`size_of::<Order<Live>>() == 24`, same as the raw fields), and the transitions are
  moves the optimizer elides.
- The runtime FSM here is actually doing slightly *more* work (carrying a tag,
  asserting it); the two land within noise. The point isn't a speed win — it's that
  you get a stronger guarantee for the same cost.
- **Why it's a Rust showcase:** this type-state pattern has no real C++ analog that's
  this ergonomic. The compiler refuses to even build code that calls a method in the
  wrong state, so a whole class of order-management bugs becomes unrepresentable.

## Reproduce

```sh
cargo bench                                            # see the 10_typestate line
cargo run --release --example 10_order_state_typestate
```
