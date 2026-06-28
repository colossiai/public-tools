//! # zero_to_expert
//!
//! A progressive tour of Rust, from the borrow checker up to async executors,
//! `unsafe` abstractions and zero-cost type-state APIs.
//!
//! The teaching content lives entirely in [`examples/`](https://doc.rust-lang.org/cargo/guide/project-layout.html):
//! each file is self-contained, heavily commented, prints what it demonstrates,
//! and carries its own `#[test]`s. This crate root is intentionally almost empty.
//!
//! ```sh
//! cargo run --example 01_ownership_and_borrowing
//! cargo test --examples          # run the embedded tests across all demos
//! ```

/// A tiny formatting helper used by some demos to title their output sections.
/// Kept here so the examples can stay focused on the concept being taught.
pub fn section(title: &str) {
    println!("\n=== {title} ===");
}
