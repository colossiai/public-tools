// ============================================================================
// 05 — Fearless concurrency: data races are a COMPILE error
// Run:  cargo run --example 05_fearless_concurrency
// ----------------------------------------------------------------------------
// C++:  sharing mutable data across threads without synchronization is
//       undefined behavior — and compiles silently.
// Go:   goroutines + channels are lovely, but a plain shared variable written
//       from two goroutines is a DATA RACE the compiler won't catch (you need
//       `go test -race` at runtime to maybe find it).
// Java: `synchronized`/volatile exist, but forgetting them compiles fine and
//       races at runtime.
//
// Rust extends the SAME ownership rules from lesson 01 across threads. Two
// auto-derived marker traits do the work at compile time:
//   • Send — safe to MOVE ownership to another thread.
//   • Sync — safe to SHARE (&T) across threads.
// If a type isn't thread-safe (e.g. Rc, RefCell), the compiler refuses to send
// or share it. A data race becomes a type error, not a Heisenbug.
// ============================================================================

use std::sync::{Arc, Mutex};
use std::thread;

fn main() {
    move_ownership_into_a_thread();
    share_with_arc_mutex();
    the_bug_that_wont_compile();
}

// --- Ownership moves into the spawned thread; the compiler tracks it ---------
fn move_ownership_into_a_thread() {
    let data = vec![1, 2, 3, 4];
    let handle = thread::spawn(move || {
        // `move` transfers ownership of `data` into the thread — now nobody
        // else can touch it, so there's nothing to race on.
        let sum: i32 = data.iter().sum();
        sum
    });
    // println!("{data:?}");  // ← compile error: `data` was moved into the thread
    let sum = handle.join().expect("thread panicked");
    println!("[move] thread computed sum = {sum}");
}

// --- Shared mutable state: Arc (shared ownership) + Mutex (exclusive access) --
// The types FORCE you to lock before touching shared data. Forgetting to lock
// isn't possible — the data is only reachable through the Mutex guard.
fn share_with_arc_mutex() {
    let counter = Arc::new(Mutex::new(0u64));
    let mut handles = Vec::new();

    for _ in 0..8 {
        let c = Arc::clone(&counter);
        handles.push(thread::spawn(move || {
            for _ in 0..10_000 {
                let mut n = c.lock().expect("poisoned"); // exclusive access
                *n += 1;
            } // guard drops here → lock released automatically (RAII)
        }));
    }
    for h in handles {
        h.join().expect("thread panicked");
    }
    println!("[shared] final counter = {}", *counter.lock().unwrap()); // 80000
}

// --- The compile-time safety net ---------------------------------------------
fn the_bug_that_wont_compile() {
    // use std::rc::Rc;
    // let shared = Rc::new(0);          // Rc is NOT Send/Sync (non-atomic refcount)
    // thread::spawn(move || {
    //     println!("{}", shared);        // ← compile error:
    // });                                //   `Rc<i32>` cannot be sent between threads safely
    //
    // Swap Rc→Arc and it compiles. The type system draws the line between
    // single-threaded and shareable for you — the Go/C++/Java compilers don't.
    println!("[safety] sending a non-Send type across threads is a compile error");
}
