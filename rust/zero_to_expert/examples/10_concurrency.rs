// ============================================================================
// 10 — Fearless concurrency: threads, scoped threads, Arc<Mutex>, channels
// Run:  cargo run --example 10_concurrency
// ----------------------------------------------------------------------------
// "Fearless concurrency" = the SAME ownership rules that prevent dangling
// pointers also prevent data races, at compile time. Sharing across threads is
// allowed only through types the compiler proves are safe to share:
//
//   * Arc<T>           — atomically reference-counted shared ownership (the
//                        thread-safe Rc). Many threads can own the same data.
//   * Mutex<T>/RwLock  — make shared data mutable safely: you can't touch the
//                        data without holding the lock (the lock OWNS the data).
//   * mpsc channels    — message passing: move data between threads, no sharing.
//   * scoped threads   — borrow local stack data in threads that are guaranteed
//                        to finish before the scope ends (no Arc needed).
//
// Try to send a non-Send type or share without a lock and it simply won't build.
// ============================================================================

use std::sync::mpsc;
use std::sync::{Arc, Mutex};
use std::thread;

// Shared mutable state across threads: Arc for shared ownership, Mutex for safe
// mutation. The data lives *inside* the Mutex — you can't read it unlocked.
fn parallel_sum(nums: Vec<u64>, workers: usize) -> u64 {
    let total = Arc::new(Mutex::new(0u64));
    let chunks: Vec<Vec<u64>> = nums
        .chunks(nums.len().div_ceil(workers))
        .map(|c| c.to_vec())
        .collect();

    let mut handles = vec![];
    for chunk in chunks {
        let total = Arc::clone(&total); // each thread gets its own owning handle
        handles.push(thread::spawn(move || {
            let partial: u64 = chunk.iter().sum();
            *total.lock().unwrap() += partial; // lock → mutate → unlock on drop
        }));
    }
    for h in handles {
        h.join().unwrap();
    }
    Arc::try_unwrap(total).unwrap().into_inner().unwrap()
}

// Message passing: a producer thread sends work, the main thread consumes it.
// Ownership of each message MOVES through the channel — no shared state at all.
fn pipeline_demo() -> Vec<i64> {
    let (tx, rx) = mpsc::channel::<i64>();
    let producer = thread::spawn(move || {
        for i in 1..=5 {
            tx.send(i * i).unwrap();
        }
        // tx dropped here → channel closes → the `for` below ends.
    });
    let received: Vec<i64> = rx.iter().collect(); // blocks until channel closes
    producer.join().unwrap();
    received
}

// Scoped threads (stable since 1.63) can borrow local data: the scope guarantees
// every spawned thread joins before `scope` returns, so the borrow is sound
// WITHOUT Arc/clone.
fn scoped_max(data: &[i64]) -> i64 {
    let mid = data.len() / 2;
    let (left, right) = data.split_at(mid);
    thread::scope(|s| {
        let h1 = s.spawn(|| left.iter().copied().max().unwrap_or(i64::MIN));
        let h2 = s.spawn(|| right.iter().copied().max().unwrap_or(i64::MIN));
        h1.join().unwrap().max(h2.join().unwrap())
    })
}

fn main() {
    let nums: Vec<u64> = (1..=1000).collect();
    println!(
        "[arc/mutex] parallel_sum(1..=1000) = {}",
        parallel_sum(nums, 4)
    );

    println!("[channel] squares received = {:?}", pipeline_demo());

    let data = [3, 9, 1, 7, 12, 4, 8, 2];
    println!("[scoped] max (borrowed, no Arc) = {}", scoped_max(&data));
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn parallel_sum_matches_serial() {
        let nums: Vec<u64> = (1..=1000).collect();
        let serial: u64 = nums.iter().sum();
        assert_eq!(parallel_sum(nums, 4), serial);
        assert_eq!(serial, 500_500);
    }

    #[test]
    fn channel_preserves_order() {
        assert_eq!(pipeline_demo(), vec![1, 4, 9, 16, 25]);
    }

    #[test]
    fn scoped_threads_find_max() {
        assert_eq!(scoped_max(&[3, 9, 1, 7, 12, 4]), 12);
    }
}
