// Tier 2 — Lesson 06: Generics
//
// Generics let a function/class/type take *types* as parameters. This is what
// makes TS APIs reusable AND precise — no `any`, no overloads explosion.

// ---------- generic function ----------
// `T` is a type variable. The caller supplies T (or TS infers it).
function identity<T>(value: T): T {
    return value;
}
const s = identity("hello"); // T inferred as "hello" (literal)
const n = identity<number>(42); // T explicitly number

// ---------- multiple type params ----------
function pair<A, B>(a: A, b: B): [A, B] {
    return [a, b];
}

// ---------- generic constraint ----------
// `T extends { length: number }` means "T must have a `length` property".
function longest<T extends { length: number }>(a: T, b: T): T {
    return a.length >= b.length ? a : b;
}

// ---------- generic class ----------
class Box<T> {
    constructor(private value: T) {}
    get(): T { return this.value; }
    map<U>(fn: (v: T) => U): Box<U> {
        return new Box(fn(this.value));
    }
}

// ---------- default type parameter ----------
interface Repository<T, ID = string> {
    find(id: ID): T | undefined;
}

// ---------- keyof + generic constraint: type-safe property access ----------
function prop<T, K extends keyof T>(obj: T, key: K): T[K] {
    return obj[key];
}

function main(): void {
    console.log("identity:", s, n);
    console.log("pair:", pair("age", 36));
    console.log("longest:", longest("hi!", "hello"));

    const b = new Box(10).map((x) => x * 2).map((x) => `value=${x}`);
    console.log("Box pipeline:", b.get());

    const user = { id: 1, name: "Ada" };
    console.log("prop:", prop(user, "name")); // typed as string
    // prop(user, "missing"); // ← compile error: not a key of user
}

main();
