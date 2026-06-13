// Tier 3 — Lesson 13: Template literal types
//
// Template literals exist at the *type* level too. You can compose, split,
// and pattern-match strings purely in types. This unlocks type-safe routing,
// CSS-property typing, event-name plumbing, and more.

// ---------- compose string literals ----------
type Greeting = `Hello, ${string}`;
const g1: Greeting = "Hello, Ada";
// const g2: Greeting = "Hi, Ada"; // ← compile error

// ---------- combine literal unions ----------
type Method = "GET" | "POST" | "DELETE";
type Resource = "users" | "posts";
type Endpoint = `${Method} /${Resource}`;
// "GET /users" | "GET /posts" | "POST /users" | ... 6 combinations

const ep: Endpoint = "GET /users";

// ---------- intrinsic string manipulation types ----------
type U = Uppercase<"hello">;      // "HELLO"
type L = Lowercase<"HELLO">;      // "hello"
type C = Capitalize<"hello">;     // "Hello"
type N = Uncapitalize<"Hello">;   // "hello"

// ---------- parse a path into params: a tiny Express-style router type ----------
type ExtractParams<Path extends string> =
    Path extends `${string}:${infer Param}/${infer Rest}`
        ? Param | ExtractParams<`/${Rest}`>
        : Path extends `${string}:${infer Param}`
            ? Param
            : never;

type P1 = ExtractParams<"/users/:userId/posts/:postId">;
// "userId" | "postId"

function handleRoute<Path extends string>(
    path: Path,
    handler: (params: Record<ExtractParams<Path>, string>) => void,
): void {
    // (purely for demo — split path & call handler with sample values)
    const params = {} as Record<ExtractParams<Path>, string>;
    for (const segment of path.split("/")) {
        if (segment.startsWith(":")) {
            (params as Record<string, string>)[segment.slice(1)] = "sample";
        }
    }
    handler(params);
}

// ---------- typed event-emitter keys ----------
type EventName<T extends string> = `on${Capitalize<T>}`;
type ClickEvent = EventName<"click">; // "onClick"

function main(): void {
    console.log("greeting:", g1);
    console.log("endpoint:", ep);

    const u: U = "HELLO";
    const l: L = "hello";
    const c: C = "Hello";
    const n: N = "hello";
    console.log("string manip:", u, l, c, n);

    handleRoute("/users/:userId/posts/:postId", (params) => {
        // params is typed { userId: string; postId: string }
        console.log("router got:", params);
    });
}

main();
