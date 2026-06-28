// ============================================================================
// 08 — Lifetimes: making "this reference stays valid" a compile-time proof
// Run:  cargo run --example 08_lifetimes
// ----------------------------------------------------------------------------
// A lifetime is a region of code for which a reference is valid. The compiler
// tracks them to guarantee no reference ever outlives the data it points to
// (no dangling pointers — ever, at compile time). Most lifetimes are INFERRED
// (elision); you write them explicitly only when a function or struct relates
// multiple references and the compiler needs you to spell out the relationship.
//
// Read `<'a>` as "for some lifetime 'a". `&'a str` is "a string slice that lives
// at least as long as 'a".
// ============================================================================

// The canonical example. Returning a reference means the compiler must know
// WHICH input it borrows from. `'a` says: the result lives as long as BOTH
// inputs, so the caller may not use it past either one's end.
fn longest<'a>(a: &'a str, b: &'a str) -> &'a str {
    if a.len() >= b.len() {
        a
    } else {
        b
    }
}

// A struct that HOLDS a reference must name the lifetime: the struct cannot
// outlive the data it borrows. Here a parser borrows the input text.
struct Tokens<'a> {
    rest: &'a str,
}

impl<'a> Tokens<'a> {
    fn new(s: &'a str) -> Self {
        Tokens { rest: s.trim() }
    }

    // Returns a slice borrowing from the same `'a` input — no allocation, just
    // a window into the original string.
    fn next_token(&mut self) -> Option<&'a str> {
        if self.rest.is_empty() {
            return None;
        }
        match self.rest.find(',') {
            Some(i) => {
                let tok = &self.rest[..i];
                self.rest = self.rest[i + 1..].trim_start();
                Some(tok)
            }
            None => {
                let tok = self.rest;
                self.rest = "";
                Some(tok)
            }
        }
    }
}

// Lifetime elision: the compiler fills these in, so you DON'T write 'a here.
// (One input ref, one output ref → output borrows from the input.)
fn first_word(s: &str) -> &str {
    s.split_whitespace().next().unwrap_or("")
}

fn main() {
    let a = String::from("a longer string");
    let pick;
    {
        let b = String::from("short");
        pick = longest(&a, &b);
        println!("longest = {pick:?}"); // OK: used while both a and b are alive
    }
    // Using `pick` here would be a compile error: it might borrow `b`, now gone.

    let csv = " AAPL, MSFT ,GOOG ";
    let mut toks = Tokens::new(csv);
    let mut out = Vec::new();
    while let Some(t) = toks.next_token() {
        out.push(t.trim());
    }
    println!("tokens = {out:?}");

    println!("first_word = {:?}", first_word("hello there world"));

    // 'static is the longest lifetime: lives for the whole program. String
    // literals are &'static str (baked into the binary).
    let lit: &'static str = "I live forever";
    println!("{lit}");
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn longest_picks_longer() {
        assert_eq!(longest("aaa", "bb"), "aaa");
        assert_eq!(longest("a", "bbbb"), "bbbb");
    }

    #[test]
    fn tokenizer_borrows_input() {
        let mut t = Tokens::new("x, y ,z");
        assert_eq!(t.next_token(), Some("x"));
        assert_eq!(t.next_token(), Some("y "));
        assert_eq!(t.next_token(), Some("z"));
        assert_eq!(t.next_token(), None);
    }

    #[test]
    fn first_word_elision() {
        assert_eq!(first_word("  alpha beta"), "alpha");
        assert_eq!(first_word(""), "");
    }
}
