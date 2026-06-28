// ============================================================================
// 15 — Type-state & zero-cost abstractions: make misuse a COMPILE error, for free
// Run (optimized):  cargo run --release --example 15_typestate_and_zerocost
// ----------------------------------------------------------------------------
// The expert payoff of Rust's type system: encode a protocol's STATE in the type,
// so calling a method in the wrong state doesn't compile — and pay nothing at
// runtime, because the state markers are zero-sized (`PhantomData`) and erased.
//
// Two ideas combined:
//   * Type-state: a builder/connection that changes TYPE as it transitions, so
//     only the methods valid in the current state exist.
//   * Zero-cost: the safety lives entirely in the types; the generated machine
//     code is identical to the unchecked version. We benchmark to show it.
// ============================================================================

use std::hint::black_box;
use std::marker::PhantomData;
use std::time::Instant;

// --- Type-state builder: you cannot `.build()` until `price` AND `qty` are set --
// The two type params track, at compile time, which required fields are present.
struct Set;
struct Unset;

struct OrderBuilder<P, Q> {
    price: u64,
    qty: u32,
    // PhantomData<T> is zero-sized: it makes the struct "remember" P and Q in the
    // type system without storing anything. sizeof(OrderBuilder) ignores it.
    _state: PhantomData<(P, Q)>,
}

#[derive(Debug, PartialEq)]
struct Order {
    price: u64,
    qty: u32,
}

impl OrderBuilder<Unset, Unset> {
    fn new() -> Self {
        OrderBuilder {
            price: 0,
            qty: 0,
            _state: PhantomData,
        }
    }
}

// `price()` is available in ANY state and returns a builder whose P is now `Set`.
impl<P, Q> OrderBuilder<P, Q> {
    fn price(self, price: u64) -> OrderBuilder<Set, Q> {
        OrderBuilder {
            price,
            qty: self.qty,
            _state: PhantomData,
        }
    }
    fn qty(self, qty: u32) -> OrderBuilder<P, Set> {
        OrderBuilder {
            price: self.price,
            qty,
            _state: PhantomData,
        }
    }
}

// `build()` EXISTS ONLY when both type params are `Set`. Calling it too early is
// not a runtime error or an Option — the method simply isn't in scope, so it
// won't compile. (Try `OrderBuilder::new().build()` to see the error.)
impl OrderBuilder<Set, Set> {
    fn build(self) -> Order {
        Order {
            price: self.price,
            qty: self.qty,
        }
    }
}

// --- Zero-cost newtype: a checked unit that compiles away ---------------------
// `Ticks` is a distinct type from a bare i64 (you can't mix it up with a Qty),
// but at runtime it's just an i64 — no wrapper, no indirection. `repr(transparent)`
// guarantees it has the exact same layout/ABI as its single field, which both
// documents the intent and lets the optimizer treat the two identically.
#[repr(transparent)]
#[derive(Clone, Copy)]
struct Ticks(i64);

#[inline]
fn sum_raw(xs: &[i64]) -> i64 {
    let mut s = 0;
    for &x in xs {
        s += x;
    }
    s
}

#[inline]
fn sum_newtype(xs: &[Ticks]) -> i64 {
    let mut s = 0;
    for &Ticks(x) in xs {
        s += x;
    }
    s
}

fn main() {
    // Type-state in action: the ONLY path to an Order is via both setters.
    let order = OrderBuilder::new().price(100).qty(10).build();
    println!("[typestate] built {order:?}");
    println!(
        "[typestate] sizeof(builder) = {} bytes (PhantomData is zero-sized)",
        std::mem::size_of::<OrderBuilder<Set, Set>>()
    );
    // These would NOT compile (uncomment to see):
    //   OrderBuilder::new().build();            // no `build` until both Set
    //   OrderBuilder::new().price(1).build();   // qty still Unset

    // Zero-cost proof #1: the newtype has the same size & alignment as i64.
    println!(
        "[zerocost] sizeof(Ticks)={}, sizeof(i64)={}  (identical)",
        std::mem::size_of::<Ticks>(),
        std::mem::size_of::<i64>()
    );

    // Zero-cost proof #2: a micro-bench. The wrapped loop should match the raw
    // loop within noise — the abstraction is compiled away. (Build with --release;
    // in a debug build the wrappers aren't optimized out and this won't hold.)
    //
    // Honest benchmarking note: we take the BEST of several trials (min filters
    // out scheduler/frequency jitter) and wrap inputs/outputs in `black_box` so
    // the optimizer can't hoist the work out of the loop or constant-fold the sum.
    // A single untimed-warmup one-shot would be dominated by noise and mislead.
    const N: usize = 50_000_000;
    let raw: Vec<i64> = (0..N as i64).collect();
    let wrapped: Vec<Ticks> = raw.iter().map(|&x| Ticks(x)).collect();
    let raw = black_box(raw);
    let wrapped = black_box(wrapped);

    let best = |mut f: Box<dyn FnMut() -> i64>| -> (i64, f64) {
        let mut best_ms = f64::MAX;
        let mut out = 0;
        for _ in 0..7 {
            let t = Instant::now();
            out = black_box(f());
            best_ms = best_ms.min(t.elapsed().as_secs_f64() * 1e3);
        }
        (out, best_ms)
    };

    let (s_raw, ms_raw) = best(Box::new(|| sum_raw(black_box(&raw))));
    let (s_new, ms_new) = best(Box::new(|| sum_newtype(black_box(&wrapped))));

    println!("[zerocost] sum_raw     = {s_raw} in {ms_raw:.2} ms (best of 7)");
    println!("[zerocost] sum_newtype = {s_new} in {ms_new:.2} ms (best of 7)");
    println!(
        "[zerocost] ratio newtype/raw = {:.2}x (≈1.0 ⇒ abstraction is free)",
        ms_new / ms_raw.max(f64::MIN_POSITIVE)
    );
    assert_eq!(s_raw, s_new);
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn builder_produces_order() {
        let o = OrderBuilder::new().price(250).qty(4).build();
        assert_eq!(o, Order { price: 250, qty: 4 });
        // Setter order doesn't matter — both reach OrderBuilder<Set, Set>.
        let o2 = OrderBuilder::new().qty(4).price(250).build();
        assert_eq!(o, o2);
    }

    #[test]
    fn newtype_is_zero_sized_overhead() {
        assert_eq!(std::mem::size_of::<Ticks>(), std::mem::size_of::<i64>());
        assert_eq!(std::mem::size_of::<OrderBuilder<Set, Set>>(), 16); // u64 + u32 + pad
    }

    #[test]
    fn sums_agree() {
        let raw = [1i64, 2, 3, 4];
        let wrapped = [Ticks(1), Ticks(2), Ticks(3), Ticks(4)];
        assert_eq!(sum_raw(&raw), 10);
        assert_eq!(sum_newtype(&wrapped), 10);
    }
}
