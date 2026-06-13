// Tier 4 — Lesson 19: The strictness flags that actually matter
//
// `strict: true` is the umbrella for several individual flags:
//   - noImplicitAny
//   - strictNullChecks         ← the most important by far
//   - strictFunctionTypes
//   - strictBindCallApply
//   - strictPropertyInitialization
//   - noImplicitThis
//   - alwaysStrict
//   - useUnknownInCatchVariables
//
// Beyond `strict`, two extra flags drastically improve real-world safety:
//   - noUncheckedIndexedAccess
//   - exactOptionalPropertyTypes
//
// Our tsconfig.json has all three on. This lesson shows what each does.

// ---------- strictNullChecks ----------
// Without it: `null` and `undefined` are members of every type.
// With it: you must handle them explicitly.
function pickFirst<T>(arr: T[]): T | undefined {
    return arr[0]; // even without the next flag, this would be T under strictNullChecks alone
}

// ---------- noUncheckedIndexedAccess ----------
// Forces `T | undefined` when you index into arrays or records, because
// the index might be out of bounds. Without it: TS lies about safety.
const words = ["alpha", "beta", "gamma"];
const w = words[10]; // type: string | undefined (would be string without the flag)

function shoutFirst(arr: string[]): string {
    const first = arr[0];
    // first is `string | undefined` here, so we MUST handle the empty case:
    if (first === undefined) return "";
    return first.toUpperCase();
}

// ---------- exactOptionalPropertyTypes ----------
// `field?: T` normally means `T | undefined`. With this flag, `undefined`
// is NOT assignable unless the property type explicitly includes it.
interface Opts {
    title?: string;          // means: may be missing, but if present is string
}

const a: Opts = {};               // ✓ missing entirely
const b: Opts = { title: "hi" };  // ✓ present and string
// const c: Opts = { title: undefined }; // ✗ error with exactOptionalPropertyTypes
//   → with the flag on, you must distinguish "absent" from "present-but-undefined".

// ---------- useUnknownInCatchVariables (on under strict) ----------
// Catch variables are `unknown` instead of `any` — forces a narrow before use.
function tryParse(s: string): unknown {
    try { return JSON.parse(s); }
    catch (e) {
        if (e instanceof Error) return `error: ${e.message}`;
        return "error: unknown";
    }
}

// ---------- strictPropertyInitialization ----------
// Class fields without initializers must be initialized in the constructor,
// or marked with `!` to opt out, or have a `?` type.
class Box {
    label: string;            // must be assigned in constructor
    seen?: boolean;           // optional — undefined is fine
    deferred!: number;        // "trust me" — initialized later
    constructor(label: string) { this.label = label; }
}

function main(): void {
    console.log("first:", pickFirst([1, 2, 3]));
    console.log("oob index:", w); // undefined at runtime
    console.log("shoutFirst:", shoutFirst(["hello", "world"]));
    console.log("opts:", a, b);
    console.log("tryParse:", tryParse("{not json"));
    const box = new Box("hi");
    box.deferred = 42;
    console.log("box:", box);
}

main();
