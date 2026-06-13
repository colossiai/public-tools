// Tier 1 — Lesson 05: Arrays, tuples, readonly, and `as const`
//
// Arrays = same-typed sequence. Tuples = fixed-length sequence with a type
// per slot. `readonly` and `as const` give you immutability — at compile time.

// ---------- arrays ----------
const nums: number[] = [1, 2, 3];
const names: Array<string> = ["a", "b"]; // equivalent syntax

// ---------- tuples ----------
// Fixed length, position-typed.
const pair: [string, number] = ["age", 36];
const [k, v] = pair; // k: string, v: number

// labeled tuple — purely cosmetic, helps IDE hints
type RGB = [r: number, g: number, b: number];
const red: RGB = [255, 0, 0];

// variadic tuple — rest in the middle
type WithId<T extends unknown[]> = [id: string, ...rest: T];
const userTuple: WithId<[string, number]> = ["u_1", "Ada", 36];

// ---------- readonly ----------
const fixed: readonly number[] = [1, 2, 3];
// fixed.push(4); // ← error: Property 'push' does not exist on readonly number[]

interface Point {
    readonly x: number;
    readonly y: number;
}
const p: Point = { x: 1, y: 2 };
// p.x = 99; // ← error

// ---------- as const ----------
// Without `as const`: TS widens literals → general types.
const looseConfig = { mode: "dev", retries: 3 };
//    type: { mode: string; retries: number }   (lost the literals)

// With `as const`: everything becomes readonly + literal.
const tightConfig = { mode: "dev", retries: 3 } as const;
//    type: { readonly mode: "dev"; readonly retries: 3 }

// This is how you derive a string-literal union from data without retyping it:
const ROLES = ["admin", "editor", "viewer"] as const;
type Role = typeof ROLES[number]; // "admin" | "editor" | "viewer"

function assertRole(r: Role): void {
    console.log("role:", r);
}

function main(): void {
    console.log("nums:", nums, "/ names:", names);
    console.log("pair:", k, v);
    console.log("red:", red, "/ userTuple:", userTuple);
    console.log("fixed:", fixed, "/ point:", p);
    console.log("loose:", looseConfig, "/ tight:", tightConfig);
    assertRole("editor");
}

main();
