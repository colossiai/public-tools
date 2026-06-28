// ============================================================================
// 06 — Static vs dynamic dispatch: generics, `dyn Trait`, and object safety
// Run:  cargo run --example 06_trait_objects_and_dispatch
// ----------------------------------------------------------------------------
// Two ways to call trait methods on "some type that implements T":
//
//   * Generics  (`fn f<T: Trait>` / `impl Trait`)  → STATIC dispatch. One copy
//     per concrete type, calls inline, fastest. But every element of a
//     collection must be the SAME type.
//   * Trait objects (`&dyn Trait` / `Box<dyn Trait>`) → DYNAMIC dispatch. One
//     copy of the code; the call goes through a vtable (a fat pointer: data ptr
//     + vtable ptr). Lets you store HETEROGENEOUS types together, at the cost of
//     an indirect call that can't inline.
//
// Use generics by default; reach for `dyn` when you genuinely need a mixed
// collection or to erase the type behind an API boundary.
// ============================================================================

trait Signal {
    fn name(&self) -> &str;
    fn score(&self, price: f64) -> f64;
}

struct Momentum {
    last: f64,
}
struct MeanReversion {
    fair: f64,
}

impl Signal for Momentum {
    fn name(&self) -> &str {
        "momentum"
    }
    fn score(&self, price: f64) -> f64 {
        price - self.last
    }
}
impl Signal for MeanReversion {
    fn name(&self) -> &str {
        "mean-reversion"
    }
    fn score(&self, price: f64) -> f64 {
        self.fair - price
    }
}

// STATIC dispatch: monomorphized, the call inlines. Only one concrete type per call.
fn evaluate_static<S: Signal>(s: &S, price: f64) -> f64 {
    s.score(price)
}

// DYNAMIC dispatch: `&dyn Signal` is a fat pointer; the call hits the vtable.
fn evaluate_dyn(s: &dyn Signal, price: f64) -> f64 {
    s.score(price)
}

// The payoff: a HETEROGENEOUS collection of strategies behind one type.
// You cannot write `Vec<S: Signal>`; you need `Vec<Box<dyn Signal>>`.
fn blended_score(signals: &[Box<dyn Signal>], price: f64) -> f64 {
    signals.iter().map(|s| s.score(price)).sum()
}

fn main() {
    let mom = Momentum { last: 100.0 };
    let rev = MeanReversion { fair: 105.0 };

    println!(
        "static : {} -> {}",
        mom.name(),
        evaluate_static(&mom, 103.0)
    );
    println!("dyn    : {} -> {}", rev.name(), evaluate_dyn(&rev, 103.0));

    // Heterogeneous container — the whole reason `dyn` exists.
    let book: Vec<Box<dyn Signal>> = vec![
        Box::new(Momentum { last: 100.0 }),
        Box::new(MeanReversion { fair: 105.0 }),
    ];
    for s in &book {
        println!("  {:<15} score@103 = {:+.1}", s.name(), s.score(103.0));
    }
    println!("blended score @103 = {:+.1}", blended_score(&book, 103.0));

    // Note on OBJECT SAFETY: a trait is only usable as `dyn Trait` if its methods
    // are dispatchable through a vtable — e.g. no generic methods, and methods
    // take `self`/`&self` rather than returning `Self` by value. `Signal` above
    // is object-safe; a trait with `fn clone_box() -> Self` would not be.
    let sizes = (
        std::mem::size_of::<&Momentum>(),   // thin pointer
        std::mem::size_of::<&dyn Signal>(), // fat pointer (2 words)
    );
    println!(
        "sizeof &Momentum = {}, sizeof &dyn Signal = {} (data+vtable)",
        sizes.0, sizes.1
    );
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn static_and_dyn_agree() {
        let m = Momentum { last: 100.0 };
        assert_eq!(evaluate_static(&m, 103.0), 3.0);
        assert_eq!(evaluate_dyn(&m, 103.0), 3.0);
    }

    #[test]
    fn heterogeneous_blend() {
        let book: Vec<Box<dyn Signal>> = vec![
            Box::new(Momentum { last: 100.0 }),      // +3
            Box::new(MeanReversion { fair: 105.0 }), // +2
        ];
        assert_eq!(blended_score(&book, 103.0), 5.0);
    }

    #[test]
    fn dyn_ref_is_a_fat_pointer() {
        assert_eq!(
            std::mem::size_of::<&dyn Signal>(),
            2 * std::mem::size_of::<usize>()
        );
    }
}
