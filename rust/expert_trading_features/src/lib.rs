//! # expert_trading_features
//!
//! Low-latency trading techniques in Rust — the companion to the C++ collection
//! in [`cpp/expert_trading_features`](../../cpp/expert_trading_features). Demos
//! 01–08 mirror the C++ ones so you can read them side by side; 09–11 cover
//! patterns where Rust's type system specifically pays off in a trading stack.
//!
//! Each demo is a self-contained file in `examples/`, heavily commented, with its
//! own `#[test]`s. The hook in every header is the same question: **what does
//! Rust change versus the C++ version?**
//!
//! ```sh
//! cargo run --release --example 02_spsc_ring_buffer
//! cargo test --examples
//! cargo bench
//! ```
//!
//! These are teaching demos, not a production trading stack. The point is the
//! technique and *why it matters*, with honest notes on when it does and doesn't
//! pay off — and benchmarks you can reproduce on your own box.

/// 64-byte cache-line alignment, so an independently-written field gets its own
/// line and never false-shares with its neighbours (see demo 03). The Rust analog
/// of C++'s `alignas(64)` / `std::hardware_destructive_interference_size`.
#[repr(align(64))]
#[derive(Default)]
pub struct CachePadded<T>(pub T);

impl<T> CachePadded<T> {
    pub const fn new(v: T) -> Self {
        CachePadded(v)
    }
}

impl<T> core::ops::Deref for CachePadded<T> {
    type Target = T;
    fn deref(&self) -> &T {
        &self.0
    }
}
impl<T> core::ops::DerefMut for CachePadded<T> {
    fn deref_mut(&mut self) -> &mut T {
        &mut self.0
    }
}
