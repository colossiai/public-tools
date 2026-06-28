// ============================================================================
// 14 — Async from scratch: a Future, a Waker, and a minimal executor (no crates)
// Run:  cargo run --example 14_async_executor
// ----------------------------------------------------------------------------
// `async fn` / `.await` are sugar. The compiler turns an async function into a
// state machine implementing the `Future` trait:
//
//     trait Future { type Output; fn poll(self: Pin<&mut Self>, cx) -> Poll<…>; }
//
// `poll` is called by an EXECUTOR. It returns `Ready(v)` when done, or `Pending`
// when blocked — and before returning Pending it stashes the `Waker` from `cx`
// so that whatever it's waiting on can call `wake()` to ask for another poll.
// `Pin` guarantees the self-referential state machine won't move in memory.
//
// `std` deliberately ships NO executor. This file builds one — a `block_on` that
// parks the thread and a Waker that unparks it — to demystify tokio/async-std.
// ============================================================================

use std::future::Future;
use std::pin::Pin;
use std::sync::atomic::{AtomicU32, Ordering};
use std::sync::Arc;
use std::task::{Context, Poll, RawWaker, RawWakerVTable, Waker};
use std::thread::{self, Thread};

// --- Build a Waker by hand from a parked thread -------------------------------
// A Waker is a type-erased (clone, wake, wake_by_ref, drop) vtable over some
// data pointer. Ours carries an Arc<Thread>; waking == unparking that thread.
fn thread_waker(thread: Arc<Thread>) -> Waker {
    fn clone(ptr: *const ()) -> RawWaker {
        // SAFETY: `ptr` came from Arc::into_raw below; reconstruct, bump the
        // refcount via clone, and forget the temporary so we don't drop a ref.
        let arc = unsafe { Arc::from_raw(ptr as *const Thread) };
        let cloned = Arc::clone(&arc);
        std::mem::forget(arc);
        RawWaker::new(Arc::into_raw(cloned) as *const (), &VTABLE)
    }
    fn wake(ptr: *const ()) {
        // SAFETY: takes ownership of one ref and drops it after unparking.
        let arc = unsafe { Arc::from_raw(ptr as *const Thread) };
        arc.unpark();
    }
    fn wake_by_ref(ptr: *const ()) {
        let arc = unsafe { Arc::from_raw(ptr as *const Thread) };
        arc.unpark();
        std::mem::forget(arc); // don't consume our ref
    }
    fn drop_waker(ptr: *const ()) {
        // SAFETY: balances one Arc::into_raw.
        unsafe { drop(Arc::from_raw(ptr as *const Thread)) };
    }
    static VTABLE: RawWakerVTable = RawWakerVTable::new(clone, wake, wake_by_ref, drop_waker);

    let raw = RawWaker::new(Arc::into_raw(thread) as *const (), &VTABLE);
    // SAFETY: `raw`'s vtable upholds the Waker contract above.
    unsafe { Waker::from_raw(raw) }
}

// --- The executor: drive ONE future to completion on this thread --------------
fn block_on<F: Future>(future: F) -> F::Output {
    // Pin the future to the stack; we never move it after this.
    let mut future = Box::pin(future);
    let waker = thread_waker(Arc::new(thread::current()));
    let mut cx = Context::from_waker(&waker);

    loop {
        match future.as_mut().poll(&mut cx) {
            Poll::Ready(val) => return val,
            // Nothing to do until someone wakes us; sleep the thread instead of
            // busy-spinning. `wake()` (→ unpark) makes the next park() return.
            Poll::Pending => thread::park(),
        }
    }
}

// --- A leaf future: cooperatively yield control exactly once ------------------
// First poll: register interest (wake ourselves) and return Pending. The
// executor re-polls; second time we're Ready. This is the smallest future that
// actually exercises the waker round-trip.
struct YieldNow {
    yielded: bool,
}
impl Future for YieldNow {
    type Output = ();
    fn poll(mut self: Pin<&mut Self>, cx: &mut Context<'_>) -> Poll<()> {
        if self.yielded {
            Poll::Ready(())
        } else {
            self.yielded = true;
            cx.waker().wake_by_ref(); // "please poll me again"
            Poll::Pending
        }
    }
}
fn yield_now() -> YieldNow {
    YieldNow { yielded: false }
}

// Count how many times the executor had to poll, to prove yields really suspend.
static POLLS: AtomicU32 = AtomicU32::new(0);

// --- async fns: the compiler builds the Future state machine for us -----------
async fn sum_to(n: u32) -> u32 {
    let mut acc = 0;
    for i in 1..=n {
        acc += i;
        POLLS.fetch_add(1, Ordering::Relaxed);
        yield_now().await; // suspend; resumes on the next poll
    }
    acc
}

async fn run() -> (u32, u32) {
    // Sequential awaits compose naturally; each `.await` may suspend the whole
    // chain and resume exactly where it left off.
    let a = sum_to(5).await; // 15
    let b = sum_to(3).await; // 6
    (a, b)
}

fn main() {
    let (a, b) = block_on(run());
    println!("[executor] sum_to(5)={a}, sum_to(3)={b}");
    println!(
        "[executor] total polls of yield points = {}",
        POLLS.load(Ordering::Relaxed)
    );
    println!("note: a real runtime (tokio/async-std) adds a multi-task scheduler,");
    println!("      timers, and IO reactors on top of exactly this poll/wake loop.");
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn block_on_runs_to_completion() {
        assert_eq!(block_on(sum_to(10)), 55);
    }

    #[test]
    fn awaits_compose() {
        assert_eq!(block_on(run()), (15, 6));
    }

    #[test]
    fn ready_future_needs_no_wake() {
        // An already-ready future returns on the first poll.
        assert_eq!(block_on(async { 7 }), 7);
    }
}
