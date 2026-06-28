// ============================================================================
// 09 — Seqlock: wait-free top-of-book publishing (one writer, many readers)
// Run:  cargo run --release --example 09_seqlock
// (No direct C++ demo — the cpp README lists seqlocks as a "production direction".)
// ----------------------------------------------------------------------------
// Publishing the top of book to many strategy threads is a one-writer / many-
// reader problem. A Mutex would make readers block the writer (and each other);
// an RwLock still has writer/reader contention. A SEQLOCK lets the writer NEVER
// block: it bumps a sequence number to odd before writing and to even after.
// Readers snapshot the data between two even, equal sequence reads; if the number
// changed (or was odd) mid-read, they detect the torn read and simply retry.
//
// Why this is a great fit for Rust:
//   * The unsafe interior (an `UnsafeCell<T>` + sequence protocol) is wrapped in a
//     fully safe, generic `SeqLock<T>` API — callers never write `unsafe`.
//   * `unsafe impl Sync` states the exact contract (single writer) that makes it
//     sound, and `T: Copy` ensures a snapshot is a trivial bitwise read.
//
// Honest caveat: the concurrent volatile read/write of `data` is, in the strict
// abstract memory model, a (benign) data race that the sequence check makes safe
// in practice on real hardware. Rigorous implementations (crossbeam's seqlock,
// the `seqlock` crate) read field-by-field with atomics. We keep the classic
// shape to show the protocol.
// ============================================================================

use std::cell::UnsafeCell;
use std::sync::atomic::{fence, AtomicUsize, Ordering};
use std::sync::Arc;

pub struct SeqLock<T> {
    seq: AtomicUsize, // even = stable, odd = write in progress
    data: UnsafeCell<T>,
}

// SAFETY: sound for a SINGLE writer plus any number of readers. The writer's
// even/odd sequence transitions, paired with the readers' retry-on-mismatch,
// ensure a reader only returns a snapshot taken entirely within one stable
// (even, unchanged) window.
unsafe impl<T: Send> Sync for SeqLock<T> {}

impl<T: Copy> SeqLock<T> {
    pub fn new(v: T) -> Self {
        SeqLock {
            seq: AtomicUsize::new(0),
            data: UnsafeCell::new(v),
        }
    }

    /// Publish a new value. Must be called by the single writer only.
    pub fn write(&self, v: T) {
        let s = self.seq.load(Ordering::Relaxed);
        self.seq.store(s.wrapping_add(1), Ordering::Relaxed); // -> odd: in progress
        fence(Ordering::Release);
        // SAFETY: single writer; readers that observe the odd seq will retry.
        unsafe { std::ptr::write_volatile(self.data.get(), v) };
        self.seq.store(s.wrapping_add(2), Ordering::Release); // -> even: published
    }

    /// Take a consistent snapshot. Wait-free for the writer; readers spin only
    /// while a write is actually in flight.
    pub fn read(&self) -> T {
        loop {
            let s1 = self.seq.load(Ordering::Acquire);
            if s1 & 1 != 0 {
                std::hint::spin_loop(); // writer mid-update — try again
                continue;
            }
            // SAFETY: bounded by the seq re-check below; if a write overlapped this
            // read, s2 != s1 and we discard the (possibly torn) value.
            let v = unsafe { std::ptr::read_volatile(self.data.get()) };
            fence(Ordering::Acquire);
            let s2 = self.seq.load(Ordering::Relaxed);
            if s1 == s2 {
                return v; // stable window: snapshot is consistent
            }
        }
    }
}

#[derive(Clone, Copy, Debug, PartialEq)]
struct TopOfBook {
    bid: i64,
    ask: i64,
    bid_sz: u64,
    ask_sz: u64,
}

const SPREAD: i64 = 100; // writer always maintains ask = bid + SPREAD

fn main() {
    use std::sync::atomic::AtomicBool;
    use std::thread;

    let book = Arc::new(SeqLock::new(TopOfBook {
        bid: 1_000_000,
        ask: 1_000_000 + SPREAD,
        bid_sz: 10,
        ask_sz: 10,
    }));
    let stop = Arc::new(AtomicBool::new(false));

    // One writer, hammering updates while preserving the invariant ask-bid==SPREAD.
    let w = {
        let book = Arc::clone(&book);
        let stop = Arc::clone(&stop);
        thread::spawn(move || {
            let mut bid = 1_000_000i64;
            let mut updates = 0u64;
            while !stop.load(Ordering::Relaxed) {
                bid += 1;
                book.write(TopOfBook {
                    bid,
                    ask: bid + SPREAD,
                    bid_sz: (bid % 97) as u64,
                    ask_sz: (bid % 89) as u64,
                });
                updates += 1;
            }
            updates
        })
    };

    // Several readers snapshotting concurrently; each verifies the invariant. A
    // torn read would show ask-bid != SPREAD.
    let readers: Vec<_> = (0..4)
        .map(|_| {
            let book = Arc::clone(&book);
            let stop = Arc::clone(&stop);
            thread::spawn(move || {
                let (mut reads, mut torn) = (0u64, 0u64);
                while !stop.load(Ordering::Relaxed) {
                    let t = book.read();
                    if t.ask - t.bid != SPREAD {
                        torn += 1; // would indicate a consistency bug
                    }
                    reads += 1;
                }
                (reads, torn)
            })
        })
        .collect();

    thread::sleep(std::time::Duration::from_millis(300));
    stop.store(true, Ordering::Relaxed);

    let updates = w.join().unwrap();
    let mut total_reads = 0u64;
    let mut total_torn = 0u64;
    for r in readers {
        let (reads, torn) = r.join().unwrap();
        total_reads += reads;
        total_torn += torn;
    }
    println!("writer published {updates} updates");
    println!("4 readers took {total_reads} snapshots, {total_torn} torn (consistency violations)");
    println!("=> readers never blocked the writer, and every snapshot was internally consistent");
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn single_thread_read_after_write() {
        let s = SeqLock::new(0u64);
        s.write(42);
        assert_eq!(s.read(), 42);
        s.write(7);
        assert_eq!(s.read(), 7);
    }

    #[test]
    fn concurrent_reads_are_never_torn() {
        use std::sync::atomic::AtomicBool;
        use std::thread;
        let book = Arc::new(SeqLock::new(TopOfBook {
            bid: 100,
            ask: 100 + SPREAD,
            bid_sz: 1,
            ask_sz: 1,
        }));
        let stop = Arc::new(AtomicBool::new(false));
        let w = {
            let book = Arc::clone(&book);
            let stop = Arc::clone(&stop);
            thread::spawn(move || {
                let mut bid = 100i64;
                while !stop.load(Ordering::Relaxed) {
                    bid += 1;
                    book.write(TopOfBook {
                        bid,
                        ask: bid + SPREAD,
                        bid_sz: 1,
                        ask_sz: 1,
                    });
                }
            })
        };
        let mut torn = 0u64;
        for _ in 0..200_000 {
            let t = book.read();
            if t.ask - t.bid != SPREAD {
                torn += 1;
            }
        }
        stop.store(true, Ordering::Relaxed);
        w.join().unwrap();
        assert_eq!(torn, 0, "seqlock returned a torn snapshot");
    }
}
