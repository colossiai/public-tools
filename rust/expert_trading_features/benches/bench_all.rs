// ============================================================================
// bench_all — std-only micro-benchmarks behind the reports in bench_intel_mac/
// Run:  cargo bench            (release build, harness disabled — see Cargo.toml)
// ----------------------------------------------------------------------------
// One section per demo, each printing a labeled line the matching report
// transcribes. Methodology mirrors the rest of the repo: best-of-N trials (the
// min filters scheduler/frequency jitter) and `black_box` on inputs/outputs so
// the optimizer can't hoist work out of the loop or constant-fold the answer.
//
// The data-structure demos reimplement a compact version of the example's type
// here (examples aren't importable as library modules); the logic matches.
// ============================================================================

use expert_trading_features::CachePadded;
use std::cell::UnsafeCell;
use std::hint::black_box;
use std::mem::MaybeUninit;
use std::sync::atomic::{fence, AtomicUsize, Ordering};
use std::sync::Arc;
use std::time::Instant;

const TRIALS: usize = 7;

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
    println!("{demo:<28} {msg}");
}

// --- 01 fixed-point: integer-tick add+compare vs f64 ------------------------
fn bench_01_fixed_point() {
    const N: usize = 100_000_000;
    let (_a, ms_fp) = best_ms(|| {
        let mut acc = 0i64;
        let mut hits = 0i64;
        let step = black_box(1i64); // opaque => the dependent add chain can't fold
        for _ in 0..N {
            acc += step;
            if acc >= step {
                hits += 1;
            }
        }
        black_box(acc);
        hits
    });
    let (_b, ms_f) = best_ms(|| {
        let mut acc = 0.0f64;
        let mut hits = 0i64;
        let step = black_box(0.0001f64);
        for _ in 0..N {
            acc += step;
            if acc >= step {
                hits += 1;
            }
        }
        black_box(acc as i64);
        hits
    });
    line(
        "01_fixed_point",
        format!("add+compare: int = {ms_fp:.2} ms   f64 = {ms_f:.2} ms   ratio {:.2}x (exact, no slower)", ms_f / ms_fp.max(f64::MIN_POSITIVE)),
    );
}

// --- 02 SPSC ring throughput (compact reimplementation of the example) -------
mod spsc {
    use super::*;
    pub struct Ring<T> {
        pub buf: Box<[UnsafeCell<MaybeUninit<T>>]>,
        pub mask: usize,
        pub head: CachePadded<AtomicUsize>,
        pub tail: CachePadded<AtomicUsize>,
    }
    unsafe impl<T: Send> Sync for Ring<T> {}
    unsafe impl<T: Send> Send for Ring<T> {}
    pub struct Tx<T> {
        pub r: Arc<Ring<T>>,
        pub ct: usize,
    }
    pub struct Rx<T> {
        pub r: Arc<Ring<T>>,
        pub ch: usize,
    }
    unsafe impl<T: Send> Send for Tx<T> {}
    unsafe impl<T: Send> Send for Rx<T> {}
    pub fn channel<T: Send>(cap: usize) -> (Tx<T>, Rx<T>) {
        let buf = (0..cap)
            .map(|_| UnsafeCell::new(MaybeUninit::uninit()))
            .collect::<Vec<_>>()
            .into_boxed_slice();
        let r = Arc::new(Ring {
            buf,
            mask: cap - 1,
            head: CachePadded::new(AtomicUsize::new(0)),
            tail: CachePadded::new(AtomicUsize::new(0)),
        });
        (
            Tx {
                r: Arc::clone(&r),
                ct: 0,
            },
            Rx { r, ch: 0 },
        )
    }
    impl<T> Tx<T> {
        #[inline]
        pub fn push(&mut self, v: T) -> Result<(), T> {
            let cap = self.r.buf.len();
            let head = self.r.head.load(Ordering::Relaxed);
            let next = head.wrapping_add(1);
            if next.wrapping_sub(self.ct) > cap {
                self.ct = self.r.tail.load(Ordering::Acquire);
                if next.wrapping_sub(self.ct) > cap {
                    return Err(v);
                }
            }
            unsafe { (*self.r.buf[head & self.r.mask].get()).write(v) };
            self.r.head.store(next, Ordering::Release);
            Ok(())
        }
    }
    impl<T> Rx<T> {
        #[inline]
        pub fn pop(&mut self) -> Option<T> {
            let tail = self.r.tail.load(Ordering::Relaxed);
            if tail == self.ch {
                self.ch = self.r.head.load(Ordering::Acquire);
                if tail == self.ch {
                    return None;
                }
            }
            let v = unsafe { (*self.r.buf[tail & self.r.mask].get()).assume_init_read() };
            self.r.tail.store(tail.wrapping_add(1), Ordering::Release);
            Some(v)
        }
    }
}

fn bench_02_spsc() {
    use std::thread;
    const N: u64 = 5_000_000;
    let run = || {
        let (mut tx, mut rx) = spsc::channel::<u64>(1024);
        let c = thread::spawn(move || {
            let (mut got, mut sum) = (0u64, 0i64);
            while got < N {
                if let Some(v) = rx.pop() {
                    sum = sum.wrapping_add(v as i64);
                    got += 1;
                } else {
                    std::hint::spin_loop();
                }
            }
            sum
        });
        for i in 0..N {
            while tx.push(i).is_err() {
                std::hint::spin_loop();
            }
        }
        c.join().unwrap()
    };
    let (_s, ms) = best_ms(run);
    let per = ms * 1e6 / N as f64;
    line(
        "02_spsc_ring",
        format!(
            "{per:.2} ns/tick   {:.0}M ticks/s   (5M ticks, lock-free)",
            (N as f64 / (ms * 1e6)) * 1000.0
        ),
    );
}

// --- 03 false sharing: packed vs cache-padded counters -----------------------
fn bench_03_false_sharing() {
    use std::sync::atomic::AtomicU64;
    use std::thread;
    const ITERS: u64 = 100_000_000;
    let hammer = |x: &AtomicU64| {
        for _ in 0..ITERS {
            x.fetch_add(1, Ordering::Relaxed);
        }
    };
    let bench = |a: &AtomicU64, b: &AtomicU64| -> f64 {
        let t = Instant::now();
        thread::scope(|s| {
            s.spawn(|| hammer(a));
            s.spawn(|| hammer(b));
        });
        t.elapsed().as_secs_f64() * 1e9 / (2.0 * ITERS as f64)
    };
    #[derive(Default)]
    struct Packed {
        a: AtomicU64,
        b: AtomicU64,
    }
    #[derive(Default)]
    struct Padded {
        a: CachePadded<AtomicU64>,
        b: CachePadded<AtomicU64>,
    }
    let p = Packed::default();
    let q = Padded::default();
    let mut packed = f64::MAX;
    let mut padded = f64::MAX;
    for _ in 0..3 {
        packed = packed.min(bench(&p.a, &p.b));
        padded = padded.min(bench(&q.a, &q.b));
    }
    line(
        "03_false_sharing",
        format!(
            "packed = {packed:.2} ns/op   padded = {padded:.2} ns/op   speedup {:.2}x",
            packed / padded
        ),
    );
}

// --- 04 object pool: acquire/release vs Box::new/drop -----------------------
fn bench_04_object_pool() {
    #[derive(Clone, Copy)]
    struct Order {
        id: u64,
        price: i64,
    }
    struct Pool {
        slots: Vec<MaybeUninit<Order>>,
        next: Vec<usize>,
        head: usize,
    }
    const NIL: usize = usize::MAX;
    impl Pool {
        fn new(n: usize) -> Self {
            let slots = (0..n).map(|_| MaybeUninit::uninit()).collect();
            let next = (0..n)
                .map(|i| if i + 1 < n { i + 1 } else { NIL })
                .collect();
            Pool {
                slots,
                next,
                head: 0,
            }
        }
        #[inline]
        fn acquire(&mut self, v: Order) -> usize {
            let i = self.head;
            self.head = self.next[i];
            self.slots[i].write(v);
            i
        }
        #[inline]
        fn release(&mut self, i: usize) -> Order {
            let v = unsafe { self.slots[i].assume_init_read() };
            self.next[i] = self.head;
            self.head = i;
            v
        }
    }
    const N: usize = 20_000_000;
    let mut pool = Pool::new(1024);
    let (_a, ms_pool) = best_ms(|| {
        let mut sink = 0i64;
        for i in 0..N as u64 {
            let h = pool.acquire(Order {
                id: i,
                price: 1_000_000 + (i & 1023) as i64,
            });
            let o = pool.release(black_box(h));
            sink = sink.wrapping_add(o.id as i64 ^ o.price);
        }
        sink
    });
    let (_b, ms_heap) = best_ms(|| {
        let mut sink = 0i64;
        for i in 0..N as u64 {
            let o = Box::new(Order {
                id: i,
                price: 1_000_000 + (i & 1023) as i64,
            });
            let o = black_box(o); // force the allocation to actually happen
            sink = sink.wrapping_add(o.id as i64 ^ o.price);
            drop(o);
        }
        sink
    });
    let pool_ns = ms_pool * 1e6 / N as f64;
    let heap_ns = ms_heap * 1e6 / N as f64;
    line(
        "04_object_pool",
        format!(
            "pool = {pool_ns:.2} ns/op   Box::new/drop = {heap_ns:.2} ns/op   speedup {:.2}x",
            heap_ns / pool_ns.max(f64::MIN_POSITIVE)
        ),
    );
}

// --- 05 order book: flat array vs BTreeMap (steady-state, populated book) ----
fn bench_05_order_book() {
    use std::collections::BTreeMap;
    const MAXT: usize = 1 << 16;
    const N: usize = 5_000_000;
    const CENTER: i32 = 32_768;
    const BAND: i32 = 1_000;

    let mut st: u64 = 0xC0FFEE;
    let ticks: Vec<i32> = (0..N)
        .map(|_| {
            st = st.wrapping_mul(6364136223846793005).wrapping_add(1);
            CENTER - BAND + ((st >> 33) % (2 * BAND as u64 + 1)) as i32
        })
        .collect();
    let ticks = black_box(ticks);

    let mut arr = vec![0u64; MAXT];
    let mut best = -1i32;
    for t in CENTER - BAND..=CENTER + BAND {
        arr[t as usize] = 100;
        best = best.max(t);
    }
    let (_a, ms_arr) = best_ms(|| {
        let mut sink = 0i64;
        for &t in &ticks {
            arr[t as usize] += 1;
            if t > best {
                best = t;
            }
            sink += best as i64;
            arr[t as usize] -= 1;
        }
        sink
    });

    let mut map: BTreeMap<i32, u64> = BTreeMap::new();
    for t in CENTER - BAND..=CENTER + BAND {
        map.insert(t, 100);
    }
    let (_b, ms_map) = best_ms(|| {
        let mut sink = 0i64;
        for &t in &ticks {
            *map.get_mut(&t).unwrap() += 1;
            sink += *map.keys().next_back().unwrap() as i64;
            *map.get_mut(&t).unwrap() -= 1;
        }
        sink
    });
    let arr_ns = ms_arr * 1e6 / N as f64;
    let map_ns = ms_map * 1e6 / N as f64;
    line(
        "05_order_book",
        format!(
            "array = {arr_ns:.2} ns/op   BTreeMap = {map_ns:.2} ns/op   speedup {:.1}x",
            map_ns / arr_ns.max(f64::MIN_POSITIVE)
        ),
    );
}

// --- 06 branchless vs branchy vs prefetch -----------------------------------
fn bench_06_branchless() {
    const N: usize = 1 << 22;
    let mut st: u64 = 0x1234_5678;
    let data: Vec<i32> = (0..N)
        .map(|_| {
            st = st
                .wrapping_mul(6364136223846793005)
                .wrapping_add(1442695040888963407);
            ((st >> 33) % 100) as i32
        })
        .collect();
    let data = black_box(data);
    let (_a, ms_by) = best_ms(|| {
        let mut s = 0i64;
        for &v in black_box(&data) {
            if v >= 50 {
                s += v as i64;
            }
        }
        s
    });
    let (_b, ms_bl) = best_ms(|| {
        let mut s = 0i64;
        for &v in black_box(&data) {
            let mask = -((v >= 50) as i64);
            s += (v as i64) & mask;
        }
        s
    });
    line(
        "06_branchless",
        format!(
            "branchy = {:.3} ns/el   branchless = {:.3} ns/el   ratio {:.2}x (often a tie at -O3)",
            ms_by * 1e6 / N as f64,
            ms_bl * 1e6 / N as f64,
            ms_by / ms_bl.max(f64::MIN_POSITIVE)
        ),
    );
}

// --- 07 rdtscp encode latency percentiles -----------------------------------
fn bench_07_timestamp() {
    #[inline(never)]
    fn encode(id: u64, px: i64, qty: u32) -> u64 {
        let mut h = id.wrapping_mul(1099511628211);
        h ^= px as u64;
        h = h.wrapping_mul(1099511628211);
        h ^ qty as u64
    }
    #[cfg(target_arch = "x86_64")]
    let (ticks, tpns): (fn() -> u64, f64) = {
        use core::arch::x86_64::{__rdtscp, _mm_lfence, _rdtsc};
        fn t() -> u64 {
            unsafe {
                _mm_lfence();
                let mut a = 0u32;
                let v = __rdtscp(&mut a);
                _mm_lfence();
                v
            }
        }
        let w = Instant::now();
        let c0 = unsafe { _rdtsc() };
        while w.elapsed() < std::time::Duration::from_millis(50) {
            std::hint::spin_loop();
        }
        let c1 = unsafe { _rdtsc() };
        (
            t as fn() -> u64,
            (c1 - c0) as f64 / (w.elapsed().as_secs_f64() * 1e9),
        )
    };
    #[cfg(not(target_arch = "x86_64"))]
    let (ticks, tpns): (fn() -> u64, f64) = (
        (|| Instant::now().elapsed().as_nanos() as u64) as fn() -> u64,
        1.0,
    );

    const M: usize = 200_000;
    let mut ns: Vec<f64> = Vec::with_capacity(M);
    let mut sink = 0u64;
    for i in 0..M as u64 {
        let s = ticks();
        sink ^= encode(i, 1_000_000 + (i % 7) as i64, 100);
        let e = ticks();
        ns.push((e - s) as f64 / tpns);
    }
    black_box(sink);
    ns.sort_by(|a, b| a.partial_cmp(b).unwrap());
    let pct = |p: f64| ns[((p / 100.0) * (ns.len() - 1) as f64) as usize];
    line(
        "07_timestamp",
        format!(
            "encode_order: p50={:.1} p99={:.1} p99.9={:.1} max={:.0} ns",
            pct(50.0),
            pct(99.0),
            pct(99.9),
            ns[ns.len() - 1]
        ),
    );
}

// --- 08 dispatch: enum (static) vs Box<dyn> (opaque, vtable) -----------------
fn bench_08_dispatch() {
    #[derive(Clone, Copy)]
    struct Tick {
        price: i64,
        qty: u32,
    }
    trait Strategy {
        fn on_tick(&mut self, t: Tick);
        fn pnl(&self) -> i64;
    }
    struct Mom {
        acc: i64,
        last: i64,
    }
    impl Strategy for Mom {
        fn on_tick(&mut self, t: Tick) {
            self.acc += (t.price - self.last) * t.qty as i64;
            self.last = t.price;
        }
        fn pnl(&self) -> i64 {
            self.acc
        }
    }
    struct MeanRev {
        acc: i64,
        fair: i64,
    }
    impl Strategy for MeanRev {
        fn on_tick(&mut self, t: Tick) {
            self.acc += (self.fair - t.price) * t.qty as i64;
        }
        fn pnl(&self) -> i64 {
            self.acc
        }
    }
    // Two arms returning different concrete types => the caller genuinely can't
    // know which, so the vtable call can't be devirtualized back to a direct one.
    #[inline(never)]
    fn make(k: u8) -> Box<dyn Strategy> {
        match k {
            0 => Box::new(Mom { acc: 0, last: 0 }),
            _ => Box::new(MeanRev {
                acc: 0,
                fair: 1_000_050,
            }),
        }
    }
    enum Strat {
        Mom { acc: i64, last: i64 },
    }
    impl Strat {
        #[inline(always)]
        fn on_tick(&mut self, t: Tick) {
            match self {
                Strat::Mom { acc, last } => {
                    *acc += (t.price - *last) * t.qty as i64;
                    *last = t.price;
                }
            }
        }
        fn pnl(&self) -> i64 {
            match self {
                Strat::Mom { acc, .. } => *acc,
            }
        }
    }
    const N: usize = 20_000_000;
    let feed: Vec<Tick> = (0..N)
        .map(|i| Tick {
            price: 1_000_000 + (i % 100) as i64,
            qty: 10,
        })
        .collect();
    let feed = black_box(feed);
    let (_a, ms_dyn) = best_ms(|| {
        let mut s = make(black_box(0));
        for &t in &feed {
            s.on_tick(t);
        }
        s.pnl()
    });
    let (_b, ms_enum) = best_ms(|| {
        let mut s = Strat::Mom { acc: 0, last: 0 };
        for &t in &feed {
            s.on_tick(t);
        }
        s.pnl()
    });
    line(
        "08_dispatch",
        format!(
            "dyn = {:.3} ns/tick   enum = {:.3} ns/tick   dyn/enum {:.2}x",
            ms_dyn * 1e6 / N as f64,
            ms_enum * 1e6 / N as f64,
            ms_dyn / ms_enum.max(f64::MIN_POSITIVE)
        ),
    );
}

// --- 09 seqlock read vs Mutex read (uncontended snapshot) -------------------
fn bench_09_seqlock() {
    #[derive(Clone, Copy)]
    struct Tob {
        bid: i64,
        ask: i64,
        bs: u64,
        a_s: u64,
    }
    struct SeqLock<T> {
        seq: AtomicUsize,
        data: UnsafeCell<T>,
    }
    unsafe impl<T: Send> Sync for SeqLock<T> {}
    impl<T: Copy> SeqLock<T> {
        fn new(v: T) -> Self {
            SeqLock {
                seq: AtomicUsize::new(0),
                data: UnsafeCell::new(v),
            }
        }
        fn read(&self) -> T {
            loop {
                let s1 = self.seq.load(Ordering::Acquire);
                if s1 & 1 != 0 {
                    continue;
                }
                let v = unsafe { std::ptr::read_volatile(self.data.get()) };
                fence(Ordering::Acquire);
                if self.seq.load(Ordering::Relaxed) == s1 {
                    return v;
                }
            }
        }
    }
    const N: usize = 50_000_000;
    let sl = SeqLock::new(Tob {
        bid: 100,
        ask: 200,
        bs: 1,
        a_s: 1,
    });
    let (_a, ms_seq) = best_ms(|| {
        let mut acc = 0i64;
        for _ in 0..N {
            let t = black_box(&sl).read();
            acc = acc.wrapping_add(t.bid + t.ask + t.bs as i64 + t.a_s as i64);
        }
        acc
    });
    let mtx = std::sync::Mutex::new(Tob {
        bid: 100,
        ask: 200,
        bs: 1,
        a_s: 1,
    });
    let (_b, ms_mtx) = best_ms(|| {
        let mut acc = 0i64;
        for _ in 0..N {
            let t = *black_box(&mtx).lock().unwrap();
            acc = acc.wrapping_add(t.bid + t.ask + t.bs as i64 + t.a_s as i64);
        }
        acc
    });
    line(
        "09_seqlock",
        format!(
            "seqlock read = {:.2} ns   Mutex read = {:.2} ns   speedup {:.2}x",
            ms_seq * 1e6 / N as f64,
            ms_mtx * 1e6 / N as f64,
            ms_mtx / ms_seq.max(f64::MIN_POSITIVE)
        ),
    );
}

// --- 10 typestate: same lifecycle, runtime-tagged FSM vs zero-cost type-state -
// Both run submit -> ack -> fill with identical arithmetic. The runtime FSM
// carries a `state` tag and asserts the transition each step; the type-state
// version carries neither (transitions are moves the optimizer elides) and its
// safety is enforced entirely at compile time.
fn bench_10_typestate() {
    const N: usize = 50_000_000;

    // Runtime-checked finite state machine.
    #[derive(Clone, Copy, PartialEq)]
    enum S {
        Pending,
        Live,
        Done,
    }
    struct Rt {
        state: S,
        qty: u32,
        filled: u32,
    }
    impl Rt {
        #[inline]
        fn submit(qty: u32) -> Self {
            Rt {
                state: S::Pending,
                qty,
                filled: 0,
            }
        }
        #[inline]
        fn ack(&mut self) {
            assert!(self.state == S::Pending);
            self.state = S::Live;
        }
        #[inline]
        fn fill(&mut self, n: u32) -> bool {
            assert!(self.state == S::Live);
            self.filled += n;
            if self.filled >= self.qty {
                self.state = S::Done;
                true
            } else {
                false
            }
        }
    }
    let (_a, ms_rt) = best_ms(|| {
        let mut sink = 0i64;
        for i in 0..N as u32 {
            let mut o = Rt::submit(10);
            o.ack();
            let done = o.fill(black_box(i % 10 + 1));
            sink += o.filled as i64 + done as i64;
        }
        sink
    });

    // Type-state: the state lives in the type; transitions are moves.
    use std::marker::PhantomData;
    struct Pending;
    struct Live;
    struct O<St> {
        qty: u32,
        filled: u32,
        _s: PhantomData<St>,
    }
    impl O<Pending> {
        #[inline]
        fn submit(qty: u32) -> Self {
            O {
                qty,
                filled: 0,
                _s: PhantomData,
            }
        }
        #[inline]
        fn ack(self) -> O<Live> {
            O {
                qty: self.qty,
                filled: self.filled,
                _s: PhantomData,
            }
        }
    }
    impl O<Live> {
        #[inline]
        fn fill(mut self, n: u32) -> (bool, Self) {
            self.filled += n;
            (self.filled >= self.qty, self)
        }
    }
    let (_b, ms_ts) = best_ms(|| {
        let mut sink = 0i64;
        for i in 0..N as u32 {
            let o = O::<Pending>::submit(10).ack();
            let (done, o) = o.fill(black_box(i % 10 + 1));
            sink += o.filled as i64 + done as i64;
        }
        sink
    });
    line("10_typestate", format!("runtime-tagged FSM = {ms_rt:.2} ms   type-state = {ms_ts:.2} ms   ratio {:.2}x (no tag/checks at runtime)", ms_rt / ms_ts.max(f64::MIN_POSITIVE)));
}

// --- 11 zero-copy view vs owned-copy parse ----------------------------------
fn bench_11_zero_copy() {
    #[repr(C)]
    struct Add {
        msg_type: u8,
        order_id: [u8; 8],
        side: u8,
        price: [u8; 8],
        qty: [u8; 4],
    }
    const LEN: usize = std::mem::size_of::<Add>();
    fn view(b: &[u8]) -> &Add {
        unsafe { &*(b.as_ptr() as *const Add) }
    }
    struct Owned {
        price: i64,
        qty: u32,
    }
    fn owned(b: &[u8]) -> Owned {
        let m = view(b);
        Owned {
            price: i64::from_be_bytes(m.price),
            qty: u32::from_be_bytes(m.qty),
        }
    }
    const MSGS: usize = 2_000_000;
    let mut buf = Vec::with_capacity(MSGS * LEN);
    for i in 0..MSGS as u64 {
        buf.push(b'A');
        buf.extend_from_slice(&i.to_be_bytes());
        buf.push(b'B');
        buf.extend_from_slice(&(1_000_000i64 + i as i64).to_be_bytes());
        buf.extend_from_slice(&100u32.to_be_bytes());
    }
    let buf = black_box(buf);
    let (_a, ms_view) = best_ms(|| {
        let mut n = 0i128;
        let mut off = 0;
        for _ in 0..MSGS {
            let m = view(&buf[off..off + LEN]);
            n += i64::from_be_bytes(m.price) as i128 * u32::from_be_bytes(m.qty) as i128;
            off += LEN;
        }
        n as i64
    });
    let (_b, ms_owned) = best_ms(|| {
        let mut n = 0i128;
        let mut off = 0;
        for _ in 0..MSGS {
            let o = black_box(owned(&buf[off..off + LEN]));
            n += o.price as i128 * o.qty as i128;
            off += LEN;
        }
        n as i64
    });
    line("11_zero_copy", format!("view = {ms_view:.2} ms   owned-copy = {ms_owned:.2} ms   ratio {:.2}x (view also avoids all allocation)", ms_owned / ms_view.max(f64::MIN_POSITIVE)));
}

fn main() {
    println!(
        "expert_trading_features micro-benchmarks (best of {TRIALS} trials, black_box guarded)\n"
    );
    bench_01_fixed_point();
    bench_02_spsc();
    bench_03_false_sharing();
    bench_04_object_pool();
    bench_05_order_book();
    bench_06_branchless();
    bench_07_timestamp();
    bench_08_dispatch();
    bench_09_seqlock();
    bench_10_typestate();
    bench_11_zero_copy();
}
