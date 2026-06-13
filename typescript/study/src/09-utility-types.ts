// Tier 2 — Lesson 09: Built-in utility types
//
// These are the bread and butter of day-to-day TS. They transform one type
// into another — make all fields optional, pick a subset, infer a return type,
// unwrap a promise, etc. Internalize these; you will use them daily.

interface User {
    id: number;
    name: string;
    email: string;
    age: number;
}

// ---------- Partial<T>: every field optional ----------
type UserUpdate = Partial<User>;
// { id?: number; name?: string; email?: string; age?: number }

function updateUser(id: number, patch: Partial<User>): void {
    console.log("patching", id, patch);
}

// ---------- Required<T>: every field required (inverse of Partial) ----------
interface Config { host?: string; port?: number }
type FullConfig = Required<Config>;
// { host: string; port: number }

// ---------- Pick<T, K>: keep only these keys ----------
type UserPublic = Pick<User, "id" | "name">;

// ---------- Omit<T, K>: drop these keys ----------
type UserPrivate = Omit<User, "email">;

// ---------- Record<K, V>: object with K-typed keys, V-typed values ----------
type RoleMatrix = Record<"admin" | "editor" | "viewer", string[]>;
const perms: RoleMatrix = {
    admin: ["*"],
    editor: ["read", "write"],
    viewer: ["read"],
};

// ---------- Readonly<T>: every field readonly ----------
type FrozenUser = Readonly<User>;

// ---------- ReturnType<F>, Parameters<F>: extract function pieces ----------
function makeUser(id: number, name: string): User {
    return { id, name, email: `${name}@x.com`, age: 0 };
}
type MakeUserReturn = ReturnType<typeof makeUser>;   // User
type MakeUserArgs = Parameters<typeof makeUser>;     // [number, string]

// ---------- Awaited<P>: unwrap promise(s) ----------
async function fetchUser(): Promise<User> {
    return makeUser(1, "Ada");
}
type FetchedUser = Awaited<ReturnType<typeof fetchUser>>; // User (Promise unwrapped)

// ---------- NonNullable<T>: drop null/undefined ----------
type Maybe = string | null | undefined;
type Definitely = NonNullable<Maybe>; // string

async function main(): Promise<void> {
    updateUser(1, { name: "Ada", age: 36 });

    const cfg: FullConfig = { host: "localhost", port: 5432 };
    console.log("cfg:", cfg);

    const pub: UserPublic = { id: 1, name: "Ada" };
    const priv: UserPrivate = { id: 1, name: "Ada", age: 36 };
    console.log("pick/omit:", pub, priv);

    console.log("perms:", perms);

    const frozen: FrozenUser = makeUser(2, "Eve");
    // frozen.name = "X"; // ← error
    console.log("frozen:", frozen);

    const args: MakeUserArgs = [3, "Grace"];
    const r: MakeUserReturn = makeUser(...args);
    console.log("ReturnType:", r);

    const fetched: FetchedUser = await fetchUser();
    console.log("Awaited:", fetched);

    const cleaned: Definitely = "I am never null";
    console.log("NonNullable:", cleaned);
}

main();
