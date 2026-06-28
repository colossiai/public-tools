// ============================================================================
// 04 — Object pool / free list: zero allocation on the hot path
// Run:  cargo run --release --example 04_object_pool
// C++ counterpart: cpp/expert_trading_features/04_object_pool.cpp
// ----------------------------------------------------------------------------
// `Box::new` / the global allocator are forbidden on a trading hot path: they can
// lock, touch the kernel, and have a long, unpredictable tail (page faults, arena
// contention). Instead pre-allocate ALL objects up front and hand them out from
// an intrusive free list — O(1), no allocator, deterministic latency.
//
// What Rust changes vs C++:
//   * We hand out a `Handle` (a typed index), not a raw pointer. release() takes
//     the handle by value, so it's CONSUMED — the borrow/ownership rules make a
//     use-after-free or double-free far harder to write than with raw `T*`.
//   * Storage is `Vec<MaybeUninit<T>>`; the unsafe is confined to get()/release().
//   * No placement-new ceremony: `MaybeUninit::write` is the safe-ish primitive.
// ============================================================================

use std::mem::MaybeUninit;

// A resting order — what we allocate millions of times a day.
#[derive(Clone, Copy, Debug, PartialEq)]
struct Order {
    id: u64,
    price: i64,
    qty: u32,
    side: u8, // b'B' / b'S'
}

/// A typed handle into the pool. Carrying the index (not a pointer) means a stale
/// handle can be cheaply range-checked, and `release` consuming it by value stops
/// you using the slot afterwards.
#[derive(Clone, Copy, PartialEq, Eq, Debug)]
struct Handle(usize);

struct Pool<T> {
    slots: Vec<MaybeUninit<T>>,
    next_free: Vec<usize>, // intrusive free list: next_free[i] = next free slot
    free_head: usize,
    in_use: usize,
}

const NIL: usize = usize::MAX;

impl<T> Pool<T> {
    fn with_capacity(n: usize) -> Self {
        let mut slots = Vec::with_capacity(n);
        let mut next_free = Vec::with_capacity(n);
        for i in 0..n {
            slots.push(MaybeUninit::uninit());
            next_free.push(if i + 1 < n { i + 1 } else { NIL });
        }
        Pool {
            slots,
            next_free,
            free_head: if n == 0 { NIL } else { 0 },
            in_use: 0,
        }
    }

    /// O(1), no heap. Returns None when exhausted (caller decides policy).
    fn acquire(&mut self, value: T) -> Option<Handle> {
        if self.free_head == NIL {
            return None;
        }
        let idx = self.free_head;
        self.free_head = self.next_free[idx];
        self.slots[idx].write(value); // initialize the slot
        self.in_use += 1;
        Some(Handle(idx))
    }

    /// O(1) return to the pool. Consumes the handle so it can't be reused.
    fn release(&mut self, h: Handle) {
        // SAFETY: a live Handle always points at an initialized slot; we drop the
        // value exactly once and thread the slot back onto the free list.
        unsafe { self.slots[h.0].assume_init_drop() };
        self.next_free[h.0] = self.free_head;
        self.free_head = h.0;
        self.in_use -= 1;
    }

    fn get(&self, h: Handle) -> &T {
        // SAFETY: a live Handle points at an initialized slot.
        unsafe { self.slots[h.0].assume_init_ref() }
    }

    fn in_use(&self) -> usize {
        self.in_use
    }
    fn capacity(&self) -> usize {
        self.slots.len()
    }
}

fn main() {
    let mut pool: Pool<Order> = Pool::with_capacity(1 << 16);
    println!(
        "pool capacity = {} orders, allocated once up front",
        pool.capacity()
    );

    // Acquire a churn of resting orders.
    let mut live: Vec<Handle> = Vec::new();
    for i in 0..1000u64 {
        let h = pool
            .acquire(Order {
                id: 1000 + i,
                price: 1_000_000 + i as i64,
                qty: 100,
                side: if i & 1 == 0 { b'S' } else { b'B' },
            })
            .unwrap();
        live.push(h);
    }
    println!("after 1000 acquires: in_use={}", pool.in_use());

    // Cancel the even ones, recording notional.
    let mut notional: u128 = 0;
    for i in (0..live.len()).step_by(2) {
        let o = pool.get(live[i]);
        notional += o.price as u128 * o.qty as u128;
        pool.release(live[i]);
    }
    println!(
        "after cancelling 500: in_use={} (slots recycled, no allocator call)",
        pool.in_use()
    );

    // Reacquire — the freed slots come right back, hot in cache.
    for i in (0..live.len()).step_by(2) {
        live[i] = pool
            .acquire(Order {
                id: 9000 + i as u64,
                price: 2_000_000,
                qty: 50,
                side: b'S',
            })
            .unwrap();
    }
    println!(
        "after reacquiring 500: in_use={}, cancelled notional={notional}",
        pool.in_use()
    );
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn acquire_release_recycles_slots() {
        let mut p: Pool<Order> = Pool::with_capacity(2);
        let h1 = p
            .acquire(Order {
                id: 1,
                price: 100,
                qty: 1,
                side: b'B',
            })
            .unwrap();
        let h2 = p
            .acquire(Order {
                id: 2,
                price: 200,
                qty: 2,
                side: b'S',
            })
            .unwrap();
        assert_eq!(
            p.acquire(Order {
                id: 3,
                price: 300,
                qty: 3,
                side: b'B'
            }),
            None
        ); // full
        assert_eq!(p.in_use(), 2);
        p.release(h1);
        let h3 = p
            .acquire(Order {
                id: 3,
                price: 300,
                qty: 3,
                side: b'B',
            })
            .unwrap();
        assert_eq!(h3, h1); // recycled the freed slot
        assert_eq!(p.get(h2).id, 2);
        assert_eq!(p.get(h3).id, 3);
    }

    #[test]
    fn empty_pool_yields_nothing() {
        let mut p: Pool<u32> = Pool::with_capacity(0);
        assert_eq!(p.acquire(1), None);
    }
}
