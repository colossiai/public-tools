// ============================================================================
// 12 — Unsafe Rust & FFI: the escape hatch, and how to wrap it safely
// Run:  cargo run --example 12_unsafe_and_ffi
// ----------------------------------------------------------------------------
// `unsafe` does NOT turn off the borrow checker. It unlocks five extra powers the
// compiler can't verify for you:
//   1. dereference a raw pointer            4. implement an unsafe trait
//   2. call an unsafe / extern "C" function 5. access a mutable static / union
//   3. access fields of a union
//
// The expert discipline: keep `unsafe` BLOCKS tiny, uphold the documented
// invariants, and expose a SAFE abstraction so callers never write `unsafe`.
// `std` itself is exactly this — safe APIs over unsafe internals.
// ============================================================================

use std::mem::MaybeUninit;

// --- 1. A safe API over unsafe internals: reimplement slice::split_at_mut -----
// You cannot write this in safe Rust: it hands out TWO &mut into one slice, and
// the borrow checker can't see that the halves are disjoint. With a raw-pointer
// `unsafe` block (and a checked precondition) we prove it, then expose it safely.
fn split_at_mut(slice: &mut [i32], mid: usize) -> (&mut [i32], &mut [i32]) {
    let len = slice.len();
    assert!(mid <= len, "mid out of bounds"); // uphold the invariant up front
    let ptr = slice.as_mut_ptr();
    // SAFETY: `mid <= len` (asserted), so both ranges are in-bounds and the two
    // resulting slices cover disjoint regions → no aliasing &mut.
    unsafe {
        (
            std::slice::from_raw_parts_mut(ptr, mid),
            std::slice::from_raw_parts_mut(ptr.add(mid), len - mid),
        )
    }
}

// --- 2. MaybeUninit: build an array without zero-initializing it first --------
// Useful in hot paths where you'll write every slot anyway and want to skip the
// redundant zeroing. Reading an uninit slot is UB — so we fill all of them.
fn squares_uninit<const N: usize>() -> [u64; N] {
    let mut arr: [MaybeUninit<u64>; N] = unsafe { MaybeUninit::uninit().assume_init() };
    for (i, slot) in arr.iter_mut().enumerate() {
        slot.write((i * i) as u64); // initialize every element
    }
    // SAFETY: every element was written above, so the array is fully initialized.
    unsafe { std::mem::transmute_copy(&arr) }
}

// --- 3. FFI: call into C. `extern "C"` declares the foreign ABI; the call is
// unsafe because the compiler can't check the foreign side. `abs` is in libc,
// linked automatically. A `#[repr(C)]` struct guarantees a C-compatible layout.
extern "C" {
    fn abs(input: i32) -> i32;
}

#[repr(C)]
#[derive(Debug)]
struct CPoint {
    x: i32,
    y: i32,
}

fn c_abs(n: i32) -> i32 {
    // SAFETY: `abs` is a pure libc function with no preconditions on `n`.
    unsafe { abs(n) }
}

fn main() {
    // Safe-wrapped unsafe: caller writes zero `unsafe`.
    let mut data = [1, 2, 3, 4, 5, 6];
    let (lo, hi) = split_at_mut(&mut data, 3);
    lo.iter_mut().for_each(|x| *x *= 10);
    hi.iter_mut().for_each(|x| *x += 100);
    println!("[split_at_mut] {data:?}");

    let sq: [u64; 6] = squares_uninit();
    println!("[MaybeUninit] squares = {sq:?}");

    println!("[FFI] libc abs(-42) = {}", c_abs(-42));

    let p = CPoint { x: -3, y: 7 };
    println!(
        "[repr(C)] {p:?}  size={} (C-compatible layout)",
        std::mem::size_of::<CPoint>()
    );
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn split_is_disjoint_and_complete() {
        let mut v = [1, 2, 3, 4];
        let (a, b) = split_at_mut(&mut v, 2);
        a[0] = 10;
        b[1] = 40;
        assert_eq!(v, [10, 2, 3, 40]);
    }

    #[test]
    #[should_panic(expected = "out of bounds")]
    fn split_checks_bounds() {
        let mut v = [1, 2, 3];
        let _ = split_at_mut(&mut v, 4);
    }

    #[test]
    fn uninit_array_is_fully_written() {
        assert_eq!(squares_uninit::<5>(), [0, 1, 4, 9, 16]);
    }

    #[test]
    fn ffi_abs_matches_std() {
        assert_eq!(c_abs(-7), 7);
        assert_eq!(c_abs(7), 7);
    }
}
