// ════════════════════════════════════════════════════════════════════
// 06 · False friends — features that LOOK familiar but behave differently
// ════════════════════════════════════════════════════════════════════
//
// These map to instincts from Java/C++/Go that are subtly WRONG in TS.
// Learn the difference, not the feature.

// ────────────────────────────────────────────────────────────────────
// (a) `enum` — not the Java/C++ enum you expect. Prefer `as const` unions.
// ────────────────────────────────────────────────────────────────────
// TS `enum` emits a real runtime object and has quirks (numeric enums are
// bidirectional, they're nominal-ish, they bloat output). Most teams instead
// use a `const` object + a union type derived from it: zero runtime surprise,
// pure string literals, and it plays nicely with narrowing (see 02).
const Color = { Red: "red", Green: "green", Blue: "blue" } as const;
type Color = (typeof Color)[keyof typeof Color]; // "red" | "green" | "blue"

function paint(c: Color): string {
    return `painting ${c}`;
}

// ────────────────────────────────────────────────────────────────────
// (b) `readonly` is COMPILE-TIME ONLY — not C++ `const`, not immutability.
// ────────────────────────────────────────────────────────────────────
// It stops writes THROUGH a readonly-typed reference. It does not freeze the
// object; a mutable alias to the same object can still change it.
interface Config {
    readonly retries: number;
}

function mutateViaAlias(): void {
    const mutable = { retries: 3 };
    const view: Config = mutable; // same object, readonly view
    // view.retries = 5;          // ← compile error through the readonly view
    mutable.retries = 5;          // ...but the underlying object is not frozen
    console.log("readonly is a view, not a lock:", view.retries); // 5
}

// `as const` gives you deep readonly literal narrowing — the closest to a
// real compile-time constant, but STILL not runtime-frozen (use Object.freeze
// for that).
const SETTINGS = { region: "us", limit: 10 } as const;
type Region = (typeof SETTINGS)["region"]; // "us" (a literal, not string)

// ────────────────────────────────────────────────────────────────────
// (c) Method parameters are BIVARIANT — a deliberate soundness hole.
// ────────────────────────────────────────────────────────────────────
// Java wildcards / C++ overloading make you reason about variance carefully.
// TS is careful for *function-typed properties* under `strictFunctionTypes`
// (contravariant params), BUT parameters declared with METHOD syntax stay
// bivariant for ergonomic reasons — a documented unsafe spot.
interface Animal { name: string; }
interface Dog extends Animal { bark(): void; }

interface HandlerMethod {
    handle(a: Animal): void;  // method syntax → bivariant params (looser)
}
interface HandlerFn {
    handle: (a: Animal) => void; // property syntax → contravariant (stricter)
}

// A Dog-handler is accepted where an Animal-handler is expected via the
// METHOD form, even though that's technically unsafe:
const dogHandlerMethod: HandlerMethod = { handle: (d: Dog) => console.log("bark check") };
// The property form would REJECT the same assignment under strictFunctionTypes.

// ────────────────────────────────────────────────────────────────────
// (d) `any` disables the checker; `unknown` is the safe top type.
// ────────────────────────────────────────────────────────────────────
// Instinct from dynamic code is to reach for `any`. `any` is contagious and
// silently turns off type checking. Use `unknown` — you must narrow before
// use, so safety is preserved (see 05 for narrowing).
function lengthSafe(x: unknown): number {
    if (typeof x === "string" || Array.isArray(x)) return x.length; // must narrow
    return 0;
}

function main(): void {
    console.log(paint(Color.Green));
    // paint("purple"); // ← compile error: not a Color

    mutateViaAlias();
    console.log("region literal:", SETTINGS.region);

    dogHandlerMethod.handle({ name: "generic" }); // compiles due to bivariance
    console.log("bivariant method assignment compiled (unsafe but allowed)");

    console.log("lengthSafe('abc'):", lengthSafe("abc"));
    console.log("lengthSafe(42):", lengthSafe(42));
}

main();

// TAKEAWAY: reach for `as const` unions over `enum`; treat `readonly` as a
// compile-time write-guard (not a freeze); know that method-syntax params are
// bivariant; and default to `unknown` over `any` at every boundary.
