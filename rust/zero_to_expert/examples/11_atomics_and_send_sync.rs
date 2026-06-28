// ============================================================================
// 11 — Atomics, memory ordering, and the Send/Sync marker traits
// Run:  cargo run --example 11_atomics_and_send_sync
// ----------------------------------------------------------------------------
// Lock-free synchronization, and the two marker traits that make the whole
// concurrency story sound:
//
//   * Send  — a type is safe to MOVE to another thread.
//   * Sync  — a type is safe to SHARE (&T) across threads. (T: Sync ⇔ &T: Send.)
//
// These are AUTO traits: the compiler derives them structurally. `Rc` is neither
// (its count isn't atomic) so it can't cross threads — caught at compile time.
// `Arc`, atomics, and `Mutex` are Sync, which is why demo 10 could share them.
//
// Atomics give race-free shared counters/flags without a lock. The `Ordering`
// argument controls how surrounding memory operations may be reordered:
//   Relaxed  — only the atom itself is atomic (fine for a plain counter).
//   Acquire/Release — establish happens-before for publishing data (the lock
//   pattern). SeqCst — a single global order, the safe default when unsure.
// ============================================================================

use std::sync::atomic::{AtomicBool, AtomicU64, Ordering};
use std::sync::Arc;
use std::thread;

// A lock-free counter hammered by many threads. fetch_add is one atomic RMW;
// Relaxed is correct here because we only care about the final tally, not
// ordering relative to other memory.
fn atomic_counter(threads: usize, per_thread: u64) -> u64 {
    let counter = Arc::new(AtomicU64::new(0));
    let mut handles = vec![];
    for _ in 0..threads {
        let counter = Arc::clone(&counter);
        handles.push(thread::spawn(move || {
            for _ in 0..per_thread {
                counter.fetch_add(1, Ordering::Relaxed);
            }
        }));
    }
    for h in handles {
        h.join().unwrap();
    }
    counter.load(Ordering::Relaxed)
}

// A tiny spinlock that OWNS its data (the std::sync::Mutex design): you cannot
// touch the value without holding the lock, enforced by the `with` API. Acquire
// on lock / Release on unlock give the happens-before edge so writes in the
// critical section are visible to the next holder.
//
// `UnsafeCell` is the one primitive that legally allows `&self`-mutation; we make
// the type `Sync` with an `unsafe impl`, promising that `with` serializes access
// so there is never an overlapping `&mut`. (Educational — prefer std::sync::Mutex.)
struct SpinLock<T> {
    locked: AtomicBool,
    data: std::cell::UnsafeCell<T>,
}
// SAFETY: `with` only ever hands out `&mut T` while the lock is held, so accesses
// are serialized across threads. Requires `T: Send` to move the value between them.
unsafe impl<T: Send> Sync for SpinLock<T> {}

impl<T> SpinLock<T> {
    fn new(value: T) -> Self {
        SpinLock {
            locked: AtomicBool::new(false),
            data: std::cell::UnsafeCell::new(value),
        }
    }
    fn with<R>(&self, f: impl FnOnce(&mut T) -> R) -> R {
        // compare_exchange_weak: try to flip false→true; spin until we win.
        while self
            .locked
            .compare_exchange_weak(false, true, Ordering::Acquire, Ordering::Relaxed)
            .is_err()
        {
            std::hint::spin_loop(); // PAUSE hint: be nice to the core while spinning
        }
        // SAFETY: we hold the lock → exclusive access to the data.
        let result = f(unsafe { &mut *self.data.get() });
        self.locked.store(false, Ordering::Release); // publish our writes
        result
    }
}

fn spinlock_demo(threads: usize, bumps: u64) -> u64 {
    let lock = Arc::new(SpinLock::new(0u64));
    let mut handles = vec![];
    for _ in 0..threads {
        let lock = Arc::clone(&lock);
        handles.push(thread::spawn(move || {
            for _ in 0..bumps {
                lock.with(|v| *v += 1); // critical section, mutually exclusive
            }
        }));
    }
    for h in handles {
        h.join().unwrap();
    }
    lock.with(|v| *v)
}

fn main() {
    println!(
        "[atomic]   8 threads × 100k adds = {}",
        atomic_counter(8, 100_000)
    );
    println!(
        "[spinlock] 4 threads × 50k  bumps = {}",
        spinlock_demo(4, 50_000)
    );

    // Compile-time proof that Rc is not thread-safe but Arc is. These are
    // const checks via trait bounds; flipping Rc to be Send would not compile.
    fn assert_send<T: Send>() {}
    assert_send::<Arc<AtomicU64>>();
    // assert_send::<std::rc::Rc<u64>>(); // ← uncomment: compile error, Rc: !Send
    println!("Arc<AtomicU64>: Send + Sync ✓   (Rc: !Send, rejected at compile time)");
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn atomic_counter_is_exact() {
        assert_eq!(atomic_counter(8, 100_000), 800_000);
    }

    #[test]
    fn spinlock_serializes_writes() {
        assert_eq!(spinlock_demo(4, 50_000), 200_000);
    }
}
