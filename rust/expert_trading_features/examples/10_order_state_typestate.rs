// ============================================================================
// 10 — Type-state order lifecycle: illegal transitions don't compile
// Run:  cargo run --release --example 10_order_state_typestate
// (No C++ counterpart — this is a place Rust's type system specifically shines.)
// ----------------------------------------------------------------------------
// An order moves through a state machine: PendingNew -> Live -> (Filled | Cancelled).
// Calling the wrong method for the current state (fill a cancelled order, cancel
// one the exchange hasn't acked yet) is a classic, costly trading bug.
//
// Rust lets you encode the STATE IN THE TYPE. `Order<Live>` and `Order<Cancelled>`
// are different types; `fill()` exists only on `Order<Live>`. A wrong transition
// isn't a runtime check or a panic — it simply fails to compile. And because the
// state marker is a zero-sized `PhantomData`, this safety costs ZERO bytes and
// ZERO instructions: `Order<Live>` has the same layout as the raw fields.
//
// This is the type-state pattern applied to the order lifecycle — the kind of
// invariant you'd otherwise enforce with runtime asserts and hope your tests hit.
// ============================================================================

use std::marker::PhantomData;

// State markers — zero-sized types used only at compile time.
pub struct PendingNew;
pub struct Live;
pub struct Filled;
pub struct Cancelled;

pub struct Order<State> {
    id: u64,
    price: i64,
    qty: u32,
    filled: u32,
    _state: PhantomData<State>,
}

// Fields/queries available in ANY state.
impl<S> Order<S> {
    pub fn id(&self) -> u64 {
        self.id
    }
    pub fn price(&self) -> i64 {
        self.price
    }
    fn transition<New>(self) -> Order<New> {
        Order {
            id: self.id,
            price: self.price,
            qty: self.qty,
            filled: self.filled,
            _state: PhantomData,
        }
    }
}

impl Order<PendingNew> {
    /// Create a freshly-submitted order awaiting exchange acknowledgement.
    pub fn submit(id: u64, price: i64, qty: u32) -> Self {
        Order {
            id,
            price,
            qty,
            filled: 0,
            _state: PhantomData,
        }
    }
    /// Exchange acked => the order is now working.
    pub fn ack(self) -> Order<Live> {
        self.transition()
    }
    /// Rejected before it ever worked.
    pub fn reject(self) -> Order<Cancelled> {
        self.transition()
    }
}

impl Order<Live> {
    /// A (partial or full) fill. Returns either a still-Live order (partial) or a
    /// Filled one (complete) — encoded as an enum so the caller must handle both.
    pub fn fill(mut self, n: u32) -> FillResult {
        self.filled += n;
        if self.filled >= self.qty {
            FillResult::Complete(self.transition())
        } else {
            FillResult::Partial(self)
        }
    }
    /// Cancel a working order.
    pub fn cancel(self) -> Order<Cancelled> {
        self.transition()
    }
    pub fn remaining(&self) -> u32 {
        self.qty - self.filled
    }
}

impl Order<Filled> {
    pub fn filled_qty(&self) -> u32 {
        self.filled
    }
}

pub enum FillResult {
    Partial(Order<Live>),
    Complete(Order<Filled>),
}

fn main() {
    // The happy path: submit -> ack -> partial fill -> full fill.
    let o = Order::<PendingNew>::submit(1, 1_000_000, 100);
    let o = o.ack(); // now Order<Live>
    println!("order {} live, {} to go", o.id(), o.remaining());

    let o = match o.fill(40) {
        FillResult::Partial(live) => {
            println!("partial fill, {} remaining", live.remaining());
            live
        }
        FillResult::Complete(_) => unreachable!(),
    };
    match o.fill(60) {
        FillResult::Complete(done) => println!(
            "order {} fully filled: {} lots",
            done.id(),
            done.filled_qty()
        ),
        FillResult::Partial(_) => unreachable!(),
    }

    // The point: these illegal transitions DO NOT COMPILE (uncomment to see):
    //   let p = Order::<PendingNew>::submit(2, 100, 10);
    //   p.fill(1);          // error: no method `fill` on Order<PendingNew>
    //   let c = p.ack().cancel();
    //   c.fill(1);          // error: no method `fill` on Order<Cancelled>
    println!("(illegal transitions like filling a cancelled order are compile errors)");

    println!(
        "sizeof Order<Live> = {} bytes (PhantomData state marker is free)",
        std::mem::size_of::<Order<Live>>()
    );
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn full_lifecycle() {
        let o = Order::<PendingNew>::submit(1, 100, 10).ack();
        match o.fill(10) {
            FillResult::Complete(done) => assert_eq!(done.filled_qty(), 10),
            FillResult::Partial(_) => panic!("should be complete"),
        }
    }

    #[test]
    fn partial_then_complete() {
        let o = Order::<PendingNew>::submit(1, 100, 10).ack();
        let o = match o.fill(3) {
            FillResult::Partial(o) => {
                assert_eq!(o.remaining(), 7);
                o
            }
            FillResult::Complete(_) => panic!(),
        };
        assert!(matches!(o.fill(7), FillResult::Complete(_)));
    }

    #[test]
    fn state_marker_is_zero_cost() {
        // No bigger than the four data fields (u64 + i64 + u32 + u32 = 24).
        assert_eq!(std::mem::size_of::<Order<Live>>(), 24);
        assert_eq!(
            std::mem::size_of::<Order<Live>>(),
            std::mem::size_of::<Order<Cancelled>>()
        );
    }
}
