// Tier 3 — Lesson 11: keyof and mapped types
//
// `keyof T` = the union of T's property names as string-literal types.
// Mapped types = "for each key K in some union, produce a new property".
// Together they're how TS transforms one object type into another.

interface User {
    id: number;
    name: string;
    email: string;
}

// ---------- keyof ----------
type UserKey = keyof User; // "id" | "name" | "email"

function read<T, K extends keyof T>(obj: T, key: K): T[K] {
    return obj[key];
}

// ---------- mapped type ----------
// Loop over every key of T and produce a new property.
type ReadonlyAll<T> = {
    readonly [K in keyof T]: T[K];
};

type OptionalAll<T> = {
    [K in keyof T]?: T[K];
};

// ---------- mapped type with a transformation ----------
// Wrap every value in a Promise. Powerful pattern for async repository APIs.
type Promised<T> = {
    [K in keyof T]: Promise<T[K]>;
};
type AsyncUser = Promised<User>;
// { id: Promise<number>; name: Promise<string>; email: Promise<string> }

// ---------- key remapping with `as` (TS 4.1+) ----------
// Build getter signatures: { id } → { getId(): number; getName(): string; ... }
type Getters<T> = {
    [K in keyof T as `get${Capitalize<K & string>}`]: () => T[K];
};
type UserGetters = Getters<User>;
// { getId: () => number; getName: () => string; getEmail: () => string }

// ---------- filter keys via `as never` ----------
// Keep only keys whose values are strings.
type StringKeysOnly<T> = {
    [K in keyof T as T[K] extends string ? K : never]: T[K];
};
type StringFieldsOfUser = StringKeysOnly<User>; // { name: string; email: string }

function main(): void {
    const u: User = { id: 1, name: "Ada", email: "ada@x.com" };
    console.log("read name:", read(u, "name"));

    const frozen: ReadonlyAll<User> = u;
    console.log("frozen:", frozen);

    const patch: OptionalAll<User> = { name: "Eve" };
    console.log("patch:", patch);

    // demonstrate getter type via a runtime impl
    const getters: UserGetters = {
        getId: () => u.id,
        getName: () => u.name,
        getEmail: () => u.email,
    };
    console.log("getter:", getters.getName());

    const s: StringFieldsOfUser = { name: u.name, email: u.email };
    console.log("string-only keys:", s);
}

main();
