// ============================================================================
// 03 — Error handling: Result, the `?` operator, and your own error type
// Run:  cargo run --example 03_error_handling
// ----------------------------------------------------------------------------
// Rust has no exceptions for recoverable errors. Fallible functions return
// `Result<T, E>`, and the caller MUST acknowledge the error (the type won't let
// them ignore it). The `?` operator makes propagation ergonomic: it returns the
// error early, converting it via `From` on the way out. `panic!` is reserved for
// bugs / unrecoverable states, not for control flow.
// ============================================================================

use std::fmt;

// A domain error as an enum: each failure mode is a distinct, matchable variant.
#[derive(Debug, PartialEq)]
enum ParseOrderError {
    MissingField(&'static str),
    BadInt(String),
    InvalidSide(String),
}

// Implementing Display + Error makes it a first-class error usable with `?`,
// `Box<dyn Error>`, `anyhow`, logging, etc.
impl fmt::Display for ParseOrderError {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            ParseOrderError::MissingField(name) => write!(f, "missing field: {name}"),
            ParseOrderError::BadInt(s) => write!(f, "not an integer: {s:?}"),
            ParseOrderError::InvalidSide(s) => write!(f, "invalid side: {s:?} (want B/S)"),
        }
    }
}
impl std::error::Error for ParseOrderError {}

// `From<std::num::ParseIntError>` lets `?` auto-convert the std error into ours.
impl From<std::num::ParseIntError> for ParseOrderError {
    fn from(e: std::num::ParseIntError) -> Self {
        ParseOrderError::BadInt(e.to_string())
    }
}

#[derive(Debug, PartialEq)]
struct Order {
    side: char,
    price: u64,
    qty: u32,
}

// Parse "B,100,10" → Order. Note every `?` either unwraps Ok or returns Err,
// converting the error type automatically via the `From` impls above.
fn parse_order(line: &str) -> Result<Order, ParseOrderError> {
    let mut parts = line.split(',');
    let side_s = parts.next().ok_or(ParseOrderError::MissingField("side"))?;
    let price_s = parts.next().ok_or(ParseOrderError::MissingField("price"))?;
    let qty_s = parts.next().ok_or(ParseOrderError::MissingField("qty"))?;

    let side = match side_s.trim() {
        "B" => 'B',
        "S" => 'S',
        other => return Err(ParseOrderError::InvalidSide(other.to_string())),
    };
    let price: u64 = price_s.trim().parse()?; // ParseIntError → ParseOrderError via From
    let qty: u32 = qty_s.trim().parse()?;
    Ok(Order { side, price, qty })
}

// Returning `Box<dyn Error>` lets a function bubble up *any* error type — handy
// at application boundaries (main, request handlers) where the concrete type
// doesn't matter, only that something failed.
fn total_notional(lines: &[&str]) -> Result<u64, Box<dyn std::error::Error>> {
    let mut sum = 0u64;
    for line in lines {
        let o = parse_order(line)?; // ParseOrderError coerces into Box<dyn Error>
        sum += o.price * o.qty as u64;
    }
    Ok(sum)
}

fn main() {
    for line in ["B,100,10", "S,250,4", "X,1,1", "B,oops,1", "B,100"] {
        match parse_order(line) {
            Ok(o) => println!("ok:  {line:<10} -> {o:?}"),
            Err(e) => println!("err: {line:<10} -> {e}"),
        }
    }

    match total_notional(&["B,100,10", "S,250,4"]) {
        Ok(n) => println!("total notional = {n}"),
        Err(e) => println!("aggregation failed: {e}"),
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn parses_valid() {
        assert_eq!(
            parse_order("B,100,10"),
            Ok(Order {
                side: 'B',
                price: 100,
                qty: 10
            })
        );
    }

    #[test]
    fn reports_specific_errors() {
        assert_eq!(
            parse_order("X,1,1"),
            Err(ParseOrderError::InvalidSide("X".into()))
        );
        assert_eq!(
            parse_order("B,100"),
            Err(ParseOrderError::MissingField("qty"))
        );
        assert!(matches!(
            parse_order("B,nope,1"),
            Err(ParseOrderError::BadInt(_))
        ));
    }

    #[test]
    fn aggregates_or_fails() {
        assert_eq!(total_notional(&["B,100,10", "S,250,4"]).unwrap(), 2000);
        assert!(total_notional(&["B,100,10", "bad"]).is_err());
    }
}
