// Tier 1 — Lesson 01: Types and variables
//
// Goal: know what TS actually *adds* on top of JS values.
//
// Mental model: types describe the *set of possible values* a variable can hold.
// `number` is "any number". `42` (a literal type) is "only the number 42".
// `unknown` is "any value, but you must narrow before using it".
// `any` is "stop type-checking me" — avoid.

// ---------- primitives ----------
const userName: string = "Ada";
const age: number = 36;
const isAdmin: boolean = true;
const nothing: null = null;
const notSet: undefined = undefined;

// ---------- inference (almost always prefer this) ----------
// TS infers `string` here — adding `: string` is redundant noise.
const inferred = "TypeScript infers me";

// `let` widens literal → general type; `const` keeps the literal.
let mutable = "hello";   // type: string
const literal = "hello"; // type: "hello"

// ---------- any vs unknown ----------
// `any` is an escape hatch that disables checking. Code below compiles but crashes:
const dangerous: any = "not a number";
// dangerous.toFixed(2);  // ← would crash at runtime, TS allows it

// `unknown` forces you to narrow before use. This is the safe escape hatch.
const safer: unknown = JSON.parse('{"x": 1}');
if (typeof safer === "object" && safer !== null && "x" in safer) {
    // TS now knows `safer` has an `x` property
    console.log("narrowed unknown:", safer.x);
}

// ---------- void & never ----------
// `void` = the function returns nothing meaningful.
function logIt(msg: string): void {
    console.log(msg);
}

// `never` = the function never returns (throws or loops forever).
// Used by TS for exhaustiveness checks (see lesson 04).
function fail(reason: string): never {
    throw new Error(reason);
}

function main(): void {
    logIt(`user=${userName} age=${age} admin=${isAdmin}`);
    logIt(`inferred type stays inferred: ${inferred}, mutable=${mutable}, literal=${literal}`);
    console.log("null/undefined:", nothing, notSet);
    console.log("dangerous any:", dangerous);
    try { fail("demonstrating never"); } catch (e) { console.log("caught:", (e as Error).message); }
}

main();
