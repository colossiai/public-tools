// ════════════════════════════════════════════════════════════════════
// 03 · Types as a computation language (the crown jewel)
// ════════════════════════════════════════════════════════════════════
//
// This is what makes TS unique among mainstream languages. The type system
// is itself a (Turing-complete) functional language: you compute types FROM
// other types.
//
// C++: template metaprogramming is the only real analog. `infer` is like
//      template argument deduction; mapped types are like variadic template
//      transformations — but here it's ergonomic and designed for it.
// Java/Go: nothing remotely like this. Generics only substitute; they cannot
//      inspect, transform, or pattern-match a type.
//
// Five primitives, composed below: keyof · indexed access · mapped types ·
// conditional types + infer · template literal types.

// ---------- keyof + indexed access ----------
interface User {
    id: number;
    name: string;
    admin: boolean;
}
type UserKey = keyof User;        // "id" | "name" | "admin"
type NameType = User["name"];     // string

// A fully generic, type-safe property getter:
function get<T, K extends keyof T>(obj: T, key: K): T[K] {
    return obj[key]; // return type is exactly the field's type, per key
}

// ---------- mapped types: transform every field ----------
// Rebuild a type by iterating its keys. `+?`/`-?`, `readonly`, and key
// remapping via `as` are all available.
type MyPartial<T> = { [K in keyof T]?: T[K] };
type MyReadonly<T> = { readonly [K in keyof T]: T[K] };

// Recursive mapped type — deep immutability (no built-in in C++/Java):
type DeepReadonly<T> = T extends (infer E)[]
    ? ReadonlyArray<DeepReadonly<E>>
    : T extends object
    ? { readonly [K in keyof T]: DeepReadonly<T[K]> }
    : T;

// ---------- conditional types + infer: pattern-match a type ----------
// `infer` binds a piece of a matched type to a name, like destructuring.
type ElementOf<T> = T extends (infer E)[] ? E : never;
type Unwrap<T> = T extends Promise<infer R> ? R : T;
type MyReturnType<F> = F extends (...args: any[]) => infer R ? R : never;

type A = ElementOf<string[]>;                 // string
type B = Unwrap<Promise<number>>;             // number
type C = MyReturnType<() => User>;            // User

// ---------- template literal types: string algebra at the type level ----------
// Build/parse strings in the type system. This is genuinely unique to TS.
type Getters<T> = {
    [K in keyof T as `get${Capitalize<string & K>}`]: () => T[K];
};
type UserGetters = Getters<User>;
// => { getId: () => number; getName: () => string; getAdmin: () => boolean }

type Route = `/${string}`;                    // any string starting with "/"
type HttpEvent = `on:${"GET" | "POST"}`;      // "on:GET" | "on:POST"

// A tiny type-level parser: split "a.b.c" into a tuple of segments.
type Split<S extends string, D extends string> =
    S extends `${infer Head}${D}${infer Tail}` ? [Head, ...Split<Tail, D>] : [S];
type Parts = Split<"user.address.city", ".">; // ["user", "address", "city"]

function main(): void {
    const u: User = { id: 1, name: "Ada", admin: true };

    // `get` proves the compile-time machinery pays off at runtime ergonomics:
    const name: string = get(u, "name");
    const admin: boolean = get(u, "admin");
    console.log("get name/admin:", name, admin);
    // get(u, "nope"); // ← compile error: "nope" is not keyof User

    const frozen: DeepReadonly<{ a: { b: number[] } }> = { a: { b: [1, 2] } };
    // frozen.a.b.push(3); // ← compile error: readonly all the way down
    console.log("deep readonly value:", frozen);

    // Types A/B/C, UserGetters, Route, Parts are compile-time only — they
    // vanish at runtime. Log something so the file DOES something:
    const _typeChecks: [A, B, C] = ["s", 42, u];
    console.log("type-level results exist only at compile time:", _typeChecks.length);
}

main();

// TAKEAWAY: this is the layer libraries like Zod, Prisma, and tRPC are built
// on. Fluency here — mapped + conditional + template literal types, composed
// recursively — is what "TS expert" actually means.
