// ============================================================================
// 07 — Cycle-accurate timestamps & a latency histogram (measure the tail)
// Run:  cargo run --release --example 07_low_latency_timestamp
// C++ counterpart: cpp/expert_trading_features/07_low_latency_timestamp.cpp
// ----------------------------------------------------------------------------
// You can't optimize what you can't measure, and in trading the TAIL is what
// matters (the p99.9 outlier, not the mean).
//
// Techniques (same as the C++ version):
//   * rdtscp — read the CPU time-stamp counter directly (~5-10 ns) instead of a
//     syscall-backed clock. On modern x86 the TSC is invariant (constant rate).
//   * lfence around the read so instructions don't drift out of the timed region.
//   * A latency histogram to recover percentiles (p50/p99/p99.9/max).
//
// What Rust changes vs C++:
//   * `rdtscp`/`lfence` are `core::arch::x86_64` intrinsics behind `unsafe` and
//     `#[cfg(target_arch = "x86_64")]`, with a `std::time::Instant` fallback
//     elsewhere — the portability split is explicit in the type/cfg, not #ifdef.
//   * `#[inline(never)]` pins the function under test so it isn't optimized away.
// ============================================================================

use std::time::Instant;

#[cfg(target_arch = "x86_64")]
mod tsc {
    use core::arch::x86_64::{__rdtscp, _mm_lfence, _rdtsc};

    #[inline(always)]
    pub fn ticks() -> u64 {
        // SAFETY: rdtscp/lfence have no memory-safety preconditions; the fences
        // keep earlier/later work from reordering across the read.
        unsafe {
            _mm_lfence();
            let mut aux = 0u32;
            let t = __rdtscp(&mut aux);
            _mm_lfence();
            t
        }
    }
    pub fn calibrate_ticks_per_ns() -> f64 {
        use std::time::Instant;
        let w0 = Instant::now();
        let c0 = unsafe { _rdtsc() };
        while w0.elapsed() < std::time::Duration::from_millis(50) {
            std::hint::spin_loop();
        }
        let c1 = unsafe { _rdtsc() };
        (c1 - c0) as f64 / (w0.elapsed().as_secs_f64() * 1e9)
    }
    pub const HAS_TSC: bool = true;
}

#[cfg(not(target_arch = "x86_64"))]
mod tsc {
    use std::time::Instant;
    thread_local! { static START: Instant = Instant::now(); }
    #[inline(always)]
    pub fn ticks() -> u64 {
        START.with(|s| s.elapsed().as_nanos() as u64)
    }
    pub fn calibrate_ticks_per_ns() -> f64 {
        1.0
    }
    pub const HAS_TSC: bool = false;
}

// The "work" we profile: a tiny order-encode step. `inline(never)` so it stays a
// real call the timer can bracket.
#[inline(never)]
fn encode_order(id: u64, px: i64, qty: u32) -> u64 {
    let mut h = id.wrapping_mul(1099511628211);
    h ^= px as u64;
    h = h.wrapping_mul(1099511628211);
    h ^= qty as u64;
    h
}

fn main() {
    let tpns = if tsc::HAS_TSC {
        tsc::calibrate_ticks_per_ns()
    } else {
        1.0
    };
    println!("TSC available: {}   (~{tpns:.3} ticks/ns)", tsc::HAS_TSC);

    const N: usize = 200_000;
    let mut samples: Vec<u64> = Vec::with_capacity(N);
    let mut sink = 0u64;
    for i in 0..N as u64 {
        let start = tsc::ticks();
        sink ^= encode_order(i, 1_000_000 + (i % 7) as i64, 100);
        let end = tsc::ticks();
        samples.push(end - start);
    }

    // Convert to ns and recover percentiles by sorting (fine for an offline report).
    let mut ns: Vec<f64> = samples
        .iter()
        .map(|&t| {
            if tsc::HAS_TSC {
                t as f64 / tpns
            } else {
                t as f64
            }
        })
        .collect();
    ns.sort_by(|a, b| a.partial_cmp(b).unwrap());

    let pct = |p: f64| ns[((p / 100.0) * (ns.len() - 1) as f64) as usize];
    println!("encode_order latency over {N} samples (sink={sink:#x}):");
    println!("  p50   = {:7.2} ns", pct(50.0));
    println!("  p99   = {:7.2} ns", pct(99.0));
    println!("  p99.9 = {:7.2} ns", pct(99.9));
    println!(
        "  max   = {:7.2} ns   <-- the tail you actually fear",
        ns[ns.len() - 1]
    );

    // Show the syscall-clock overhead for contrast.
    let t0 = Instant::now();
    let _ = Instant::now().duration_since(t0);
    println!(
        "(Instant::now() pair overhead is itself tens of ns — too coarse to time an 18 ns op)"
    );
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn encode_is_deterministic() {
        assert_eq!(encode_order(1, 100, 10), encode_order(1, 100, 10));
        assert_ne!(encode_order(1, 100, 10), encode_order(2, 100, 10));
    }

    #[test]
    fn ticks_are_monotonic_nondecreasing() {
        let a = tsc::ticks();
        let b = tsc::ticks();
        assert!(b >= a);
    }
}
