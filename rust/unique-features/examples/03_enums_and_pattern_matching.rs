// ============================================================================
// 03 — Enums (sum types), exhaustive match, no null, no exceptions
// Run:  cargo run --example 03_enums_and_pattern_matching
// ----------------------------------------------------------------------------
// C++:  std::variant + std::visit is the analog, but verbose and no built-in
//       exhaustiveness. null pointers and exceptions are the norm.
// Java:  sealed interfaces + pattern-matching switch arrived recently; `null`
//       and checked/unchecked exceptions are pervasive.
// Go:    no sum types at all (interface{} + type switch, no exhaustiveness);
//       errors are values but nil is everywhere.
//
// Rust enums are true ALGEBRAIC data types: each variant can carry different
// data, and `match` must handle every variant (compile error otherwise). This
// replaces BOTH of the classic footguns:
//   • no null           → Option<T>  (Some / None)
//   • no exceptions      → Result<T, E> (Ok / Err) + the `?` operator
// ============================================================================

fn main() {
    sum_type_with_data();
    no_null_option();
    no_exceptions_result();
}

// --- A variant can carry payload; match binds and destructures it ------------
enum Shape {
    Circle { radius: f64 },
    Rect { w: f64, h: f64 },
    Point, // no data
}
fn area(s: &Shape) -> f64 {
    match s {
        Shape::Circle { radius } => std::f64::consts::PI * radius * radius,
        Shape::Rect { w, h } => w * h,
        Shape::Point => 0.0,
        // Add a variant above and EVERY match like this fails to compile until
        // you handle it. No silent fall-through, no forgotten case.
    }
}
fn sum_type_with_data() {
    let shapes = [
        Shape::Circle { radius: 2.0 },
        Shape::Rect { w: 3.0, h: 4.0 },
        Shape::Point,
    ];
    for s in &shapes {
        println!("[enum] area = {:.2}", area(s));
    }
}

// --- Option<T>: the absence of a value is in the type, not a null pointer -----
fn find_even(xs: &[i32]) -> Option<i32> {
    for &x in xs {
        if x % 2 == 0 {
            return Some(x);
        }
    }
    None
}
fn no_null_option() {
    let xs = [1, 3, 5, 8, 9];
    match find_even(&xs) {
        Some(n) => println!("[option] first even = {n}"),
        None => println!("[option] none found"),
    }
    // You CANNOT forget the None case — the compiler makes you address it.
    // Ergonomic combinators exist too:
    let doubled = find_even(&xs).map(|n| n * 2).unwrap_or(-1);
    println!("[option] doubled-or-default = {doubled}");
}

// --- Result<T,E> + `?`: errors are values that propagate without exceptions --
#[derive(Debug)]
enum ParseErr {
    Empty,
    NotANumber(String),
}
fn parse_positive(s: &str) -> Result<u32, ParseErr> {
    if s.is_empty() {
        return Err(ParseErr::Empty);
    }
    // `?` unwraps Ok, or converts+returns Err early — like a checked, explicit,
    // stack-unwind-free exception that's visible in the signature.
    let n: i64 = s
        .parse()
        .map_err(|_| ParseErr::NotANumber(s.to_string()))?;
    Ok(n.max(0) as u32)
}
fn no_exceptions_result() {
    for input in ["42", "", "oops"] {
        match parse_positive(input) {
            Ok(n) => println!("[result] {input:?} -> {n}"),
            Err(ParseErr::Empty) => println!("[result] {input:?} -> error: empty"),
            Err(ParseErr::NotANumber(s)) => {
                println!("[result] {input:?} -> error: {s:?} is not a number")
            }
        }
    }
}
