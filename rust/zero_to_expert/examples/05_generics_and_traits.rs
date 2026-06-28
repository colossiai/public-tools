// ============================================================================
// 05 — Generics & traits: shared behavior with zero runtime cost
// Run:  cargo run --example 05_generics_and_traits
// ----------------------------------------------------------------------------
// Traits are Rust's interfaces: a set of methods a type can implement. Generics
// let a function/struct work over ANY type that satisfies given trait bounds.
// Crucially this is *monomorphized*: the compiler stamps out a specialized copy
// per concrete type, so a generic call is as fast as a hand-written one (static
// dispatch). This file shows trait bounds, default methods, operator overloading
// (`Add`), and the `From`/`Into` conversion traits.
// ============================================================================

use std::ops::Add;

// A trait with one required method and one DEFAULT method built on top of it.
// Implementors get `describe` for free unless they override it.
trait Instrument {
    fn ticker(&self) -> &str;
    fn risk_weight(&self) -> f64;

    fn describe(&self) -> String {
        format!("{} (risk weight {:.2})", self.ticker(), self.risk_weight())
    }
}

struct Equity {
    symbol: String,
}
struct Bond {
    isin: String,
    duration: f64,
}

impl Instrument for Equity {
    fn ticker(&self) -> &str {
        &self.symbol
    }
    fn risk_weight(&self) -> f64 {
        1.0
    }
}
impl Instrument for Bond {
    fn ticker(&self) -> &str {
        &self.isin
    }
    fn risk_weight(&self) -> f64 {
        0.2 * self.duration
    }
    fn describe(&self) -> String {
        // override the default
        format!(
            "BOND {} dur={:.1}y rw={:.2}",
            self.isin,
            self.duration,
            self.risk_weight()
        )
    }
}

// Generic function with a trait bound. `T: Instrument` reads "for any T that
// implements Instrument". Resolved & inlined at compile time, per concrete T.
fn capital_charge<T: Instrument>(inst: &T, notional: f64) -> f64 {
    notional * inst.risk_weight()
}

// `impl Trait` in argument position is sugar for an anonymous generic bound.
fn print_instrument(inst: impl Instrument) {
    println!("  {}", inst.describe());
}

// Operator overloading is just a trait (`Add`). A fixed-point price newtype:
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
struct Ticks(i64);

impl Add for Ticks {
    type Output = Ticks; // associated type: the result
    fn add(self, rhs: Ticks) -> Ticks {
        Ticks(self.0 + rhs.0)
    }
}

// From gives you Into for free: `let t: Ticks = 5i64.into();`
impl From<i64> for Ticks {
    fn from(v: i64) -> Self {
        Ticks(v)
    }
}

fn main() {
    let eq = Equity {
        symbol: "AAPL".into(),
    };
    let bd = Bond {
        isin: "US10Y".into(),
        duration: 8.5,
    };

    println!("charge(equity, 1000) = {}", capital_charge(&eq, 1000.0));
    println!("charge(bond,   1000) = {}", capital_charge(&bd, 1000.0));

    print_instrument(eq);
    print_instrument(bd);

    let spread = Ticks(105) + Ticks::from(3); // operator + From/Into
    let limit: Ticks = 200.into();
    println!("spread={spread:?}, limit={limit:?}");
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn default_and_override_methods() {
        assert_eq!(
            Equity { symbol: "X".into() }.describe(),
            "X (risk weight 1.00)"
        );
        assert!(Bond {
            isin: "Y".into(),
            duration: 5.0
        }
        .describe()
        .starts_with("BOND Y"));
    }

    #[test]
    fn generic_charge_uses_risk_weight() {
        let b = Bond {
            isin: "Z".into(),
            duration: 10.0,
        };
        assert_eq!(capital_charge(&b, 100.0), 100.0 * 2.0); // 0.2 * 10.0 = 2.0
    }

    #[test]
    fn operator_and_conversion() {
        assert_eq!(Ticks(2) + Ticks(3), Ticks(5));
        let t: Ticks = 7i64.into();
        assert_eq!(t, Ticks(7));
    }
}
