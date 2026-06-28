// ============================================================================
// 07 — Closures: Fn, FnMut, FnOnce, and how capture works
// Run:  cargo run --example 07_closures
// ----------------------------------------------------------------------------
// A closure is an anonymous function that can CAPTURE its environment. Which of
// the three closure traits it implements is decided by HOW it uses captures:
//
//   * Fn      — captures by shared ref (&). Callable many times, reads only.
//   * FnMut   — captures by mutable ref (&mut). Callable many times, mutates.
//   * FnOnce  — captures by value (move) and consumes them. Callable once.
//
// Every closure is FnOnce; some are also FnMut; some are also Fn (a hierarchy).
// `move` forces capture-by-value, which is how you hand state to another thread
// or return a closure that outlives the current frame.
// ============================================================================

// Accept any read-only callable: bound `Fn(i64) -> i64`.
fn apply_twice<F: Fn(i64) -> i64>(f: F, x: i64) -> i64 {
    f(f(x))
}

// Accept a mutating callable. `FnMut` because the closure changes captured state.
fn run_n_times<F: FnMut()>(mut f: F, n: usize) {
    for _ in 0..n {
        f();
    }
}

// Return a closure that OWNS its captured state. `impl Fn` hides the unnameable
// closure type; `move` transfers `offset` into the returned closure so it can
// outlive this function.
fn make_adder(offset: i64) -> impl Fn(i64) -> i64 {
    move |x| x + offset
}

// A boxed closure can be stored in structs / vectors when you need a named field
// type or heterogeneous callables (same trick as `dyn Trait` in demo 06).
type Pricer = Box<dyn Fn(f64) -> f64>; // alias keeps the signatures readable
fn pricer_table() -> Vec<(&'static str, Pricer)> {
    let fee = 0.001;
    vec![
        ("with_fee", Box::new(move |p| p * (1.0 + fee))), // captures `fee` by move
        ("half", Box::new(|p| p / 2.0)),
        ("double", Box::new(|p| p * 2.0)),
    ]
}

fn main() {
    // Fn: pure, reusable.
    println!("apply_twice(+3): {}", apply_twice(|x| x + 3, 10)); // 16

    // FnMut: closure mutates captured `count`.
    let mut count = 0;
    run_n_times(|| count += 1, 5);
    println!("FnMut ran, count = {count}");

    // FnOnce: closure consumes a captured String (moves it out), so it's callable
    // only once. Calling it twice would not compile.
    let greeting = String::from("hello");
    let consume = move || greeting + " world"; // moves & consumes `greeting`
    println!("FnOnce produced: {}", consume());

    // Returned closure that outlives its maker.
    let add10 = make_adder(10);
    println!("add10(5) = {}", add10(5));

    // Closures shine with iterators (demo 04) — here capturing an external param.
    let threshold = 100;
    let big: Vec<i64> = (90..=110).filter(|&n| n > threshold).collect();
    println!("> {threshold}: {big:?}");

    // Stored, heterogeneous closures.
    for (name, f) in pricer_table() {
        println!("  {name:<9}(100.0) = {:.3}", f(100.0));
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn fn_bound_composes() {
        assert_eq!(apply_twice(|x| x * 2, 3), 12); // 3 -> 6 -> 12
    }

    #[test]
    fn fnmut_accumulates() {
        let mut total = 0;
        run_n_times(|| total += 2, 4);
        assert_eq!(total, 8);
    }

    #[test]
    fn returned_closure_captures_by_value() {
        let add = make_adder(100);
        assert_eq!(add(1), 101);
        assert_eq!(add(2), 102); // still callable: it's Fn, not FnOnce
    }
}
