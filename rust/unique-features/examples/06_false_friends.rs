// ============================================================================
// 06 — False friends: things that LOOK familiar but behave differently
// Run:  cargo run --example 06_false_friends
// ----------------------------------------------------------------------------
// These match instincts from C++/Java/Go that misfire in Rust. Learn the
// difference, not the feature.
// ============================================================================

fn main() {
    move_is_destructive();
    no_inheritance_use_composition();
    integer_overflow_is_checked();
    everything_is_an_expression();
    shadowing_not_mutation();
    deterministic_drop();
}

// --- (a) `move` is destructive — unlike C++'s "valid but unspecified" --------
fn move_is_destructive() {
    let a = String::from("owned");
    let b = a; // a is now statically INVALID (not just "moved-from but usable")
    // In C++, `auto b = std::move(a);` leaves `a` in a usable state, so
    // reading it compiles and is a subtle bug. In Rust reading `a` here is a
    // hard compile error — the whole class of use-after-move bugs is gone.
    println!("[move] b = {b}  (a is unusable, checked at compile time)");
}

// --- (b) No inheritance. Reuse via composition + traits ----------------------
// There is no `class Dog extends Animal`. You compose data and share behavior
// through traits (lesson 04). "Is-a" hierarchies become "has-a" + trait impls.
trait Speak {
    fn speak(&self) -> String;
}
struct Dog;
impl Speak for Dog {
    fn speak(&self) -> String {
        "woof".into()
    }
}
fn no_inheritance_use_composition() {
    println!("[no-inherit] {}", Dog.speak());
}

// --- (c) Integer overflow PANICS in debug (wraps silently in C/Java/Go) ------
fn integer_overflow_is_checked() {
    let x: u8 = 250;
    // let y = x + 10;              // ← debug build: PANIC "attempt to add with overflow"
    //                             //   release build: wraps to 4 (documented)
    // Be explicit about which behavior you want:
    println!(
        "[overflow] checked={:?}  wrapping={}  saturating={}",
        x.checked_add(10),      // None  (overflow signalled as a value)
        x.wrapping_add(10),     // 4     (opt into wraparound)
        x.saturating_add(10),   // 255   (clamp to max)
    );
}

// --- (d) `if`, `match`, and blocks are EXPRESSIONS, not just statements ------
fn everything_is_an_expression() {
    let n = 7;
    // No ternary operator needed — `if` yields a value:
    let parity = if n % 2 == 0 { "even" } else { "odd" };
    // A block's last expression (no semicolon) is its value:
    let squared = {
        let t = n;
        t * t
    };
    println!("[expr] {n} is {parity}, squared = {squared}");
}

// --- (e) `let` shadowing is not mutation, and bindings are immutable by default
fn shadowing_not_mutation() {
    let x = "42"; // &str
    let x = x.parse::<i32>().unwrap(); // NEW binding named x, different type
    let x = x * 2; // shadow again
    // Variables are immutable unless you write `let mut`. Shadowing lets you
    // reuse a name (even changing its type) without `mut` — a fresh binding
    // each time, not an in-place write.
    println!("[shadow] final x = {x} (i32), via three separate bindings");
}

// --- (f) Deterministic destruction: Drop is RAII, but memory-safe ------------
struct Guard(&'static str);
impl Drop for Guard {
    fn drop(&mut self) {
        // Runs automatically at end of scope, in reverse declaration order —
        // like a C++ destructor, but the borrow checker guarantees no
        // use-after-free or double-free can reach it.
        println!("[drop] releasing {}", self.0);
    }
}
fn deterministic_drop() {
    let _first = Guard("first");
    let _second = Guard("second");
    println!("[drop] scope ending; watch the reverse-order cleanup:");
} // "second" drops, then "first" — deterministic, no GC, no finalizer surprises.
