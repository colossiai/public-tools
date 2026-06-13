// Tier 3 — Lesson 14: User-defined type guards & assertion functions
//
// Sometimes `typeof` / `instanceof` / `in` aren't enough — you need to teach
// the compiler that a *custom* check narrows a type. Two tools:
//
//   1. `function isX(v): v is X`        → returns boolean, narrows on true.
//   2. `function assertX(v): asserts v is X` → throws if not, narrows after call.

// ---------- type predicate: `v is X` ----------
interface Cat { kind: "cat"; meow(): void }
interface Dog { kind: "dog"; bark(): void }

function isCat(animal: Cat | Dog): animal is Cat {
    return animal.kind === "cat";
}

function handle(a: Cat | Dog): void {
    if (isCat(a)) {
        a.meow(); // narrowed to Cat
    } else {
        a.bark(); // narrowed to Dog
    }
}

// ---------- common gotcha: predicates can lie ----------
// TS trusts you. If your predicate is wrong, narrowing is wrong.
function isString_bad(v: unknown): v is string {
    return true; // never check anything — compiles fine, lies at runtime
}

// ---------- assertion function: `asserts v is X` ----------
// Throws if the check fails. After the call, the variable is narrowed
// for the *rest of the scope* (no `if` needed).
function assertString(v: unknown): asserts v is string {
    if (typeof v !== "string") throw new Error(`expected string, got ${typeof v}`);
}

function shout(v: unknown): string {
    assertString(v);
    return v.toUpperCase(); // v is string from here on
}

// ---------- assertion functions that check a condition ----------
function assert(condition: unknown, msg = "assertion failed"): asserts condition {
    if (!condition) throw new Error(msg);
}

function divide(a: number, b: number): number {
    assert(b !== 0, "divide by zero");
    return a / b;
}

// ---------- combining: validate-then-narrow ----------
interface ApiUser { id: number; name: string }

function isApiUser(v: unknown): v is ApiUser {
    return (
        typeof v === "object" && v !== null &&
        "id" in v && typeof (v as Record<string, unknown>).id === "number" &&
        "name" in v && typeof (v as Record<string, unknown>).name === "string"
    );
}

function main(): void {
    handle({ kind: "cat", meow: () => console.log("meow") });
    handle({ kind: "dog", bark: () => console.log("woof") });

    console.log("shout:", shout("hello"));
    console.log("divide:", divide(10, 2));

    const payload: unknown = JSON.parse('{"id": 1, "name": "Ada"}');
    if (isApiUser(payload)) {
        console.log("validated user:", payload.name);
    }

    // demonstrate the "predicates can lie" hazard, but don't *use* the lie
    console.log("isString_bad lies:", isString_bad(42));
}

main();
