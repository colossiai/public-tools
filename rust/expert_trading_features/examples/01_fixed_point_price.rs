// ============================================================================
// 01 — Fixed-point prices: never represent money/prices with floating point
// Run:  cargo run --release --example 01_fixed_point_price
// C++ counterpart: cpp/expert_trading_features/01_fixed_point_price.cpp
// ----------------------------------------------------------------------------
// Why this matters in trading:
//   * `f64` cannot represent 0.10 exactly -> rounding drift, failed equality, and
//     prices that don't land on the exchange tick grid.
//   * Exchanges quote on an integer *tick* grid. Store the price AS a scaled
//     integer and all arithmetic is exact, branch-free, and trivially comparable.
//
// What Rust changes vs C++:
//   * A `#[repr(transparent)]` newtype makes `Px` a DISTINCT type from a bare i64
//     (and from `Qty`), so the compiler rejects mixing a price with a quantity —
//     a whole class of bugs gone, at zero runtime cost (same layout as i64).
//   * `derive(PartialOrd, Ord, Eq)` gives exact, total ordering for free.
//   * Arithmetic that can overflow is opt-in explicit (`checked_`/`saturating_`),
//     and debug builds panic on overflow instead of silently wrapping.
// ============================================================================

use std::fmt;

/// A price scaled to 4 implied decimals (1 unit = 0.0001). 123.4500 -> 1_234_500.
/// `repr(transparent)` => identical layout/ABI to `i64`; the newtype is free.
#[repr(transparent)]
#[derive(Clone, Copy, PartialEq, Eq, PartialOrd, Ord, Hash, Default)]
struct Px(i64);

/// A separate unit for size. Because `Px` and `Qty` are different types, you
/// cannot accidentally pass a quantity where a price is expected.
#[repr(transparent)]
#[derive(Clone, Copy, PartialEq, Eq, PartialOrd, Ord, Default)]
struct Qty(u64);

impl Px {
    const SCALE: i64 = 10_000; // 4 decimal places

    const fn from_decimal(whole: i64, frac4: i64) -> Px {
        Px(whole * Px::SCALE + frac4)
    }
    const fn raw(self) -> i64 {
        self.0
    }

    // Exact arithmetic. `checked_add` returns None on overflow rather than wrapping
    // or invoking UB — you decide the policy at the call site.
    fn checked_add(self, rhs: Px) -> Option<Px> {
        self.0.checked_add(rhs.0).map(Px)
    }

    // Snap to a coarser tick (e.g. round a theo to the $0.01 grid), round-half-up,
    // entirely on the integer grid — no float ever touches a price.
    fn round_to_tick(self, tick: i64) -> Px {
        let half = tick / 2;
        let bias = if self.0 >= 0 { half } else { -half };
        Px(((self.0 + bias) / tick) * tick)
    }
}

// Operator overloading is just a trait. We only implement the ops that make sense
// for a price (Px + Px, Px - Px) — you can't multiply two prices together.
impl std::ops::Add for Px {
    type Output = Px;
    fn add(self, o: Px) -> Px {
        Px(self.0 + o.0)
    }
}
impl std::ops::Sub for Px {
    type Output = Px;
    fn sub(self, o: Px) -> Px {
        Px(self.0 - o.0)
    }
}

// Only convert to text at the edge (logging / display).
impl fmt::Display for Px {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        let w = self.0 / Px::SCALE;
        let frac = (self.0 % Px::SCALE).abs();
        write!(f, "{w}.{frac:04}")
    }
}
impl fmt::Debug for Px {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(f, "Px({self})")
    }
}

fn main() {
    // The classic floating-point trap.
    let a = 0.1f64 + 0.2;
    println!("f64   0.1 + 0.2 == 0.3 ? {}   (actual = {a:.17})", a == 0.3);

    // Fixed-point is exact.
    let p1 = Px::from_decimal(0, 1000); // 0.1000
    let p2 = Px::from_decimal(0, 2000); // 0.2000
    let p3 = Px::from_decimal(0, 3000); // 0.3000
    println!(
        "fixed 0.1 + 0.2 == 0.3 ? {}   (sum = {})",
        p1 + p2 == p3,
        p1 + p2
    );

    let bid = Px::from_decimal(123, 4500);
    let ask = Px::from_decimal(123, 4600);
    println!("bid={bid} ask={ask} spread={}", ask - bid);

    let theo = Px::from_decimal(123, 4537);
    println!("theo={theo} rounded-to-$0.01={}", theo.round_to_tick(100));

    // The unit safety: this line does not compile — Px and Qty are distinct types.
    //   let _ = bid + Qty(100);
    let size = Qty(100);
    println!(
        "(price {bid} and qty {} are different types — can't be mixed)",
        size.0
    );

    // `const fn` => compile-time pricing, zero runtime cost.
    const LIMIT: Px = Px::from_decimal(100, 2500);
    const _: () = assert!(LIMIT.raw() == 1_002_500);
    println!("const limit price = {LIMIT}");

    // Overflow is explicit: checked_add returns None instead of wrapping/UB.
    println!(
        "checked_add near MAX: {:?}",
        Px(i64::MAX).checked_add(Px(1))
    );
    println!(
        "checked_add normal:   {:?}",
        bid.checked_add(Px::from_decimal(0, 100))
    );
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn addition_is_exact() {
        assert_eq!(
            Px::from_decimal(0, 1000) + Px::from_decimal(0, 2000),
            Px::from_decimal(0, 3000)
        );
    }

    #[test]
    fn ordering_is_total_and_exact() {
        let mut v = [
            Px::from_decimal(1, 0),
            Px::from_decimal(0, 9999),
            Px::from_decimal(1, 1),
        ];
        v.sort();
        assert_eq!(
            v,
            [
                Px::from_decimal(0, 9999),
                Px::from_decimal(1, 0),
                Px::from_decimal(1, 1)
            ]
        );
    }

    #[test]
    fn round_to_penny() {
        assert_eq!(
            Px::from_decimal(123, 4537).round_to_tick(100),
            Px::from_decimal(123, 4500)
        );
        assert_eq!(
            Px::from_decimal(123, 4567).round_to_tick(100),
            Px::from_decimal(123, 4600)
        );
    }

    #[test]
    fn checked_add_flags_overflow() {
        assert_eq!(Px(i64::MAX).checked_add(Px(1)), None);
        assert_eq!(Px(1).checked_add(Px(2)), Some(Px(3)));
    }

    #[test]
    fn newtype_is_zero_cost() {
        assert_eq!(std::mem::size_of::<Px>(), std::mem::size_of::<i64>());
    }
}
