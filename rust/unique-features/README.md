# Rust's Unique Features — for experienced C++ / Java / Go developers

You already know pointers, RAII, generics, interfaces, and threads. This
mini-course skips the shared basics and focuses **only** on what Rust does that
your three languages don't — plus the "false friends" that look familiar but
behave differently.

Each lesson is one runnable file under `examples/` with a `main()` and inline
`// C++ / Java / Go` contrast comments. Every "would-be compile error" is shown
as a commented-out line — uncomment it to feel the compiler push back (that
pushback *is* the feature).

## How to run

```bash
cargo run --example 01_ownership_and_borrowing   # one lesson
cargo build --examples                           # type-check/compile all six
```

## The lessons

| # | File | What's unique | Your closest prior instinct (and why it's wrong) |
|---|------|---------------|---------------------------------------------------|
| 01 | `ownership_and_borrowing` | Single **owner** + the borrow checker's *shared XOR mutable* rule → memory safety & data-race freedom, no GC, zero runtime cost | C++ RAII/move is closest, but a moved-from value stays *usable* (use-after-move compiles). Java/Go lean on a GC and let you alias-mutate freely. |
| 02 | `lifetimes` | Compile-time **lifetime** labels prove no reference outlives its data — pure static proof, zero codegen | C++ happily returns a reference to a local (UB at runtime). Java/Go rely on the GC, so you can't even express a temporary borrow. |
| 03 | `enums_and_pattern_matching` | True **sum types** + exhaustive `match`; **no null** (`Option`), **no exceptions** (`Result` + `?`) | `std::variant`/sealed-classes/`interface{}` are clumsier and non-exhaustive; null and exceptions are the norm you're leaving behind. |
| 04 | `traits_and_dispatch` | Implement a trait for a **foreign type**, **blanket impls**, coherence/orphan rule, and **you pick** static (monomorphized, zero-cost) vs `dyn` (vtable) dispatch | Java interfaces are nominal (declared at the class). Go interfaces have no coherence/generic-bound story. C++ templates lack the orphan rule and the diagnostics. |
| 05 | `fearless_concurrency` | `Send`/`Sync` marker traits extend ownership across threads → a **data race is a compile error** | Go races need `-race` at runtime to *maybe* catch; C++ is UB; Java compiles a forgotten `synchronized` fine. |
| 06 | `false_friends` | Destructive move, no inheritance, checked integer overflow, expression-oriented syntax, shadowing, deterministic `Drop` | Each matches a C++/Java/Go instinct that misfires in Rust. |

## Suggested order

**01 first** — ownership is the foundation everything else rests on. Then
**02 → 03 → 04** (lifetimes, then the two ideas you'll use hourly: sum
types and traits), then **05 → 06**. If you have only an hour, do **01 and 03**:
ownership and "no-null/no-exceptions" are what most change how you write code.

## The one-sentence version of each idea

- **01** Every value has one owner; borrows are *shared XOR mutable* — the compiler proves it, so there's no GC and no aliasing bugs.
- **02** A reference can never outlive what it points to, and the proof costs nothing at runtime.
- **03** Model "one of N cases" as an enum; `Option`/`Result` put "missing" and "failed" in the type, not in a null or a throw.
- **04** Traits are structural power + coherence: extend foreign types, and choose zero-cost or dynamic dispatch per call site.
- **05** If a type isn't thread-safe, you can't send or share it — data races don't compile.
- **06** `move` kills the source; no inheritance; overflow panics in debug; `if`/`match` are expressions; `Drop` is deterministic RAII.

## Relationship to `../zero_to_expert/`

`../zero_to_expert/` is the full 15-lesson curriculum with benchmarks and
embedded tests. This directory is the **fast path** for someone who already
programs in a statically-typed systems/JVM language and just wants the delta.
Overlapping topics go deeper there — see its lessons 01 (ownership), 05–06
(traits/dispatch), 08 (lifetimes), 10–11 (concurrency, `Send`/`Sync`), and 15
(typestate & zero-cost abstractions).
