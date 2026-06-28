# Rust: Zero to Expert

A progressive tour of Rust as **runnable, self-contained demos** — from the borrow
checker up to a hand-built async executor and zero-cost type-state APIs. Each demo is
one file in [`examples/`](examples/): heavily commented, prints what it teaches, and
carries its own `#[test]`s so the claims are checked, not just asserted in prose.

> Teaching demos, not a framework. The point is the *concept* and *why Rust does it
> this way*, with the trade-offs called out honestly. Zero external dependencies —
> everything is `std` only, including the async runtime in demo 14.

## The demos

| # | File | Topic | What it shows |
|---|------|-------|---------------|
| 01 | [`01_ownership_and_borrowing.rs`](examples/01_ownership_and_borrowing.rs) | **Ownership & borrowing** | move vs copy, shared/`&mut` borrows, why the aliasing bug can't compile |
| 02 | [`02_structs_enums_matching.rs`](examples/02_structs_enums_matching.rs) | **Structs, enums, `match`** | sum types, exhaustive matching, `Option`/`if let`/`let-else` |
| 03 | [`03_error_handling.rs`](examples/03_error_handling.rs) | **Error handling** | `Result`, the `?` operator, custom error enums, `From`, `Box<dyn Error>` |
| 04 | [`04_collections_and_iterators.rs`](examples/04_collections_and_iterators.rs) | **Collections & iterators** | lazy adapter chains, `Vec`/`HashMap`/`BTreeMap`, `collect` into `Result` |
| 05 | [`05_generics_and_traits.rs`](examples/05_generics_and_traits.rs) | **Generics & traits** | trait bounds, default methods, operator overloading, `From`/`Into` |
| 06 | [`06_trait_objects_and_dispatch.rs`](examples/06_trait_objects_and_dispatch.rs) | **Static vs dynamic dispatch** | generics vs `dyn Trait`, fat pointers, object safety, heterogeneous collections |
| 07 | [`07_closures.rs`](examples/07_closures.rs) | **Closures** | `Fn`/`FnMut`/`FnOnce`, capture modes, `move`, returning & boxing closures |
| 08 | [`08_lifetimes.rs`](examples/08_lifetimes.rs) | **Lifetimes** | explicit `'a`, structs holding references, elision, `'static` |
| 09 | [`09_smart_pointers.rs`](examples/09_smart_pointers.rs) | **Smart pointers** | `Box` (recursion), `Rc`/`RefCell` (shared mutability), `Weak` (cycle breaking) |
| 10 | [`10_concurrency.rs`](examples/10_concurrency.rs) | **Fearless concurrency** | threads, `Arc<Mutex>`, `mpsc` channels, scoped threads |
| 11 | [`11_atomics_and_send_sync.rs`](examples/11_atomics_and_send_sync.rs) | **Atomics & `Send`/`Sync`** | lock-free counter, memory `Ordering`, a hand-built spinlock, marker traits |
| 12 | [`12_unsafe_and_ffi.rs`](examples/12_unsafe_and_ffi.rs) | **Unsafe & FFI** | raw pointers, a safe `split_at_mut`, `MaybeUninit`, `extern "C"`, `repr(C)` |
| 13 | [`13_macros.rs`](examples/13_macros.rs) | **Declarative macros** | `macro_rules!`, repetition, building `vec!`/`hashmap!`, generating items |
| 14 | [`14_async_executor.rs`](examples/14_async_executor.rs) | **Async from scratch** | the `Future`/`Poll`/`Waker` machinery and a working `block_on`, no crates |
| 15 | [`15_typestate_and_zerocost.rs`](examples/15_typestate_and_zerocost.rs) | **Type-state & zero-cost** | a builder that won't compile when misused; a newtype that benchmarks at ~1.0× |

## Running

```sh
cargo run --example 01_ownership_and_borrowing   # run one demo
cargo test --examples                            # run the embedded tests (45 of them)
cargo bench                                       # micro-benchmarks (see below)

# The benchmark-bearing demo wants optimizations on:
cargo run --release --example 15_typestate_and_zerocost
```

## Benchmarks

A std-only benchmark harness, [`benches/bench_all.rs`](benches/bench_all.rs), measures
something concrete for every demo (`cargo bench`). Per-demo **bench reports** with
measured numbers, methodology, and interpretation live in
[`bench_intel_mac/`](bench_intel_mac/) (named for the box they ran on; see its
[README](bench_intel_mac/README.md) for the full machine spec).

The comparisons are like-for-like, so the results split cleanly into two groups:

- **Abstraction is free (~1.0×)** — the correctness/type-system features compile away:
  error handling (03), iterators (04), generics (05), macros (13), zero-cost newtypes
  (15). That ~1.0 is the whole point.
- **Real, expected trade-offs** — indirection that can't inline (`dyn` dispatch 06
  ~2.2×, boxed closures 07 ~2.1×), allocation (owned vs borrowed strings 08 ~3.7×,
  clone vs move 01, deep clone vs `Rc::clone` 09), and lock contention (mutex vs
  atomic 11 ~3.3×).

Each file's header comment also lists its exact run command. Verified with
**Rust 1.96** (`cargo run`/`cargo test`).

## Suggested path

- **Basics (01–04)** — ownership, the type system's data modeling, errors, iterators.
  This is the mental-model shift; everything else builds on it.
- **Intermediate (05–08)** — abstraction (traits/generics), dispatch choices,
  closures, and lifetimes. Where Rust starts to feel expressive.
- **Advanced / expert (09–15)** — shared & interior mutability, concurrency and the
  `Send`/`Sync` guarantees, `unsafe` + FFI behind safe APIs, metaprogramming, the
  async model demystified, and type-driven design that costs nothing at runtime.

## The recurring themes

1. **The compiler is the proof checker.** Ownership/borrowing (01, 08), `Send`/`Sync`
   (11), and type-state (15) turn whole classes of bugs — dangling pointers, data
   races, protocol misuse — into compile errors, not runtime hopes.
2. **Make illegal states unrepresentable.** Enums + exhaustive `match` (02), `Result`
   over exceptions (03), and type-state builders (15) push correctness into types.
3. **Zero-cost abstractions.** Generics monomorphize and iterators fuse (04, 05); a
   newtype compiles down to its inner value (15). You don't pay for the abstraction.
4. **Safety is opt-out, not absent.** `unsafe` is a small, auditable escape hatch you
   wrap in a safe API (12) — the same way `std` is built.
5. **No hidden runtime.** No GC, no implicit executor. When you want one — reference
   counting (09), an async scheduler (14) — you add it explicitly and can see its cost.
