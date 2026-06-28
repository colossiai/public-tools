// ============================================================================
// bench_all — std-only micro-benchmarks behind the reports in bench_intel_mac/
// Run:  cargo bench            (release build, harness disabled — see Cargo.toml)
// ----------------------------------------------------------------------------
// One section per demo. Each prints a labeled result line that the matching
// report transcribes. Methodology: best-of-N trials (min filters scheduler /
// frequency jitter), `black_box` on inputs and outputs so the optimizer can't
// hoist work out of the loop or constant-fold the answer.
//
// Several demos teach *correctness / type-system* features whose honest result
// is "no runtime cost" — for those we benchmark the abstraction against the
// hand-written baseline and expect a ratio of ~1.0. That ~1.0 IS the finding.
// ============================================================================

use std::hint::black_box;
use std::time::Instant;

const TRIALS: usize = 7;

// Time `f` TRIALS times, return (result, best milliseconds).
fn best_ms(mut f: impl FnMut() -> i64) -> (i64, f64) {
    let mut best = f64::MAX;
    let mut out = 0;
    for _ in 0..TRIALS {
        let t = Instant::now();
        out = black_box(f());
        best = best.min(t.elapsed().as_secs_f64() * 1e3);
    }
    (out, best)
}

fn line(demo: &str, msg: String) {
    println!("{demo:<34} {msg}");
}

// --- 01 ownership: what `.clone()` costs vs a move (which is ~free) ----------
fn bench_01_ownership() {
    const N: usize = 2000;
    const LEN: usize = 1024; // 8 KiB Vec<u64>
    let src = black_box(vec![7u64; LEN]);

    // Clone: allocate + memcpy LEN*8 bytes, every time.
    let (_c, ms_clone) = best_ms(|| {
        let mut acc = 0i64;
        for _ in 0..N {
            let c = black_box(src.clone());
            acc += c[0] as i64;
        }
        acc
    });
    // Move: transfer ownership of an existing buffer — no allocation, no copy of
    // the heap data. We move a freshly-made Vec in and out of a sink.
    let (_m, ms_move) = best_ms(|| {
        let mut acc = 0i64;
        let mut sink = black_box(vec![7u64; LEN]);
        for _ in 0..N {
            let moved = sink; // move out
            acc += moved[0] as i64;
            sink = moved; // move back — still no copy of the 8 KiB
        }
        acc
    });
    let per_clone = ms_clone * 1e6 / N as f64; // ns per clone
    let per_move = ms_move * 1e6 / N as f64;
    line("01_ownership", format!(
        "clone 8KiB = {per_clone:.1} ns/op   move = {per_move:.2} ns/op   (move avoids the alloc+copy)"
    ));
}

// --- 02 enums/match: dispatch over an enum compiles to a jump, ~free ---------
fn bench_02_match() {
    #[derive(Clone, Copy)]
    enum Op {
        Add,
        Sub,
        Mul,
        Nop,
    }
    let ops: Vec<Op> = (0..4_000_000usize)
        .map(|i| match i % 4 {
            0 => Op::Add,
            1 => Op::Sub,
            2 => Op::Mul,
            _ => Op::Nop,
        })
        .collect();
    let ops = black_box(ops);
    let (_s, ms) = best_ms(|| {
        let mut acc = 0i64;
        for (i, op) in ops.iter().enumerate() {
            let x = i as i64;
            acc += match op {
                Op::Add => x + 1,
                Op::Sub => x - 1,
                Op::Mul => x * 2,
                Op::Nop => 0,
            };
        }
        acc
    });
    let per = ms * 1e6 / ops.len() as f64;
    line(
        "02_match",
        format!("enum match dispatch = {per:.3} ns/op  (compiles to a branch/jump table)"),
    );
}

// --- 03 error handling: the `?` happy path is as cheap as no error channel ----
// Fair comparison: IDENTICAL loop structure and arithmetic, the only difference
// being whether the step returns Result<i64,_> (unwrapped via `?`) or a bare i64.
// `step_ok` has no validation branch, so this isolates the Result/`?` machinery.
fn bench_03_errors() {
    let data: Vec<i64> = (0..20_000_000).collect();
    let data = black_box(data);
    #[inline]
    fn step_ok(x: i64) -> Result<i64, ()> {
        Ok(x * 2)
    }
    #[inline]
    fn step_raw(x: i64) -> i64 {
        x * 2
    }
    fn checked(xs: &[i64]) -> Result<i64, ()> {
        let mut acc = 0;
        for &x in xs {
            acc += step_ok(x)?;
        }
        Ok(acc)
    }
    fn direct(xs: &[i64]) -> i64 {
        let mut acc = 0;
        for &x in xs {
            acc += step_raw(x);
        }
        acc
    }
    let (_a, ms_res) = best_ms(|| checked(black_box(&data)).unwrap());
    let (_b, ms_dir) = best_ms(|| direct(black_box(&data)));
    line("03_error_handling", format!(
        "Result+? = {ms_res:.2} ms   bare i64 = {ms_dir:.2} ms   ratio {:.2}x (zero-cost on the Ok path)",
        ms_res / ms_dir.max(f64::MIN_POSITIVE)
    ));
}

// --- 04 iterators: a fused adapter chain vs the hand-written loop -------------
fn bench_04_iterators() {
    let data: Vec<i64> = (0..20_000_000).collect();
    let data = black_box(data);
    let (_a, ms_iter) = best_ms(|| {
        black_box(&data)
            .iter()
            .filter(|&&x| x % 2 == 0)
            .map(|&x| x * 3)
            .sum()
    });
    let (_b, ms_loop) = best_ms(|| {
        let mut s = 0i64;
        for &x in black_box(&data) {
            if x % 2 == 0 {
                s += x * 3;
            }
        }
        s
    });
    line("04_iterators", format!(
        "iter chain = {ms_iter:.2} ms   manual loop = {ms_loop:.2} ms   ratio {:.2}x (fused, zero-cost)",
        ms_iter / ms_loop.max(f64::MIN_POSITIVE)
    ));
}

// --- 05 generics: a monomorphized generic vs a hand-specialized fn -----------
fn bench_05_generics() {
    use std::ops::Add;
    fn sum_generic<T: Add<Output = T> + Copy + Default>(xs: &[T]) -> T {
        let mut acc = T::default();
        for &x in xs {
            acc = acc + x;
        }
        acc
    }
    fn sum_i64(xs: &[i64]) -> i64 {
        let mut a = 0;
        for &x in xs {
            a += x;
        }
        a
    }
    let data: Vec<i64> = (0..20_000_000).collect();
    let data = black_box(data);
    let (_a, ms_gen) = best_ms(|| sum_generic(black_box(&data)));
    let (_b, ms_spec) = best_ms(|| sum_i64(black_box(&data)));
    line(
        "05_generics",
        format!(
        "generic = {ms_gen:.2} ms   specialized = {ms_spec:.2} ms   ratio {:.2}x (monomorphized)",
        ms_gen / ms_spec.max(f64::MIN_POSITIVE)
    ),
    );
}

// --- 06 dispatch: static (generic/inlinable) vs dynamic (Box<dyn>, vtable) ----
fn bench_06_dispatch() {
    trait Signal {
        fn score(&self, p: f64) -> f64;
    }
    struct Momentum {
        last: f64,
    }
    impl Signal for Momentum {
        #[inline]
        fn score(&self, p: f64) -> f64 {
            p - self.last
        }
    }

    fn eval_static<S: Signal>(s: &S, prices: &[f64]) -> f64 {
        prices.iter().map(|&p| s.score(p)).sum()
    }
    fn eval_dyn(s: &dyn Signal, prices: &[f64]) -> f64 {
        prices.iter().map(|&p| s.score(p)).sum()
    }
    let prices: Vec<f64> = (0..20_000_000).map(|i| (i % 100) as f64).collect();
    let prices = black_box(prices);
    let m = Momentum { last: 50.0 };
    let dynref: &dyn Signal = &m;

    let (_a, ms_s) = best_ms(|| eval_static(&m, black_box(&prices)) as i64);
    let (_b, ms_d) = best_ms(|| eval_dyn(black_box(dynref), black_box(&prices)) as i64);
    line(
        "06_dispatch",
        format!(
        "static = {ms_s:.2} ms   dyn = {ms_d:.2} ms   dyn/static {:.2}x (vtable call can't inline)",
        ms_d / ms_s.max(f64::MIN_POSITIVE)
    ),
    );
}

// --- 07 closures: generic Fn (inlined) vs Box<dyn Fn> (indirect) -------------
fn bench_07_closures() {
    fn apply_generic<F: Fn(i64) -> i64>(f: F, xs: &[i64]) -> i64 {
        xs.iter().map(|&x| f(x)).sum()
    }
    fn apply_boxed(f: &dyn Fn(i64) -> i64, xs: &[i64]) -> i64 {
        xs.iter().map(|&x| f(x)).sum()
    }
    let data: Vec<i64> = (0..20_000_000).collect();
    let data = black_box(data);
    let k = black_box(3i64);
    let boxed: Box<dyn Fn(i64) -> i64> = Box::new(move |x| x * k + 1);

    let (_a, ms_g) = best_ms(|| apply_generic(|x| x * k + 1, black_box(&data)));
    let (_b, ms_b) = best_ms(|| apply_boxed(black_box(&*boxed), black_box(&data)));
    line(
        "07_closures",
        format!(
            "generic Fn = {ms_g:.2} ms   Box<dyn Fn> = {ms_b:.2} ms   boxed/generic {:.2}x",
            ms_b / ms_g.max(f64::MIN_POSITIVE)
        ),
    );
}

// --- 08 lifetimes: borrowing slices (zero-copy) vs allocating owned Strings ---
fn bench_08_lifetimes() {
    let text = black_box("AAPL,MSFT,GOOG,AMZN,META,NVDA,TSLA,NFLX,INTC,AMD".repeat(50_000));
    // Zero-copy: yield &str slices that borrow from `text`. No allocation.
    let (_a, ms_borrow) = best_ms(|| {
        let mut total = 0i64;
        for tok in black_box(text.as_str()).split(',') {
            total += tok.len() as i64;
        }
        total
    });
    // Owned: allocate a String per token (what you'd do without borrowing).
    let (_b, ms_owned) = best_ms(|| {
        let mut total = 0i64;
        for tok in black_box(text.as_str()).split(',') {
            let owned: String = tok.to_string(); // heap alloc per token
            total += owned.len() as i64;
        }
        total
    });
    line("08_lifetimes", format!(
        "borrow &str = {ms_borrow:.2} ms   owned String = {ms_owned:.2} ms   owned/borrow {:.2}x (alloc per token)",
        ms_owned / ms_borrow.max(f64::MIN_POSITIVE)
    ));
}

// --- 09 smart pointers: Rc::clone (refcount bump) vs a deep clone ------------
fn bench_09_smart_pointers() {
    use std::cell::RefCell;
    use std::rc::Rc;
    const N: usize = 5_000_000;
    let payload: Vec<u64> = (0..256).collect(); // 2 KiB
    let rc = Rc::new(payload.clone());
    let rc = black_box(rc);
    let payload = black_box(payload);

    let (_a, ms_rc) = best_ms(|| {
        let mut acc = 0i64;
        for _ in 0..N {
            let c = Rc::clone(black_box(&rc));
            acc += c[0] as i64;
        }
        acc
    });
    let (_b, ms_deep) = best_ms(|| {
        let mut acc = 0i64;
        for _ in 0..N {
            let c = black_box(&payload).clone();
            acc += c[0] as i64;
        }
        acc
    });
    let rc_ns = ms_rc * 1e6 / N as f64;
    let deep_ns = ms_deep * 1e6 / N as f64;

    // RefCell runtime-borrow-check overhead vs a direct &mut. We sum each read so
    // the loop can't be folded away, and black_box the cell each iteration.
    let cell = RefCell::new(0i64);
    let mut plain = 0i64;
    let (_c, ms_ref) = best_ms(|| {
        let mut acc = 0i64;
        for _ in 0..N {
            let c = black_box(&cell);
            *c.borrow_mut() += 1;
            acc += *c.borrow();
        }
        acc
    });
    let (_d, ms_plain) = best_ms(|| {
        let mut acc = 0i64;
        for _ in 0..N {
            let p = black_box(&mut plain);
            *p += 1;
            acc += *p;
        }
        acc
    });
    let ref_ns = ms_ref * 1e6 / N as f64;
    let plain_ns = ms_plain * 1e6 / N as f64;
    line("09_smart_pointers", format!(
        "Rc::clone = {rc_ns:.1} ns   deep clone 2KiB = {deep_ns:.1} ns   RefCell = {ref_ns:.2} ns vs &mut = {plain_ns:.2} ns/iter"
    ));
}

// --- 10 concurrency: parallel sum speedup, 1 vs N threads --------------------
fn bench_10_concurrency() {
    use std::thread;
    fn parallel_sum(nums: &[u64], workers: usize) -> u64 {
        if workers <= 1 {
            return nums.iter().sum();
        }
        let chunk = nums.len().div_ceil(workers);
        thread::scope(|s| {
            let handles: Vec<_> = nums
                .chunks(chunk)
                .map(|c| s.spawn(move || c.iter().sum::<u64>()))
                .collect();
            handles.into_iter().map(|h| h.join().unwrap()).sum()
        })
    }
    let nums: Vec<u64> = (0..50_000_000).collect();
    let nums = black_box(nums);
    let (_a, ms1) = best_ms(|| parallel_sum(black_box(&nums), 1) as i64);
    let (_b, ms4) = best_ms(|| parallel_sum(black_box(&nums), 4) as i64);
    let (_c, ms8) = best_ms(|| parallel_sum(black_box(&nums), 8) as i64);
    line(
        "10_concurrency",
        format!(
            "sum 50M: 1 thread = {ms1:.2} ms   4 = {ms4:.2} ms ({:.2}x)   8 = {ms8:.2} ms ({:.2}x)",
            ms1 / ms4.max(f64::MIN_POSITIVE),
            ms1 / ms8.max(f64::MIN_POSITIVE)
        ),
    );
}

// --- 11 atomics: lock-free counter vs Mutex<u64> under heavy contention ------
fn bench_11_atomics() {
    use std::sync::atomic::{AtomicU64, Ordering};
    use std::sync::{Arc, Mutex};
    use std::thread;
    const THREADS: usize = 8;
    const PER: u64 = 1_000_000;

    let run_atomic = || {
        let c = Arc::new(AtomicU64::new(0));
        let hs: Vec<_> = (0..THREADS)
            .map(|_| {
                let c = Arc::clone(&c);
                thread::spawn(move || {
                    for _ in 0..PER {
                        c.fetch_add(1, Ordering::Relaxed);
                    }
                })
            })
            .collect();
        for h in hs {
            h.join().unwrap();
        }
        c.load(Ordering::Relaxed) as i64
    };
    let run_mutex = || {
        let c = Arc::new(Mutex::new(0u64));
        let hs: Vec<_> = (0..THREADS)
            .map(|_| {
                let c = Arc::clone(&c);
                thread::spawn(move || {
                    for _ in 0..PER {
                        *c.lock().unwrap() += 1;
                    }
                })
            })
            .collect();
        for h in hs {
            h.join().unwrap();
        }
        let v = *c.lock().unwrap();
        v as i64
    };
    let (_a, ms_at) = best_ms(run_atomic);
    let (_b, ms_mx) = best_ms(run_mutex);
    let ops = (THREADS as u64 * PER) as f64;
    line("11_atomics", format!(
        "8×1M increments: Atomic = {ms_at:.2} ms ({:.1} ns/op)   Mutex = {ms_mx:.2} ms ({:.1} ns/op)   {:.1}x",
        ms_at * 1e6 / ops, ms_mx * 1e6 / ops, ms_mx / ms_at.max(f64::MIN_POSITIVE)
    ));
}

// --- 12 unsafe: MaybeUninit (skip zeroing) vs zero-init then overwrite --------
fn bench_12_unsafe() {
    use std::mem::MaybeUninit;
    const LEN: usize = 4096;
    const N: usize = 200_000;
    // Baseline: allocate zeroed, then write every slot (the zeroing is wasted).
    let (_a, ms_zero) = best_ms(|| {
        let mut acc = 0i64;
        for _ in 0..N {
            let mut v = vec![0u64; LEN];
            for (i, slot) in v.iter_mut().enumerate() {
                *slot = i as u64;
            }
            acc += black_box(&v)[LEN - 1] as i64;
        }
        acc
    });
    // MaybeUninit: allocate uninitialized, write every slot once.
    let (_b, ms_uninit) = best_ms(|| {
        let mut acc = 0i64;
        for _ in 0..N {
            let mut v: Vec<MaybeUninit<u64>> = Vec::with_capacity(LEN);
            // SAFETY: we set_len then write all LEN elements before reading.
            unsafe {
                v.set_len(LEN);
            }
            for (i, slot) in v.iter_mut().enumerate() {
                slot.write(i as u64);
            }
            // SAFETY: every element initialized above.
            let last = unsafe { v[LEN - 1].assume_init() };
            acc += black_box(last) as i64;
        }
        acc
    });
    line("12_unsafe", format!(
        "fill 4Ki×u64: zero-init+write = {ms_zero:.2} ms   MaybeUninit = {ms_uninit:.2} ms   {:.2}x",
        ms_zero / ms_uninit.max(f64::MIN_POSITIVE)
    ));
}

// --- 13 macros: macro expansion vs writing the SAME code by hand -------------
// The point is "a macro expands to code you could have typed → it adds nothing".
// So the fair baseline is the hand-written expansion (Vec::new + pushes), NOT
// std `vec!` (which preallocates exact capacity — a different *implementation*,
// not a macro-vs-no-macro difference). Compared like-for-like, the ratio is ~1.0.
// (Both sides deliberately use push-then-build, so silence clippy's vec! hint.)
#[allow(clippy::vec_init_then_push)]
fn bench_13_macros() {
    macro_rules! myvec {
        ($($x:expr),+ $(,)?) => {{ let mut v = Vec::new(); $( v.push($x); )+ v }};
    }
    const N: usize = 2_000_000;
    let (_a, ms_my) = best_ms(|| {
        let mut acc = 0i64;
        for i in 0..N {
            let v: Vec<i64> = myvec![i as i64, 2, 3, 4];
            acc += black_box(&v)[0];
        }
        acc
    });
    let (_b, ms_hand) = best_ms(|| {
        let mut acc = 0i64;
        for i in 0..N {
            let v: Vec<i64> = {
                let mut v = Vec::new();
                v.push(i as i64);
                v.push(2);
                v.push(3);
                v.push(4);
                v
            };
            acc += black_box(&v)[0];
        }
        acc
    });
    line("13_macros", format!(
        "myvec! = {ms_my:.2} ms   hand-written = {ms_hand:.2} ms   ratio {:.2}x (macro adds nothing at runtime)",
        ms_my / ms_hand.max(f64::MIN_POSITIVE)
    ));
}

// --- 14 async: per-await overhead of the hand-built executor -----------------
fn bench_14_async() {
    use std::future::Future;
    use std::pin::Pin;
    use std::sync::Arc;
    use std::task::{Context, Poll, RawWaker, RawWakerVTable, Waker};
    use std::thread::{self, Thread};

    fn thread_waker(thread: Arc<Thread>) -> Waker {
        fn clone(p: *const ()) -> RawWaker {
            let a = unsafe { Arc::from_raw(p as *const Thread) };
            let c = Arc::clone(&a);
            std::mem::forget(a);
            RawWaker::new(Arc::into_raw(c) as *const (), &VT)
        }
        fn wake(p: *const ()) {
            let a = unsafe { Arc::from_raw(p as *const Thread) };
            a.unpark();
        }
        fn wake_ref(p: *const ()) {
            let a = unsafe { Arc::from_raw(p as *const Thread) };
            a.unpark();
            std::mem::forget(a);
        }
        fn drop_w(p: *const ()) {
            unsafe { drop(Arc::from_raw(p as *const Thread)) };
        }
        static VT: RawWakerVTable = RawWakerVTable::new(clone, wake, wake_ref, drop_w);
        unsafe { Waker::from_raw(RawWaker::new(Arc::into_raw(thread) as *const (), &VT)) }
    }
    fn block_on<F: Future>(f: F) -> F::Output {
        let mut f = Box::pin(f);
        let w = thread_waker(Arc::new(thread::current()));
        let mut cx = Context::from_waker(&w);
        loop {
            match f.as_mut().poll(&mut cx) {
                Poll::Ready(v) => return v,
                Poll::Pending => thread::park(),
            }
        }
    }
    struct Yield(bool);
    impl Future for Yield {
        type Output = ();
        fn poll(mut self: Pin<&mut Self>, cx: &mut Context<'_>) -> Poll<()> {
            if self.0 {
                Poll::Ready(())
            } else {
                self.0 = true;
                cx.waker().wake_by_ref();
                Poll::Pending
            }
        }
    }
    const YIELDS: u64 = 2_000_000;
    let (_a, ms) = best_ms(|| {
        block_on(async {
            let mut acc = 0i64;
            for i in 0..YIELDS {
                Yield(false).await;
                acc += i as i64;
            }
            acc
        })
    });
    line(
        "14_async",
        format!(
            "block_on {YIELDS} self-wake yields = {ms:.2} ms   {:.1} ns per poll/await round-trip",
            ms * 1e6 / YIELDS as f64
        ),
    );
}

// --- 15 zero-cost: newtype (repr transparent) vs raw i64 ---------------------
fn bench_15_zerocost() {
    #[repr(transparent)]
    #[derive(Clone, Copy)]
    struct Ticks(i64);
    fn sum_raw(xs: &[i64]) -> i64 {
        let mut s = 0;
        for &x in xs {
            s += x;
        }
        s
    }
    fn sum_nt(xs: &[Ticks]) -> i64 {
        let mut s = 0;
        for &Ticks(x) in xs {
            s += x;
        }
        s
    }
    let raw: Vec<i64> = (0..50_000_000).collect();
    let wrapped: Vec<Ticks> = raw.iter().map(|&x| Ticks(x)).collect();
    let raw = black_box(raw);
    let wrapped = black_box(wrapped);
    let (_a, ms_raw) = best_ms(|| sum_raw(black_box(&raw)));
    let (_b, ms_nt) = best_ms(|| sum_nt(black_box(&wrapped)));
    line(
        "15_zerocost",
        format!(
        "raw i64 = {ms_raw:.2} ms   newtype = {ms_nt:.2} ms   ratio {:.2}x (abstraction is free)",
        ms_nt / ms_raw.max(f64::MIN_POSITIVE)
    ),
    );
}

fn main() {
    println!("zero_to_expert micro-benchmarks (best of {TRIALS} trials, black_box guarded)\n");
    bench_01_ownership();
    bench_02_match();
    bench_03_errors();
    bench_04_iterators();
    bench_05_generics();
    bench_06_dispatch();
    bench_07_closures();
    bench_08_lifetimes();
    bench_09_smart_pointers();
    bench_10_concurrency();
    bench_11_atomics();
    bench_12_unsafe();
    bench_13_macros();
    bench_14_async();
    bench_15_zerocost();
}
