// ============================================================================
// 04 — Collections & iterators: the lazy, zero-cost functional core
// Run:  cargo run --example 04_collections_and_iterators
// ----------------------------------------------------------------------------
// Iterators are Rust's workhorse. An iterator chain is LAZY: adapters like `map`
// and `filter` build a state machine that does no work until a *consumer*
// (`collect`, `sum`, `for`) drives it. Because each adapter monomorphizes and
// inlines, the chain compiles down to roughly the same code as a hand-written
// loop — "zero-cost abstraction". This file tours Vec/HashMap/BTreeMap and the
// adapters you'll reach for daily.
// ============================================================================

use std::collections::{BTreeMap, HashMap};

#[derive(Debug, Clone)]
struct Trade {
    symbol: &'static str,
    price: u64,
    qty: u32,
}

fn trades() -> Vec<Trade> {
    vec![
        Trade {
            symbol: "AAA",
            price: 100,
            qty: 10,
        },
        Trade {
            symbol: "BBB",
            price: 250,
            qty: 4,
        },
        Trade {
            symbol: "AAA",
            price: 101,
            qty: 7,
        },
        Trade {
            symbol: "CCC",
            price: 50,
            qty: 20,
        },
        Trade {
            symbol: "BBB",
            price: 248,
            qty: 9,
        },
    ]
}

// A classic lazy chain: filter → map → sum, all fused into one pass, no temp Vec.
fn notional_above(trades: &[Trade], min_price: u64) -> u64 {
    trades
        .iter()
        .filter(|t| t.price >= min_price)
        .map(|t| t.price * t.qty as u64)
        .sum()
}

// `fold` accumulates into any state; here we group volume by symbol into a map.
// HashMap = fast unordered lookup; BTreeMap = sorted iteration. Pick by need.
fn volume_by_symbol(trades: &[Trade]) -> BTreeMap<&'static str, u64> {
    trades.iter().fold(BTreeMap::new(), |mut acc, t| {
        *acc.entry(t.symbol).or_insert(0) += t.qty as u64; // entry API: insert-or-update
        acc
    })
}

fn main() {
    let ts = trades();

    println!("notional (price>=100): {}", notional_above(&ts, 100));

    // enumerate + take + collect: index pairs of the first few, materialized.
    let head: Vec<(usize, &'static str)> =
        ts.iter().map(|t| t.symbol).enumerate().take(3).collect();
    println!("first 3 symbols: {head:?}");

    // Volume per symbol (sorted because BTreeMap).
    for (sym, vol) in volume_by_symbol(&ts) {
        println!("  {sym}: volume {vol}");
    }

    // Counting occurrences with a HashMap.
    let mut counts: HashMap<&str, usize> = HashMap::new();
    for t in &ts {
        *counts.entry(t.symbol).or_default() += 1;
    }
    println!("distinct symbols traded: {}", counts.len());

    // Iterators compose with ranges and produce other iterators lazily.
    let squares_of_evens: Vec<u64> = (1..=10).filter(|n| n % 2 == 0).map(|n| n * n).collect();
    println!("squares of evens 1..=10: {squares_of_evens:?}");

    // `collect` can even build a Result<Vec<_>, _>: short-circuits on first Err.
    let parsed: Result<Vec<i32>, _> = ["1", "2", "3"].iter().map(|s| s.parse::<i32>()).collect();
    println!("parsed all: {parsed:?}");
    let parsed_bad: Result<Vec<i32>, _> =
        ["1", "x", "3"].iter().map(|s| s.parse::<i32>()).collect();
    println!("parsed with bad: is_err={}", parsed_bad.is_err());
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn lazy_chain_sums_correctly() {
        // 100*10 + 250*4 + 101*7 + 248*9 (CCC@50 filtered out)
        assert_eq!(notional_above(&trades(), 100), 1000 + 1000 + 707 + 2232);
    }

    #[test]
    fn grouping_is_sorted_and_correct() {
        let v = volume_by_symbol(&trades());
        let keys: Vec<_> = v.keys().copied().collect();
        assert_eq!(keys, ["AAA", "BBB", "CCC"]); // BTreeMap → sorted
        assert_eq!(v["AAA"], 17);
        assert_eq!(v["BBB"], 13);
    }

    #[test]
    fn collect_into_result_short_circuits() {
        let bad: Result<Vec<i32>, _> = ["1", "x"].iter().map(|s| s.parse::<i32>()).collect();
        assert!(bad.is_err());
    }
}
