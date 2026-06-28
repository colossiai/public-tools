// ============================================================================
// 05 — Array-indexed limit order book: O(1) updates, O(1) best bid/ask
// Run:  cargo run --release --example 05_order_book
// C++ counterpart: cpp/expert_trading_features/05_order_book.cpp
// ----------------------------------------------------------------------------
// A `BTreeMap<price, level>` is the textbook book but it's a pointer-chasing tree
// => a cache miss per operation. The low-latency design: prices live on a bounded
// integer TICK grid, so use a flat array indexed by tick. Then add/cancel = O(1)
// array write, and best bid/ask = O(1) amortized (track the touch, only scan when
// the top empties). Everything is contiguous => prefetch-friendly, deterministic.
//
// What Rust changes vs C++:
//   * The flat array is a `Vec<u64>` (heap, sized at construction) instead of a
//     giant `std::array` member — no risk of blowing the stack, and bounds are
//     checked in debug builds (and elided in release where provably safe).
//   * `Option<…>`/sentinels for "empty side" are explicit; no magic -1 unless we
//     choose it. We benchmark this against `BTreeMap` in `cargo bench`.
// ============================================================================

const MIN_TICK: i32 = 0;
const MAX_TICK: i32 = 1 << 16; // 65,536 price levels

pub struct OrderBook {
    bid_qty: Vec<u64>, // resting qty per tick
    ask_qty: Vec<u64>,
    best_bid: i32, // -1 => empty side
    best_ask: i32, // MAX_TICK => empty side
}

impl OrderBook {
    pub fn new() -> Self {
        OrderBook {
            bid_qty: vec![0; MAX_TICK as usize],
            ask_qty: vec![0; MAX_TICK as usize],
            best_bid: -1,
            best_ask: MAX_TICK,
        }
    }

    pub fn add_bid(&mut self, tick: i32, qty: u64) {
        self.bid_qty[tick as usize] += qty;
        if tick > self.best_bid {
            self.best_bid = tick; // new top of book
        }
    }
    pub fn add_ask(&mut self, tick: i32, qty: u64) {
        self.ask_qty[tick as usize] += qty;
        if tick < self.best_ask {
            self.best_ask = tick;
        }
    }

    // Remove size (cancel/execute) — O(1), with a cheap re-scan only if the top empties.
    pub fn reduce_bid(&mut self, tick: i32, qty: u64) {
        self.bid_qty[tick as usize] -= qty;
        if tick == self.best_bid && self.bid_qty[tick as usize] == 0 {
            while self.best_bid >= MIN_TICK && self.bid_qty[self.best_bid as usize] == 0 {
                self.best_bid -= 1;
            }
        }
    }
    pub fn reduce_ask(&mut self, tick: i32, qty: u64) {
        self.ask_qty[tick as usize] -= qty;
        if tick == self.best_ask && self.ask_qty[tick as usize] == 0 {
            while self.best_ask < MAX_TICK && self.ask_qty[self.best_ask as usize] == 0 {
                self.best_ask += 1;
            }
        }
    }

    pub fn best_bid(&self) -> i32 {
        self.best_bid
    }
    pub fn best_ask(&self) -> i32 {
        self.best_ask
    }
    pub fn bid_size(&self, tick: i32) -> u64 {
        self.bid_qty[tick as usize]
    }
    pub fn ask_size(&self, tick: i32) -> u64 {
        self.ask_qty[tick as usize]
    }
    pub fn crossed(&self) -> bool {
        self.best_bid >= self.best_ask
    }
    /// Mid in ticks ×2 (stays integer when the spread is odd).
    pub fn mid_x2(&self) -> i32 {
        self.best_bid + self.best_ask
    }
}

impl Default for OrderBook {
    fn default() -> Self {
        Self::new()
    }
}

fn print_top(b: &OrderBook, tag: &str) {
    println!(
        "[{tag}] best_bid={} ({}) | best_ask={} ({}) | mid2={} | crossed={}",
        b.best_bid(),
        b.bid_size(b.best_bid().max(0)),
        b.best_ask(),
        b.ask_size(b.best_ask().min(MAX_TICK - 1)),
        b.mid_x2(),
        b.crossed()
    );
}

fn main() {
    let mut book = OrderBook::new();
    book.add_bid(9998, 300);
    book.add_bid(9999, 500);
    book.add_bid(10000, 200); // top bid
    book.add_ask(10002, 400); // top ask
    book.add_ask(10003, 600);
    print_top(&book, "built");

    book.reduce_bid(10000, 200); // top bid filled -> best walks down O(1) amortized
    print_top(&book, "top bid filled");

    book.add_ask(10001, 150); // tighter offer
    print_top(&book, "ask improves");

    book.reduce_ask(10001, 150);
    book.reduce_ask(10002, 400);
    print_top(&book, "asks cancelled");

    println!("(run `cargo bench` for ns/op vs BTreeMap)");
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn best_tracks_top_of_book() {
        let mut b = OrderBook::new();
        b.add_bid(100, 10);
        b.add_bid(101, 5);
        assert_eq!(b.best_bid(), 101);
        b.add_ask(105, 7);
        assert_eq!(b.best_ask(), 105);
        assert!(!b.crossed());
    }

    #[test]
    fn best_walks_when_top_empties() {
        let mut b = OrderBook::new();
        b.add_bid(100, 10);
        b.add_bid(101, 5);
        b.reduce_bid(101, 5); // empties the top -> walk down to 100
        assert_eq!(b.best_bid(), 100);
    }
}
