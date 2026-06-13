// Tier 1 — Lesson 04: Unions and narrowing
//
// Union types = "one of these". `A | B` means "value is either A or B".
// "Narrowing" = code paths where TS *proves* which side of the union you're on.
// This is the heart of TypeScript's flow analysis.

// ---------- literal unions ----------
type Status = "pending" | "active" | "closed";

function describe(s: Status): string {
    return `status is ${s}`;
}

// ---------- typeof narrowing ----------
function len(value: string | number): number {
    if (typeof value === "string") {
        return value.length; // TS knows: string
    }
    return value.toString().length; // TS knows: number
}

// ---------- in operator narrowing ----------
type Dog = { kind: "dog"; bark: () => string };
type Cat = { kind: "cat"; meow: () => string };

function speak(a: Dog | Cat): string {
    if ("bark" in a) return a.bark();
    return a.meow();
}

// ---------- discriminated unions (tagged unions) ----------
// The single most useful pattern in TS. Add a literal `kind` field;
// switching on it narrows perfectly.
type Result<T> =
    | { kind: "ok"; value: T }
    | { kind: "err"; error: string };

function unwrap<T>(r: Result<T>): T {
    switch (r.kind) {
        case "ok":  return r.value;
        case "err": throw new Error(r.error);
    }
}

// ---------- exhaustiveness check via `never` ----------
// If you add a new variant to Status, the compiler will FAIL here until you
// handle it — `never` is the canary.
function color(s: Status): string {
    switch (s) {
        case "pending": return "yellow";
        case "active":  return "green";
        case "closed":  return "gray";
        default: {
            const _exhaustive: never = s;
            return _exhaustive;
        }
    }
}

function main(): void {
    console.log(describe("active"));
    console.log("len('hi'):", len("hi"), "/ len(12345):", len(12345));

    const dog: Dog = { kind: "dog", bark: () => "woof" };
    const cat: Cat = { kind: "cat", meow: () => "meow" };
    console.log("speak:", speak(dog), "/", speak(cat));

    const ok: Result<number> = { kind: "ok", value: 42 };
    console.log("unwrap:", unwrap(ok));

    console.log("color('active'):", color("active"));
}

main();
