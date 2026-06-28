// ============================================================================
// 01 — Ownership & borrowing: the idea the whole language is built on
// Run:  cargo run --example 01_ownership_and_borrowing
// ----------------------------------------------------------------------------
// Rust has no garbage collector and no manual free(). Instead every value has a
// single OWNER; when the owner goes out of scope the value is dropped. You then
// lend access out as BORROWS, and the compiler enforces one rule at compile time:
//
//     at any moment, either ONE mutable borrow (&mut T) XOR any number of
//     shared borrows (&T) — never both.
//
// That single rule is what makes Rust memory-safe AND data-race-free with zero
// runtime cost. This file shows move, copy, shared/mutable borrows, and why the
// borrow checker rejects the classic aliasing bug.
// ============================================================================

fn main() {
    move_semantics();
    copy_types();
    borrowing();
    mutable_borrow_excludes_others();
}

// --- Move: ownership transfers, the source is no longer usable ---------------
fn move_semantics() {
    let s1 = String::from("hello"); // s1 owns heap-allocated bytes
    let s2 = s1; // MOVE: ownership transfers to s2
                 // println!("{s1}");                // ← compile error: s1 was moved out of
    println!("[move] s2 = {s2}  (s1 is no longer valid)");

    // To keep both, ask for a deep copy explicitly. Rust never hides a clone.
    let s3 = s2.clone();
    println!("[move] cloned: s2={s2}, s3={s3}");
} // s2 and s3 dropped here, their buffers freed — deterministically, no GC.

// --- Copy: small, plain-old-data types are duplicated, not moved -------------
fn copy_types() {
    let a = 5; // i32 is `Copy`
    let b = a; // bit-copy, both stay valid
    println!("[copy] a={a}, b={b}  (i32 is Copy, so no move)");
}

// --- Borrowing: lend access without giving up ownership ----------------------
fn borrowing() {
    let mut tally = String::from("trade");

    // Shared borrows (&T): read-only, you can have many at once.
    let len = char_len(&tally);
    println!("[borrow] '{tally}' has {len} chars (shared borrow, owner kept)");

    // Mutable borrow (&mut T): exclusive, lets the callee mutate in place.
    append_filled(&mut tally);
    println!("[borrow] after &mut: '{tally}'");
}

fn char_len(s: &str) -> usize {
    // &str: a borrowed view, doesn't own
    s.chars().count()
}

fn append_filled(s: &mut String) {
    // &mut String: exclusive access
    s.push_str("-filled");
}

// --- The rule with teeth: &mut excludes every other borrow -------------------
fn mutable_borrow_excludes_others() {
    let mut v = vec![1, 2, 3];

    // This is the bug Rust prevents at COMPILE time: holding a reference into a
    // vector while also mutating (and possibly reallocating) it.
    //
    //     let first = &v[0];          // shared borrow of an element
    //     v.push(4);                  // &mut borrow to grow → may reallocate
    //     println!("{first}");        // ← would be a dangling read in C++
    //
    // The borrow checker rejects the above. The fix: finish reading first.
    let first = v[0]; // copy the value out (i32 is Copy)
    v.push(4); // now mutation is fine, no live borrow
    println!("[alias] first={first}, v={v:?}  (no dangling reference possible)");
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn borrow_does_not_consume() {
        let s = String::from("abc");
        assert_eq!(char_len(&s), 3);
        assert_eq!(s, "abc"); // still owned & usable after the borrow
    }

    #[test]
    fn mutable_borrow_mutates_in_place() {
        let mut s = String::from("x");
        append_filled(&mut s);
        assert_eq!(s, "x-filled");
    }
}
