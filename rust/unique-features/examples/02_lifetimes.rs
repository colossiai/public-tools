// ============================================================================
// 02 — Lifetimes: references that provably can't outlive their data
// Run:  cargo run --example 02_lifetimes
// ----------------------------------------------------------------------------
// C++:  a reference/pointer can easily outlive what it points to (return a ref
//       to a local, keep a pointer into a vector that reallocates) — compiles
//       fine, crashes (or worse) later.
// Java/Go: the GC keeps anything still referenced alive, so this bug can't
//       happen — but you never get to express "this borrow is temporary."
//
// Rust has NO analog in your three languages: lifetimes are compile-time
// LABELS on references that let the borrow checker prove no reference ever
// points to freed data. They generate zero runtime code — pure static proof.
// ============================================================================

fn main() {
    elision_makes_the_common_case_invisible();
    explicit_lifetime_relationship();
    struct_holding_a_reference();
    dangling_is_rejected();
}

// --- 90% of the time lifetimes are INFERRED (elided) — you write nothing -----
fn elision_makes_the_common_case_invisible() {
    let s = String::from("  trimmed  ");
    println!("[elision] {:?}", first_word(&s)); // no lifetime syntax needed
}
fn first_word(s: &str) -> &str {
    s.split_whitespace().next().unwrap_or("")
}

// --- When two references meet, you name the relationship: 'a ----------------
// "the returned reference lives no longer than BOTH inputs." The compiler now
// refuses any call site that would let the result dangle.
fn longest<'a>(a: &'a str, b: &'a str) -> &'a str {
    if a.len() >= b.len() {
        a
    } else {
        b
    }
}
fn explicit_lifetime_relationship() {
    let x = String::from("longer string");
    let y = String::from("short");
    println!("[explicit] longest = {}", longest(&x, &y));
}

// --- A struct that borrows must declare it can't outlive what it points to ---
struct Excerpt<'a> {
    part: &'a str, // Excerpt<'a> may not outlive the &str it holds
}
fn struct_holding_a_reference() {
    let novel = String::from("Call me Ishmael. Some years ago...");
    let first_sentence = novel.split('.').next().expect("has a sentence");
    let e = Excerpt { part: first_sentence };
    println!("[struct] excerpt = {:?}", e.part);
    // `novel` must outlive `e`; drop it too early and this fails to compile.
}

// --- The bug C++ compiles and Rust refuses -----------------------------------
fn dangling_is_rejected() {
    // fn dangle() -> &String {     // ← no lifetime possible; won't compile
    //     let local = String::from("gone at end of scope");
    //     &local                    // returning a ref to a value about to drop
    // }
    // The C++ equivalent (`const std::string& dangle()` returning a local) is
    // accepted by the compiler and is undefined behavior at runtime.
    println!("[dangling] the commented dangle() is a compile error, not a crash");
}
