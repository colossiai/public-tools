// ============================================================================
// 02 — Structs, enums & pattern matching: modeling data so bad states won't compile
// Run:  cargo run --example 02_structs_enums_matching
// ----------------------------------------------------------------------------
// Rust enums are *sum types*: a value is exactly one of several variants, and a
// variant can carry data. Combined with exhaustive `match`, you make illegal
// states unrepresentable instead of guarding against them at runtime. `Option`
// (a value or nothing) and `Result` (success or error) are just enums in std.
// ============================================================================

// A struct: a product type (all fields at once).
#[derive(Debug, Clone, PartialEq)]
struct Order {
    id: u64,
    side: Side,
    price: u64, // fixed-point ticks
    qty: u32,
}

// A fieldless enum — like a C enum but type-safe and matchable.
#[derive(Debug, Clone, Copy, PartialEq)]
enum Side {
    Buy,
    Sell,
}

// An enum whose variants carry *different* shapes of data. A message is exactly
// one of these — you can never read "the price" of a Cancel because it has none.
#[derive(Debug, Clone, PartialEq)]
enum Event {
    New(Order),
    Cancel { id: u64 },
    Fill { id: u64, filled_qty: u32 },
    Heartbeat,
}

impl Order {
    fn notional(&self) -> u64 {
        self.price * self.qty as u64
    }
}

// `match` must be exhaustive: add a variant and this stops compiling until you
// handle it — refactoring becomes the compiler's job, not yours.
fn describe(ev: &Event) -> String {
    match ev {
        Event::New(o) => format!(
            "NEW {:?} {} @ {} (notional {})",
            o.side,
            o.qty,
            o.price,
            o.notional()
        ),
        Event::Cancel { id } => format!("CANCEL order {id}"),
        // Match guards add conditions; bindings destructure the payload.
        Event::Fill { id, filled_qty } if *filled_qty == 0 => format!("FILL order {id}: nothing"),
        Event::Fill { id, filled_qty } => format!("FILL order {id}: {filled_qty} lots"),
        Event::Heartbeat => "heartbeat".to_string(),
    }
}

// Option<T> models "maybe a value" with no null pointers anywhere.
fn best_of(prices: &[u64]) -> Option<u64> {
    prices.iter().copied().max() // returns None on an empty slice
}

fn main() {
    let events = vec![
        Event::New(Order {
            id: 1,
            side: Side::Buy,
            price: 100_0000,
            qty: 10,
        }),
        Event::New(Order {
            id: 2,
            side: Side::Sell,
            price: 100_0100,
            qty: 5,
        }),
        Event::Fill {
            id: 1,
            filled_qty: 4,
        },
        Event::Fill {
            id: 1,
            filled_qty: 0,
        },
        Event::Cancel { id: 1 },
        Event::Heartbeat,
    ];
    for ev in &events {
        println!("{}", describe(ev));
    }

    // `if let` is a one-arm match for when you only care about one variant.
    if let Some(top) = best_of(&[101, 99, 105, 100]) {
        println!("best price = {top}");
    }

    // `let ... else` handles the "missing" case by diverging (return/break/panic).
    let Some(_top) = best_of(&[]) else {
        println!("no prices → nothing to quote");
        return;
    };
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn notional_is_price_times_qty() {
        let o = Order {
            id: 1,
            side: Side::Sell,
            price: 250,
            qty: 4,
        };
        assert_eq!(o.notional(), 1000);
    }

    #[test]
    fn match_covers_every_variant() {
        assert!(describe(&Event::Heartbeat).contains("heartbeat"));
        assert!(describe(&Event::Cancel { id: 7 }).contains("CANCEL order 7"));
        assert!(describe(&Event::Fill {
            id: 7,
            filled_qty: 0
        })
        .contains("nothing"));
    }

    #[test]
    fn option_handles_empty() {
        assert_eq!(best_of(&[]), None);
        assert_eq!(best_of(&[3, 9, 2]), Some(9));
    }
}
