// ════════════════════════════════════════════════════════════════════
// 05 · Types are ERASED at runtime — and how you bridge the gap
// ════════════════════════════════════════════════════════════════════
//
// Java has reflection; C++ has RTTI/`typeid`; Go has `reflect` and type
// switches. TS has NONE of that for its own types: interfaces, type aliases,
// unions, and generics are COMPILE-TIME ONLY. They are deleted before the
// JS runs. At runtime you only have JS primitives, objects, arrays, and
// classes.
//
// Consequences:
//   • No `x instanceof MyInterface` — interfaces don't exist at runtime.
//   • No reflecting over a generic `T`.
//   • Serialization/validation can't rely on types — you write the checks.
//
// TS gives you two tools to connect a runtime check back to a static type:
// user-defined type guards (`x is T`) and assertion functions (`asserts`).

interface ApiUser {
    id: number;
    name: string;
    roles: string[];
}

// ---------- what DOES exist at runtime ----------
class Widget {
    constructor(public label: string) {}
}
// Classes are real JS values, so `instanceof` works on them (like Java/C++):
function isWidget(x: unknown): x is Widget {
    return x instanceof Widget;
}

// ---------- user-defined type guard: `x is T` ----------
// The function returns a boolean, but the SIGNATURE teaches the compiler:
// "if this returned true, treat the argument as ApiUser from here on."
// Closest cousin: Go's comma-ok type assertion `v, ok := x.(T)`.
function isApiUser(x: unknown): x is ApiUser {
    return (
        typeof x === "object" &&
        x !== null &&
        "id" in x && typeof (x as any).id === "number" &&
        "name" in x && typeof (x as any).name === "string" &&
        "roles" in x && Array.isArray((x as any).roles)
    );
}

// ---------- assertion function: `asserts x is T` ----------
// Throws on failure; on the return path the compiler NARROWS the argument.
// Like Go's must-style helpers, but the narrowing is understood statically.
function assertApiUser(x: unknown): asserts x is ApiUser {
    if (!isApiUser(x)) throw new Error("not an ApiUser: " + JSON.stringify(x));
}

function parse(json: string): ApiUser {
    const data: unknown = JSON.parse(json); // JSON.parse is `any`/`unknown`-shaped
    assertApiUser(data);
    // After the assert, `data` is ApiUser with zero casts:
    return data;
}

function main(): void {
    const good = '{"id":1,"name":"Ada","roles":["admin"]}';
    const user = parse(good);
    console.log("parsed:", user.name, user.roles);

    console.log("isApiUser(good obj)?", isApiUser(JSON.parse(good)));
    console.log("isApiUser(garbage)?", isApiUser({ id: "nope" }));

    const w: unknown = new Widget("ok");
    if (isWidget(w)) console.log("widget label:", w.label); // narrowed to Widget

    try {
        parse('{"id":"bad"}');
    } catch (e) {
        console.log("rejected bad payload:", (e as Error).message);
    }
}

main();

// TAKEAWAY: the compiler cannot check data crossing a runtime boundary
// (network, JSON, env vars) — you must. Write guards / assertion functions
// (or use a schema library like Zod that generates them). This is why the TS
// ecosystem leans on runtime validators instead of reflection-based mapping.
