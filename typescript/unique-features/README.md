# TypeScript's Unique Features — for experienced C++ / Java / Go developers

You already know generics, classes, access modifiers, closures, and modules.
This mini-course skips all of that and focuses **only** on what TypeScript does
that your three languages don't — plus the "false friends" that look familiar
but behave differently.

Each lesson is one runnable `.ts` file with a `main()` and inline
`// C++ / Java / Go` contrast comments. Every "would-be compile error" is shown
as a commented-out line — uncomment it to feel the type system push back.

## How to run

```bash
pnpm install                        # one-time
pnpm 01                             # run one lesson (aliases 01..06)
pnpm tsx src/03-type-level-programming.ts
pnpm run all                        # run every lesson in order
pnpm typecheck                      # tsc --noEmit (strict, no output)
```

## The lessons

| # | File | What's unique | Your closest prior instinct (and why it's wrong) |
|---|------|---------------|---------------------------------------------------|
| 01 | `structural-typing` | Types match by **shape**, not name — applied to *everything* (objects, functions, class instances) | Java/C++ classes are nominal; even Go only structurally-types *interfaces*. Two identically-shaped types are fully interchangeable here. |
| 02 | `unions-and-exhaustiveness` | First-class union + literal types, flow-sensitive **narrowing**, `never`-based compile-time **exhaustiveness** | `std::variant`/`std::visit`, Java sealed classes, Go type switch — all clumsier, and Go has no exhaustiveness check. |
| 03 | `type-level-programming` | The type system is a **Turing-complete computation language**: `keyof`, mapped, conditional, `infer`, template-literal types | C++ TMP is the only analog (and `infer` ≈ template arg deduction). Java/Go generics only substitute — they can't inspect or transform a type. |
| 04 | `branded-nominal-types` | Simulate **nominal** typing on a structural system with zero-cost phantom "brands" (`UserId` ≠ `OrderId`, both `string`) | In Java/C++ you'd just declare a class. Here structural typing makes that free, so you opt *back* into name-safety with a brand. |
| 05 | `runtime-type-erasure` | Types are **erased before runtime**; you reconnect runtime checks to static types with guards (`x is T`) and assertions (`asserts x is T`) | No reflection/RTTI/`reflect` for TS types. `x is T` is closest to Go's comma-ok assertion. This is why the ecosystem uses validators (Zod), not reflection. |
| 06 | `false-friends` | `enum` pitfalls (prefer `as const` unions), `readonly` is compile-time-only, **bivariant** method params, `any` vs `unknown` | Every one of these matches a Java/C++/Go instinct that misfires in TS. |

## Suggested order

Read **01 first** (structural typing reframes everything else), then
**02 → 03** (the payoff: unions + type-level programming), then
**04 → 05 → 06** as needed. If you only have an hour, do **01 and 03** — they
are the two ideas that most separate "Java dev writing TS" from "TS expert."

## The one-sentence version of each idea

- **01** Stop asking "is it declared as type X"; ask "does it have X's shape."
- **02** Model "one of N cases" as a discriminated union; let `never` prove you handled them all.
- **03** You can compute types from types — this is the layer Zod/Prisma/tRPC are built on.
- **04** When two values share a representation but must not mix, brand them.
- **05** The compiler can't check data crossing a runtime boundary — you must.
- **06** `as const` over `enum`; `readonly` ≠ freeze; method params are bivariant; default to `unknown`.

## Relationship to `../study/`

`../study/` is a full zero-to-expert curriculum (20 lessons). This directory is
the **fast path** for someone who already programs in a statically-typed
language and just wants the delta. Overlapping topics go deeper there:
lessons 04/11/12/13/14/16/17 of `study/` expand on what's summarized here.
