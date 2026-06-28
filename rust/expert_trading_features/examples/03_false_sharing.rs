// ============================================================================
// 03 — False sharing: the silent latency killer (and how alignment kills it)
// Run:  cargo run --release --example 03_false_sharing
// C++ counterpart: cpp/expert_trading_features/03_false_sharing.cpp
// ----------------------------------------------------------------------------
// Two threads writing two DIFFERENT variables should be independent. But if both
// sit on the SAME 64-byte cache line, every write by one core invalidates the
// line in the other's cache => the coherence protocol ping-pongs the line and
// throughput collapses.
//
// Fix: put each hot, independently-written counter on its OWN cache line.
//
// What Rust changes vs C++:
//   * `alignas(64)` becomes `#[repr(align(64))]` (here via the crate's
//     `CachePadded<T>`). Same idea, same effect.
//   * Layout is explicit and the wrapper is a normal type you can reuse — the
//     SPSC ring in demo 02 uses the very same `CachePadded` for its head/tail.
// ============================================================================

use expert_trading_features::CachePadded;
use std::sync::atomic::{AtomicU64, Ordering};
use std::time::Instant;

const ITERS: u64 = 100_000_000;

// PACKED: two counters adjacent -> almost certainly the same cache line.
#[derive(Default)]
struct Packed {
    a: AtomicU64,
    b: AtomicU64,
}

// PADDED: each counter forced onto its own cache line.
#[derive(Default)]
struct PaddedCounters {
    a: CachePadded<AtomicU64>,
    b: CachePadded<AtomicU64>,
}

fn bench(label: &str, a: &AtomicU64, b: &AtomicU64) -> f64 {
    let hammer = |x: &AtomicU64| {
        for _ in 0..ITERS {
            x.fetch_add(1, Ordering::Relaxed);
        }
    };
    let t0 = Instant::now();
    std::thread::scope(|s| {
        s.spawn(|| hammer(a));
        s.spawn(|| hammer(b));
    });
    let ns = t0.elapsed().as_secs_f64() * 1e9;
    let per_op = ns / (2.0 * ITERS as f64);
    println!(
        "{label:<8} {per_op:>6.2} ns/op   (a={}, b={})",
        a.load(Ordering::Relaxed),
        b.load(Ordering::Relaxed)
    );
    per_op
}

fn main() {
    println!("cache line = 64 bytes, {ITERS} increments per thread\n");
    let packed = Packed::default();
    let padded = PaddedCounters::default();

    let p = bench("packed", &packed.a, &packed.b); // false sharing
    let q = bench("padded", &padded.a, &padded.b); // isolated lines

    println!(
        "\npadding speedup: {:.2}x  (sizeof Packed={}, Padded={})",
        p / q,
        std::mem::size_of::<Packed>(),
        std::mem::size_of::<PaddedCounters>()
    );
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn padded_isolates_onto_separate_lines() {
        // Each CachePadded field is 64-byte aligned, so the two counters cannot
        // share a line; the struct is at least two lines wide.
        assert!(std::mem::size_of::<PaddedCounters>() >= 128);
        assert_eq!(std::mem::align_of::<CachePadded<AtomicU64>>(), 64);
    }

    #[test]
    fn packed_is_compact() {
        assert_eq!(std::mem::size_of::<Packed>(), 16); // two u64s, same line
    }
}
