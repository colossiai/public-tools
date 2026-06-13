# TypeScript Study Plan — Zero to Expert

A pragmatic, runnable curriculum. Each lesson is a single self-contained `.ts` file with a `main()` that demonstrates one concept. No framework noise, no half-finished pseudocode — paste, run, modify.

## How to run

```bash
# one-time
pnpm install

# any lesson
pnpm tsx src/01-types-and-variables.ts

# all lessons in order
pnpm run all
```

## Curriculum

### Tier 1 — Beginner (you have *never* written TypeScript)

Goal: read and write everyday TS comfortably. After this tier you can replace plain JS with safer TS in any project.

| # | Lesson | Concept |
|---|--------|---------|
| 01 | `types-and-variables` | `string` / `number` / `boolean` / `null` / `undefined`, `any` vs `unknown`, type inference |
| 02 | `functions` | parameter types, return types, optional/default/rest params, void vs never |
| 03 | `objects-and-interfaces` | object shapes, `interface` vs `type`, optional/readonly fields, index signatures |
| 04 | `unions-and-narrowing` | union types, literal types, `typeof` / `in` / `instanceof` narrowing |
| 05 | `arrays-tuples-readonly` | `T[]`, tuples, `readonly`, `as const` |

### Tier 2 — Intermediate (you write TS daily)

Goal: build reusable, type-safe APIs.

| # | Lesson | Concept |
|---|--------|---------|
| 06 | `generics` | generic functions, classes, constraints, default type params |
| 07 | `classes` | `public` / `private` / `protected` / `readonly`, `abstract`, parameter properties |
| 08 | `enums-vs-const` | `enum` pitfalls vs `as const` unions — why most teams skip `enum` |
| 09 | `utility-types` | `Partial`, `Required`, `Pick`, `Omit`, `Record`, `ReturnType`, `Awaited` |
| 10 | `modules` | ESM `import`/`export`, type-only imports, re-exports (see `src/lib/`) |

### Tier 3 — Advanced (you design type APIs for other devs)

Goal: bend the type system to model invariants statically.

| # | Lesson | Concept |
|---|--------|---------|
| 11 | `keyof-and-mapped-types` | `keyof`, mapped types, key remapping with `as` |
| 12 | `conditional-types-and-infer` | `T extends U ? X : Y`, `infer`, distributive conditionals |
| 13 | `template-literal-types` | string manipulation at the type level |
| 14 | `type-predicates-and-asserts` | `x is T` user-defined guards, `asserts x is T` |
| 15 | `declaration-merging` | interface merging, module augmentation |

### Tier 4 — Expert (you're the person other engineers ask)

Goal: nominal typing, variance, phantom-state APIs, and the strictness knobs that change everything.

| # | Lesson | Concept |
|---|--------|---------|
| 16 | `branded-nominal-types` | simulate nominal types with brands — UserId ≠ OrderId |
| 17 | `variance-and-function-types` | covariance / contravariance / `strictFunctionTypes` |
| 18 | `builder-pattern-with-phantom-state` | compile-time state machine in a fluent builder |
| 19 | `tsconfig-strictness-flags` | what `strict`, `noUncheckedIndexedAccess`, `exactOptionalPropertyTypes` actually do |
| 20 | `decorators` | TC39 stage-3 decorators (the modern variant) |

## Suggested pacing

- Tier 1: one evening per lesson, ~1 week total.
- Tier 2: one lesson + one small project each (write a generic cache, a CRUD repo, etc.).
- Tier 3: read each lesson, then re-read after a week. These concepts compound.
- Tier 4: each lesson is a doorway to a larger topic — pull on threads that match your work.

## Where to go next

- **Library author?** Read `microsoft/TypeScript` issues tagged `Suggestion: In Discussion`. Study `type-fest` and `ts-toolbelt` source.
- **App developer?** Master `zod` (runtime + type), Drizzle/Prisma's typed query builders, and the strictness flags in Tier 4.
- **Compiler curiosity?** Read the TS handbook's "Narrowing" and "Conditional Types" sections, then skim the TypeScript source `src/compiler/checker.ts`.
