// Tier 1 — Lesson 02: Functions
//
// Functions are the most important place to put types. A well-typed function
// signature is documentation that the compiler verifies.

// ---------- basic typed function ----------
function add(a: number, b: number): number {
    return a + b;
}

// ---------- optional & default params ----------
// Optional (`?`) means "may be undefined". Default values imply the type.
function greet(name: string, title?: string): string {
    return title ? `${title} ${name}` : `Hello, ${name}`;
}

function withDefault(name: string, exclaim = false): string {
    return `Hi ${name}${exclaim ? "!" : ""}`;
}

// ---------- rest params ----------
function sum(...nums: number[]): number {
    return nums.reduce((acc, n) => acc + n, 0);
}

// ---------- function-type aliases ----------
// Type-alias the *shape* of a function, then reuse it.
type BinaryOp = (a: number, b: number) => number;

const multiply: BinaryOp = (a, b) => a * b; // params/return inferred from BinaryOp

// ---------- overloads ----------
// Multiple call signatures + one implementation. Useful when the return type
// depends on the argument shape.
function pick(value: string): string[];
function pick(value: number): number;
function pick(value: string | number): string[] | number {
    return typeof value === "string" ? value.split("") : value * 2;
}

// ---------- void return ----------
// A `void` return type means "callers should not rely on a value".
// Note the subtle rule: a function typed as `() => void` can be *implemented*
// by a function that returns something — TS just hides that value from callers.
const callbacks: Array<() => void> = [];
callbacks.push(() => 42); // legal — the `42` is discarded by the contract

function main(): void {
    console.log("add(2,3):", add(2, 3));
    console.log("greet:", greet("Ada"), "/", greet("Ada", "Dr."));
    console.log("default:", withDefault("Ada"), "/", withDefault("Ada", true));
    console.log("sum:", sum(1, 2, 3, 4, 5));
    console.log("multiply:", multiply(6, 7));
    console.log("pick(string):", pick("hi"));
    console.log("pick(number):", pick(21));
}

main();
