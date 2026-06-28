// ============================================================================
// 13 — Declarative macros: code that writes code (macro_rules!)
// Run:  cargo run --example 13_macros
// ----------------------------------------------------------------------------
// Macros operate on the SYNTAX TREE before type-checking, so they can do things
// functions can't: take a variable number of arguments of mixed types, generate
// items (structs/impls), and capture syntax fragments. `macro_rules!` matches
// token patterns and expands to replacement code — hygienic (won't capture your
// local variables) and checked when expanded.
//
// Fragment specifiers you'll see: $x:expr (expression), :ident, :ty (type),
// :tt (token tree), :pat, :literal. Repetition: $(...)* / $(...),+  with a
// separator and a count (* = 0+, + = 1+).
// ============================================================================

// The `myvec!` demo deliberately expands to `let mut v = Vec::new(); v.push(..)`
// to show repetition — that *is* the lesson, so silence clippy's suggestion to
// use a vec! literal (which is exactly what we're reimplementing).
#![allow(clippy::vec_init_then_push)]

// --- A variadic max!: at least one expr, comma-separated ----------------------
macro_rules! max {
    ($first:expr $(, $rest:expr)* $(,)?) => {{
        // `mut` is unused in the single-argument case (no $rest to compare) —
        // that's expected for a variadic macro, so silence the lint locally.
        #[allow(unused_mut)]
        let mut m = $first;
        $( if $rest > m { m = $rest; } )*   // expands once per $rest
        m
    }};
}

// --- Reimplement a tiny vec!-style builder ------------------------------------
macro_rules! myvec {
    () => { Vec::new() };
    ($($x:expr),+ $(,)?) => {{
        let mut v = Vec::new();
        $( v.push($x); )+
        v
    }};
    // "N copies of x" form: myvec![0; 3]
    ($x:expr ; $n:expr) => {{
        let mut v = Vec::new();
        for _ in 0..$n { v.push($x); }
        v
    }};
}

// --- A hashmap! literal: key => value pairs -----------------------------------
macro_rules! hashmap {
    ($($key:expr => $val:expr),* $(,)?) => {{
        let mut m = std::collections::HashMap::new();
        $( m.insert($key, $val); )*
        m
    }};
}

// --- Macros can generate ITEMS: stamp out a struct + a constructor ------------
macro_rules! make_newtype {
    ($name:ident, $inner:ty) => {
        #[derive(Debug, Clone, Copy, PartialEq)]
        struct $name($inner);
        impl $name {
            fn get(self) -> $inner {
                self.0
            }
        }
    };
}
make_newtype!(Price, i64);
make_newtype!(Qty, u32);

fn main() {
    println!("max!(3, 7, 2, 9, 5) = {}", max!(3, 7, 2, 9, 5));
    println!("max!(42)            = {}", max!(42));

    let v: Vec<i32> = myvec![1, 2, 3, 4];
    let zeros: Vec<i32> = myvec![0; 3];
    println!("myvec![1,2,3,4] = {v:?}, myvec![0;3] = {zeros:?}");

    let m = hashmap! { "AAA" => 100, "BBB" => 250 };
    println!("hashmap! len = {}, AAA = {}", m.len(), m["AAA"]);

    let p = Price(1234);
    let q = Qty(10);
    println!(
        "generated newtypes: {p:?}.get()={}, {q:?}.get()={}",
        p.get(),
        q.get()
    );
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn max_macro() {
        assert_eq!(max!(1), 1);
        assert_eq!(max!(1, 9, 3), 9);
        assert_eq!(max!(5, 4, 3, 2, 1), 5);
    }

    #[test]
    fn myvec_forms() {
        let a: Vec<i32> = myvec![];
        assert!(a.is_empty());
        assert_eq!(myvec![1, 2, 3], vec![1, 2, 3]);
        assert_eq!(myvec![7; 3], vec![7, 7, 7]);
    }

    #[test]
    fn hashmap_macro() {
        let m = hashmap! { 1 => "a", 2 => "b" };
        assert_eq!(m.len(), 2);
        assert_eq!(m[&1], "a");
    }

    #[test]
    fn generated_newtype_works() {
        assert_eq!(Price(5).get(), 5);
        assert_eq!(Qty(9), Qty(9));
    }
}
