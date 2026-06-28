// ============================================================================
// 02 — Lock-free SPSC ring buffer: the workhorse queue of a trading stack
// Run:  cargo run --release --example 02_spsc_ring_buffer
// C++ counterpart: cpp/expert_trading_features/02_spsc_ring_buffer.cpp
// ----------------------------------------------------------------------------
// One producer (feed handler) hands messages to one consumer (strategy) with NO
// locks and NO allocation on the hot path.
//
// Low-latency techniques (same as the C++ version):
//   * Single-producer/single-consumer => two atomics, no CAS loop.
//   * acquire/release ordering (not SeqCst) for the cheapest correct sync.
//   * head and tail on SEPARATE cache lines (CachePadded) to avoid false sharing.
//   * Power-of-two capacity => index wrap is a bitmask, not a modulo.
//   * Each side caches the other's index to avoid hammering a shared atomic.
//
// What Rust changes vs C++:
//   * The SP/SC contract is ENCODED IN THE TYPES. `channel()` returns one
//     `Producer` and one `Consumer`; only the Producer has `push`, only the
//     Consumer has `pop`, and `&mut self` means each side is used by one thread.
//     In C++ "single producer" is a comment you must not violate; here the borrow
//     checker enforces it (you can't clone a Producer).
//   * The unsafe lives in one audited spot behind a 100% safe API; `unsafe impl
//     Send` documents exactly the invariant that makes cross-thread use sound.
// ============================================================================

use expert_trading_features::CachePadded;
use std::cell::UnsafeCell;
use std::mem::MaybeUninit;
use std::sync::atomic::{AtomicUsize, Ordering};
use std::sync::Arc;

struct Ring<T> {
    // Each slot is independently initialized/read; UnsafeCell allows the
    // interior mutation through a shared &, MaybeUninit lets slots start empty.
    buf: Box<[UnsafeCell<MaybeUninit<T>>]>,
    mask: usize,
    head: CachePadded<AtomicUsize>, // next write index (producer owns)
    tail: CachePadded<AtomicUsize>, // next read index  (consumer owns)
}

// SAFETY: the producer only writes slot `head & mask` then publishes via a
// Release store to `head`; the consumer only reads a slot after observing that
// store via an Acquire load. So writes happen-before the matching reads and no
// two threads ever touch the same slot concurrently. Requires `T: Send` to move
// values across the thread boundary.
unsafe impl<T: Send> Sync for Ring<T> {}
unsafe impl<T: Send> Send for Ring<T> {}

impl<T> Drop for Ring<T> {
    fn drop(&mut self) {
        // Drop any elements still queued (tail..head) so we don't leak them.
        let mut tail = self.tail.load(Ordering::Relaxed);
        let head = self.head.load(Ordering::Relaxed);
        while tail != head {
            // SAFETY: indices in [tail, head) hold initialized values.
            unsafe { (*self.buf[tail & self.mask].get()).assume_init_drop() };
            tail = tail.wrapping_add(1);
        }
    }
}

/// The producer half. Not `Clone` — there can be exactly one.
pub struct Producer<T> {
    ring: Arc<Ring<T>>,
    cached_tail: usize, // producer's private view of the consumer's tail
}
/// The consumer half. Not `Clone` — there can be exactly one.
pub struct Consumer<T> {
    ring: Arc<Ring<T>>,
    cached_head: usize, // consumer's private view of the producer's head
}
// SAFETY: each handle is used by a single thread (`&mut self` methods) and the
// Ring's ordering makes the hand-off sound; the handle is therefore Send.
unsafe impl<T: Send> Send for Producer<T> {}
unsafe impl<T: Send> Send for Consumer<T> {}

/// Create a bounded SPSC queue. `capacity` must be a power of two.
pub fn channel<T: Send>(capacity: usize) -> (Producer<T>, Consumer<T>) {
    assert!(
        capacity.is_power_of_two(),
        "capacity must be a power of two"
    );
    let buf = (0..capacity)
        .map(|_| UnsafeCell::new(MaybeUninit::uninit()))
        .collect::<Vec<_>>()
        .into_boxed_slice();
    let ring = Arc::new(Ring {
        buf,
        mask: capacity - 1,
        head: CachePadded::new(AtomicUsize::new(0)),
        tail: CachePadded::new(AtomicUsize::new(0)),
    });
    (
        Producer {
            ring: Arc::clone(&ring),
            cached_tail: 0,
        },
        Consumer {
            ring,
            cached_head: 0,
        },
    )
}

impl<T> Producer<T> {
    /// Push one value. Returns `Err(value)` if the queue is full (caller keeps it).
    pub fn try_push(&mut self, v: T) -> Result<(), T> {
        let cap = self.ring.buf.len();
        let head = self.ring.head.load(Ordering::Relaxed);
        let next = head.wrapping_add(1);
        if next.wrapping_sub(self.cached_tail) > cap {
            // Maybe full: refresh our cached view of the consumer's progress.
            self.cached_tail = self.ring.tail.load(Ordering::Acquire);
            if next.wrapping_sub(self.cached_tail) > cap {
                return Err(v); // genuinely full
            }
        }
        // SAFETY: this slot is free (consumer has passed it) and only we write it.
        unsafe { (*self.ring.buf[head & self.ring.mask].get()).write(v) };
        self.ring.head.store(next, Ordering::Release); // publish the slot
        Ok(())
    }
}

impl<T> Consumer<T> {
    /// Pop one value, or `None` if the queue is empty.
    pub fn try_pop(&mut self) -> Option<T> {
        let tail = self.ring.tail.load(Ordering::Relaxed);
        if tail == self.cached_head {
            // Maybe empty: refresh our cached view of the producer's head.
            self.cached_head = self.ring.head.load(Ordering::Acquire);
            if tail == self.cached_head {
                return None; // genuinely empty
            }
        }
        // SAFETY: slot `tail` holds an initialized value published by the producer;
        // we move it out exactly once, then free the slot via the Release store.
        let v = unsafe { (*self.ring.buf[tail & self.ring.mask].get()).assume_init_read() };
        self.ring
            .tail
            .store(tail.wrapping_add(1), Ordering::Release);
        Some(v)
    }
}

// A market-data tick: small, `Copy`, so push/pop is a memcpy.
#[derive(Clone, Copy)]
struct Tick {
    seq: u64,
    price: i64,
    qty: u32,
}

fn main() {
    use std::thread;

    let (mut tx, mut rx) = channel::<Tick>(1024);
    const N: u64 = 5_000_000;

    let consumer = thread::spawn(move || {
        let mut got = 0u64;
        let mut checksum = 0i128;
        while got < N {
            if let Some(t) = rx.try_pop() {
                debug_assert_eq!(t.seq, got); // FIFO: sequence arrives in order
                checksum += t.price as i128 + t.qty as i128;
                got += 1;
            } else {
                std::hint::spin_loop();
            }
        }
        checksum
    });

    let producer = thread::spawn(move || {
        for i in 0..N {
            let t = Tick {
                seq: i,
                price: 1_000_000 + (i % 50) as i64,
                qty: 100,
            };
            while tx.try_push(t).is_err() {
                std::hint::spin_loop(); // queue full: back off
            }
        }
    });

    producer.join().unwrap();
    let checksum = consumer.join().unwrap();
    println!("SPSC ring: passed {N} ticks lock-free, checksum={checksum}");
    println!("(run `cargo bench` for ns/tick throughput)");
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn fifo_order_preserved() {
        let (mut tx, mut rx) = channel::<u32>(4);
        for i in 0..3 {
            tx.try_push(i).unwrap();
        }
        assert_eq!(rx.try_pop(), Some(0));
        assert_eq!(rx.try_pop(), Some(1));
        assert_eq!(rx.try_pop(), Some(2));
        assert_eq!(rx.try_pop(), None);
    }

    #[test]
    fn reports_full_and_empty() {
        let (mut tx, mut rx) = channel::<u32>(2); // holds 2
        assert!(rx.try_pop().is_none());
        tx.try_push(10).unwrap();
        tx.try_push(20).unwrap();
        assert_eq!(tx.try_push(30), Err(30)); // full
        assert_eq!(rx.try_pop(), Some(10));
        tx.try_push(30).unwrap(); // slot freed
        assert_eq!(rx.try_pop(), Some(20));
        assert_eq!(rx.try_pop(), Some(30));
    }

    #[test]
    fn threaded_roundtrip_checksum() {
        use std::thread;
        let (mut tx, mut rx) = channel::<u64>(64);
        const M: u64 = 200_000;
        let c = thread::spawn(move || {
            let (mut got, mut sum) = (0u64, 0u128);
            while got < M {
                if let Some(v) = rx.try_pop() {
                    sum += v as u128;
                    got += 1;
                }
            }
            sum
        });
        for i in 0..M {
            while tx.try_push(i).is_err() {}
        }
        assert_eq!(c.join().unwrap(), (0..M as u128).sum::<u128>());
    }
}
