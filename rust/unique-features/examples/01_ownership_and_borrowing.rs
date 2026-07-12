// ============================================================================
// 01 — Ownership & the borrow checker: the feature the language is built on
// Run:  cargo run --example 01_ownership_and_borrowing
// ----------------------------------------------------------------------------
// C++:  RAII + move semantics are the closest analog — but a moved-from object
//       is still *usable* (valid-but-unspecified), so use-after-move compiles
//       and is a lurking bug. There is no borrow checker; dangling refs, double
//       frees, and data races are all writable.
// Java/Go: a garbage collector manages memory; you never think about ownership,
//       but you pay GC latency and can still alias-mutate freely.
//
// Rust has NO garbage collector and NO manual free(). Every value has exactly
// ONE owner; when the owner leaves scope the value is dropped (freed)
// deterministically. You lend access via BORROWS, and the compiler enforces:
//
//     at any instant: ONE mutable borrow (&mut T)  XOR  many shared (&T).
//
// That one rule delivers memory safety AND data-race freedom at zero runtime
// cost. Below: destructive moves, Copy types, borrows, and the aliasing rule.
// ============================================================================

fn main() {
    destructive_move();
    copy_types();
    borrows();
    aliasing_xor_mutation();
}

// --- Move is DESTRUCTIVE: the source becomes unusable (unlike C++) -----------
fn destructive_move() {
    let s1 = String::from("hello"); // s1 owns the heap buffer
    let s2 = s1; // MOVE: ownership transfers; s1 is statically dead now
    // println!("{s1}");            // ← compile error: value borrowed after move
    println!("[move] s2 = {s2}   (s1 no longer exists — enforced at compile time)");

    // Rust never deep-copies implicitly. You ask, explicitly:
    let s3 = s2.clone();
    println!("[move] explicit clone: s2={s2}, s3={s3}");
} // s2, s3 dropped here — buffers freed deterministically, no GC pause.

// --- Copy types: small plain-old-data is bit-copied, not moved ---------------
fn copy_types() {
    let a = 5; // i32 implements Copy
    let b = a; // copy; both stay valid
    println!("[copy] a={a}, b={b}  (Copy types are duplicated, not moved)");
}

// --- Borrows: lend without giving up ownership -------------------------------
fn borrows() {
    let mut v = vec![1, 2, 3];
    let len = length(&v); // shared borrow &v
    push_42(&mut v); // exclusive borrow &mut v (only after the shared one ended)
    println!("[borrow] len was {len}, now v = {v:?}");
}
fn length(v: &Vec<i32>) -> usize {
    v.len()
}
fn push_42(v: &mut Vec<i32>) {
    v.push(42);
}

// --- The aliasing rule: shared XOR mutable, checked at compile time ----------
fn aliasing_xor_mutation() {
    let mut data = vec![10, 20, 30];

    let first = &data[0]; // shared borrow begins
    // data.push(40);      // ← compile error: cannot mutate while `first` is borrowed
    println!("[alias] read through shared borrow: {first}");
    // `first` is last used above, so the borrow ends here (non-lexical lifetimes).

    data.push(40); // now exclusive mutation is allowed
    println!("[alias] mutated after the shared borrow ended: {data:?}");
    // This is exactly the iterator-invalidation / dangling-pointer class of bug
    // that C++ lets you write and Rust rejects before the program runs.
}
