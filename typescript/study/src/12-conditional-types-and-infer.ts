// Tier 3 — Lesson 12: Conditional types and `infer`
//
// `T extends U ? X : Y` lets a type *branch* based on whether T is assignable
// to U. `infer V` inside the `extends` clause grabs a piece of T into a
// new type variable. Combined, this is how most utility types are written.

// ---------- basic conditional ----------
type IsString<T> = T extends string ? "yes" : "no";
type A = IsString<"hello">; // "yes"
type B = IsString<42>;      // "no"

// ---------- distributive over unions ----------
// A naked type parameter in a conditional distributes over unions:
// ToArray<string | number>  →  ToArray<string> | ToArray<number>  →  string[] | number[]
type ToArray<T> = T extends unknown ? T[] : never;
type C = ToArray<string | number>; // string[] | number[]

// To OPT OUT of distribution, wrap with brackets:
type ToArrayNonDist<T> = [T] extends [unknown] ? T[] : never;
type D = ToArrayNonDist<string | number>; // (string | number)[]

// ---------- infer: extract a type from inside another ----------
type ReturnT<F> = F extends (...args: any[]) => infer R ? R : never;
type R1 = ReturnT<() => string>;       // string
type R2 = ReturnT<(n: number) => number[]>; // number[]

// extract element type from an array
type ElementOf<A> = A extends Array<infer E> ? E : never;
type E1 = ElementOf<number[]>; // number

// unwrap a Promise (the recursive trick TS uses for Awaited)
type Unwrap<T> = T extends Promise<infer U> ? Unwrap<U> : T;
type U1 = Unwrap<Promise<Promise<string>>>; // string

// ---------- a practical conditional type ----------
// Pull out the parameter types of one specific method on an object.
type MethodArgs<T, K extends keyof T> =
    T[K] extends (...args: infer Args) => unknown ? Args : never;

interface API {
    fetch(id: number, opts: { force: boolean }): Promise<unknown>;
    save(payload: object): Promise<void>;
}
type FetchArgs = MethodArgs<API, "fetch">; // [number, { force: boolean }]

function main(): void {
    // Conditional types are purely compile-time — there's nothing to print
    // for the types themselves. We just verify the runtime shape.
    const args: FetchArgs = [42, { force: true }];
    console.log("FetchArgs at runtime:", args);

    // Demonstrate the distributive vs non-distributive split with a value:
    const arr: C = ["a", "b"]; // string[] is a valid member of (string[] | number[])
    const mixed: D = ["a", 1]; // requires the non-distributive (string|number)[]
    console.log("dist sample:", arr, "/ non-dist sample:", mixed);
}

main();
