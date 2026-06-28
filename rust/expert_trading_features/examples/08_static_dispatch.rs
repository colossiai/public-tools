// ============================================================================
// 08 — Static dispatch (enum / generics) instead of dynamic on the hot path
// Run:  cargo run --release --example 08_static_dispatch
// C++ counterpart: cpp/expert_trading_features/08_static_dispatch_crtp.cpp
// ----------------------------------------------------------------------------
// A `dyn Trait` call is an indirect jump through a vtable: the CPU can't inline
// it, may mispredict the target, and loses cross-call optimization. On a per-tick
// strategy callback fired millions of times, that adds up.
//
// What Rust changes vs C++ (CRTP):
//   * C++ reaches for CRTP to get static dispatch. Rust's idiomatic equivalent is
//     an ENUM over the closed set of strategies + `match`: the call site is fully
//     known to the compiler, so each arm inlines — no vtable, no boxing, and you
//     can still hold heterogeneous strategies in one `Vec<Strategy>`.
//   * Generics (`impl Strategy`) give the same static dispatch for a single type.
//   * We benchmark enum dispatch vs `Box<dyn Strategy>` over the same tick stream.
// ============================================================================

#[derive(Clone, Copy)]
struct Tick {
    price: i64,
    qty: u32,
}

// ---------- Dynamic polymorphism (Box<dyn>): flexible but uninlinable ----------
trait Strategy {
    fn on_tick(&mut self, t: Tick);
    fn pnl(&self) -> i64;
}

struct Momentum {
    acc: i64,
    last: i64,
}
impl Strategy for Momentum {
    fn on_tick(&mut self, t: Tick) {
        self.acc += (t.price - self.last) * t.qty as i64;
        self.last = t.price;
    }
    fn pnl(&self) -> i64 {
        self.acc
    }
}

struct MeanReversion {
    acc: i64,
    fair: i64,
}
impl Strategy for MeanReversion {
    fn on_tick(&mut self, t: Tick) {
        self.acc += (self.fair - t.price) * t.qty as i64;
    }
    fn pnl(&self) -> i64 {
        self.acc
    }
}

// An opaque factory: returning `Box<dyn Strategy>` from an `#[inline(never)]` fn
// hides the concrete type from the caller, so the compiler CANNOT devirtualize
// the `on_tick` call back into a direct one. Without this, LLVM often sees the
// concrete `Momentum` and inlines it, erasing the very cost we want to show.
#[inline(never)]
fn make_strategy(kind: u8) -> Box<dyn Strategy> {
    match kind {
        0 => Box::new(Momentum { acc: 0, last: 0 }),
        _ => Box::new(MeanReversion {
            acc: 0,
            fair: 1_000_050,
        }),
    }
}

// ---------- Static polymorphism (enum + match): inlines into the loop ----------
// The set of strategies is closed and known at compile time, so `match` dispatch
// is a direct, inlinable call — the Rust analog of CRTP.
enum Strat {
    Momentum { acc: i64, last: i64 },
    MeanRev { acc: i64, fair: i64 },
}
impl Strat {
    #[inline(always)]
    fn on_tick(&mut self, t: Tick) {
        match self {
            Strat::Momentum { acc, last } => {
                *acc += (t.price - *last) * t.qty as i64;
                *last = t.price;
            }
            Strat::MeanRev { acc, fair } => {
                *acc += (*fair - t.price) * t.qty as i64;
            }
        }
    }
    fn pnl(&self) -> i64 {
        match self {
            Strat::Momentum { acc, .. } | Strat::MeanRev { acc, .. } => *acc,
        }
    }
}

fn main() {
    use std::hint::black_box;
    const N: usize = 20_000_000;
    let feed: Vec<Tick> = (0..N)
        .map(|i| Tick {
            price: 1_000_000 + (i % 100) as i64,
            qty: 10,
        })
        .collect();

    // Dynamic dispatch through a trait object whose concrete type is hidden
    // (the realistic, pessimistic case): each on_tick is an indirect vtable call.
    let mut dynamic = make_strategy(black_box(0));
    let t0 = std::time::Instant::now();
    for &t in &feed {
        dynamic.on_tick(t);
    }
    let ns_dyn = t0.elapsed().as_secs_f64() * 1e9 / N as f64;

    // Enum (static) dispatch: the match arm inlines into the loop.
    let mut s = Strat::Momentum { acc: 0, last: 0 };
    let t1 = std::time::Instant::now();
    for &t in &feed {
        s.on_tick(t);
    }
    let ns_enum = t1.elapsed().as_secs_f64() * 1e9 / N as f64;

    println!("dyn  on_tick : {ns_dyn:.3} ns/tick  pnl={}", dynamic.pnl());
    println!(
        "enum on_tick : {ns_enum:.3} ns/tick  pnl={}  (speedup {:.2}x)",
        s.pnl(),
        ns_dyn / ns_enum
    );

    // A heterogeneous set of strategies, both ways: a closed enum set dispatches
    // statically via `match`; trait objects dispatch through the vtable.
    let mut enum_book = [
        Strat::Momentum { acc: 0, last: 0 },
        Strat::MeanRev {
            acc: 0,
            fair: 1_000_050,
        },
    ];
    let mut dyn_book: Vec<Box<dyn Strategy>> =
        vec![make_strategy(black_box(0)), make_strategy(black_box(1))];
    for &t in feed.iter().take(1000) {
        for s in &mut enum_book {
            s.on_tick(t);
        }
        for d in &mut dyn_book {
            d.on_tick(t);
        }
    }
    println!(
        "heterogeneous: enum pnls {:?}, dyn pnls {:?}",
        enum_book.iter().map(|s| s.pnl()).collect::<Vec<_>>(),
        dyn_book.iter().map(|d| d.pnl()).collect::<Vec<_>>()
    );
    println!("note: the win grows with smaller callback bodies and tighter loops.");
}

#[cfg(test)]
mod tests {
    use super::*;

    fn run<F: FnMut(Tick)>(mut f: F) {
        for i in 0..100u64 {
            f(Tick {
                price: 1000 + i as i64,
                qty: 1,
            });
        }
    }

    #[test]
    fn enum_and_dyn_agree_for_momentum() {
        let mut d: Box<dyn Strategy> = Box::new(Momentum { acc: 0, last: 0 });
        run(|t| d.on_tick(t));
        let mut e = Strat::Momentum { acc: 0, last: 0 };
        run(|t| e.on_tick(t));
        assert_eq!(d.pnl(), e.pnl());
    }

    #[test]
    fn heterogeneous_enum_vec_dispatches() {
        let mut strats = vec![
            Strat::Momentum { acc: 0, last: 0 },
            Strat::MeanRev { acc: 0, fair: 1050 },
        ];
        for s in &mut strats {
            run(|t| s.on_tick(t));
        }
        assert_eq!(strats.len(), 2);
        // MeanRev fair=1050 vs prices 1000..1100 → net pnl is finite/representable.
        let _total: i64 = strats.iter().map(|s| s.pnl()).sum();
    }
}
