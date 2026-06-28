// ============================================================================
// 06 — Branchless code & software prefetch (with a reality check)
// Run:  cargo run --release --example 06_branchless_and_prefetch
// C++ counterpart: cpp/expert_trading_features/06_branch_and_prefetch.cpp
// ----------------------------------------------------------------------------
// On the hot path a mispredicted branch (~15-20 cycles) or an L2/L3 miss (tens to
// hundreds) dwarfs the actual work. Two tools:
//   1. Branchless selection — replace an unpredictable data-dependent branch with
//      arithmetic/`cmov` so there's nothing to mispredict.
//   2. Software prefetch — pull the next record into cache while working on the
//      current one, hiding latency when you know the access pattern.
//
// What Rust changes vs C++:
//   * Prefetch is a target-specific intrinsic: `core::arch::x86_64::_mm_prefetch`
//     (unsafe, behind `#[cfg(target_arch)]`), with a portable no-op fallback.
//   * Branch-likelihood hints (`[[likely]]`) have no stable surface in Rust; you
//     lean on the optimizer / `#[cold]` for the rare path. As in C++, at `-O3`
//     LLVM often already emits a branchless `cmov`, so the win can vanish —
//     measure, don't guess.
// ============================================================================

use std::time::Instant;

#[cfg(target_arch = "x86_64")]
#[inline(always)]
fn prefetch<T>(p: *const T) {
    use core::arch::x86_64::{_mm_prefetch, _MM_HINT_T0};
    // SAFETY: _mm_prefetch has no memory-safety preconditions — a bad address is
    // simply ignored by the CPU; it only hints the cache.
    unsafe { _mm_prefetch::<_MM_HINT_T0>(p as *const i8) };
}
#[cfg(not(target_arch = "x86_64"))]
#[inline(always)]
fn prefetch<T>(_p: *const T) {}

fn main() {
    const N: usize = 1 << 22; // ~4M samples
                              // Deterministic pseudo-random data in [0, 100): a simple LCG, fixed seed.
    let mut state: u64 = 0x1234_5678;
    let data: Vec<i32> = (0..N)
        .map(|_| {
            state = state
                .wrapping_mul(6364136223846793005)
                .wrapping_add(1442695040888963407);
            ((state >> 33) % 100) as i32
        })
        .collect();

    // Branchy: ~50/50 data-dependent branch — worst case for the predictor.
    let t0 = Instant::now();
    let mut sum_branchy: i64 = 0;
    for &v in &data {
        if v >= 50 {
            sum_branchy += v as i64;
        }
    }
    let ns_branchy = t0.elapsed().as_secs_f64() * 1e9 / N as f64;

    // Branchless: turn the condition into a 0/-1 mask, no branch to mispredict.
    let t1 = Instant::now();
    let mut sum_branchless: i64 = 0;
    for &v in &data {
        let mask = -((v >= 50) as i64); // 0 or -1 (all ones)
        sum_branchless += (v as i64) & mask;
    }
    let ns_branchless = t1.elapsed().as_secs_f64() * 1e9 / N as f64;

    println!("branchy    : {ns_branchy:.3} ns/elem  sum={sum_branchy}");
    println!(
        "branchless : {ns_branchless:.3} ns/elem  sum={sum_branchless}  (speedup {:.2}x)",
        ns_branchy / ns_branchless
    );

    // Software prefetch a few iterations ahead.
    const AHEAD: usize = 16;
    let t2 = Instant::now();
    let mut sum_pf: i64 = 0;
    for i in 0..N {
        if i + AHEAD < N {
            prefetch(&data[i + AHEAD]);
        }
        sum_pf += data[i] as i64;
    }
    let ns_pf = t2.elapsed().as_secs_f64() * 1e9 / N as f64;
    println!("prefetched : {ns_pf:.3} ns/elem  sum={sum_pf}");

    // A branchless max with no comparison branch (e.g. clamp on a hot path).
    println!(
        "branchless_max(40, 99) = {}, branchless_max(7, -3) = {}",
        branchless_max(40, 99),
        branchless_max(7, -3)
    );

    println!(
        "\nreality check: at -O3 LLVM often compiles the 'branchy' loop to a cmov\n\
         already, so the two can tie. Prefetch only wins when data is COLD and the\n\
         access is far enough ahead; here the array is hot, so it can even cost a bit."
    );
}

// Branchless `max` without a comparison branch — handy on a hot path. We test
// that the bit-twiddling matches the obvious version on a range of inputs.
fn branchless_max(a: i32, b: i32) -> i32 {
    let diff = (a - b) as i64;
    let mask = (diff >> 63) as i32; // 0 if a>=b, -1 if a<b
                                    // a if a>=b else b, without a branch
    a ^ ((a ^ b) & mask)
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn branchless_max_matches_std() {
        for a in -20..20 {
            for b in -20..20 {
                assert_eq!(branchless_max(a, b), a.max(b), "a={a} b={b}");
            }
        }
    }

    #[test]
    fn mask_select_is_correct() {
        let pick = |v: i32| {
            let mask = -((v >= 50) as i64);
            (v as i64) & mask
        };
        assert_eq!(pick(49), 0);
        assert_eq!(pick(50), 50);
        assert_eq!(pick(99), 99);
    }
}
