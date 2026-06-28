// ============================================================================
// 09 — Smart pointers: Box, Rc, RefCell, Weak — ownership beyond the basics
// Run:  cargo run --example 09_smart_pointers
// ----------------------------------------------------------------------------
// The borrow checker's "one owner" / "&mut XOR &" rules are checked at compile
// time. Sometimes you need patterns those static rules can't express directly:
//
//   * Box<T>      — single owner, value on the heap. Enables recursive types and
//                   moving large values cheaply (move a pointer, not the bytes).
//   * Rc<T>       — many owners, shared ownership via reference counting
//                   (single-threaded). Drops the value when the last Rc dies.
//   * RefCell<T>  — moves the borrow check to RUNTIME, giving "interior
//                   mutability": mutate through a shared &. Panics on violation.
//   * Weak<T>     — a non-owning Rc that doesn't keep the value alive; breaks
//                   reference cycles (which would otherwise leak).
//
// Rc<RefCell<T>> = "shared, mutable, single-threaded" — the GC-language default,
// here made explicit and opt-in.
// ============================================================================

use std::cell::RefCell;
use std::rc::{Rc, Weak};

// Box enables a recursive type: a node can't contain itself by value (infinite
// size), but it can contain a Box<Self> (a pointer is a fixed size).
#[derive(Debug)]
enum Expr {
    Num(i64),
    Add(Box<Expr>, Box<Expr>),
    Mul(Box<Expr>, Box<Expr>),
}

fn eval(e: &Expr) -> i64 {
    match e {
        Expr::Num(n) => *n,
        Expr::Add(a, b) => eval(a) + eval(b),
        Expr::Mul(a, b) => eval(a) * eval(b),
    }
}

// A shared, mutable counter: Rc gives multiple owners, RefCell allows mutation
// through the shared handle. Both handles see the same value.
fn shared_counter_demo() -> i64 {
    let counter = Rc::new(RefCell::new(0));
    let a = Rc::clone(&counter); // bumps the strong count, same allocation
    let b = Rc::clone(&counter);

    *a.borrow_mut() += 10; // runtime-checked mutable borrow
    *b.borrow_mut() += 5;
    let total = *counter.borrow();
    println!(
        "[rc/refcell] strong_count={}, total={}",
        Rc::strong_count(&counter),
        total
    );
    total
}

// A parent/child tree. Children own nothing of the parent (Weak) so there's no
// cycle: parent -> child via Rc (owning), child -> parent via Weak (non-owning).
struct Node {
    val: i64,
    parent: RefCell<Weak<Node>>,
    children: RefCell<Vec<Rc<Node>>>,
}

fn tree_demo() {
    let root = Rc::new(Node {
        val: 1,
        parent: RefCell::new(Weak::new()),
        children: RefCell::new(vec![]),
    });
    let leaf = Rc::new(Node {
        val: 2,
        parent: RefCell::new(Weak::new()),
        children: RefCell::new(vec![]),
    });

    *leaf.parent.borrow_mut() = Rc::downgrade(&root); // child -> parent (Weak)
    root.children.borrow_mut().push(Rc::clone(&leaf)); // parent -> child (Rc)

    // upgrade() turns a Weak back into an Option<Rc>: Some if still alive.
    let parent_val = leaf.parent.borrow().upgrade().map(|p| p.val);
    println!(
        "[tree] leaf {} -> parent {:?}; root strong={}, weak={}",
        leaf.val,
        parent_val,
        Rc::strong_count(&root),
        Rc::weak_count(&root)
    );
}

fn main() {
    // (2 + 3) * 4 as a heap-allocated tree.
    let expr = Expr::Mul(
        Box::new(Expr::Add(Box::new(Expr::Num(2)), Box::new(Expr::Num(3)))),
        Box::new(Expr::Num(4)),
    );
    println!("[box] eval((2+3)*4) = {}", eval(&expr));

    shared_counter_demo();
    tree_demo();
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn box_recursive_eval() {
        let e = Expr::Add(Box::new(Expr::Num(40)), Box::new(Expr::Num(2)));
        assert_eq!(eval(&e), 42);
    }

    #[test]
    fn rc_refcell_shares_mutation() {
        assert_eq!(shared_counter_demo(), 15);
    }

    #[test]
    fn refcell_double_mut_borrow_panics() {
        let c = RefCell::new(0);
        let _b1 = c.borrow_mut();
        // A second concurrent mutable borrow violates the rule at RUNTIME.
        assert!(std::panic::catch_unwind(std::panic::AssertUnwindSafe(|| {
            let _b2 = c.borrow_mut();
        }))
        .is_err());
    }
}
