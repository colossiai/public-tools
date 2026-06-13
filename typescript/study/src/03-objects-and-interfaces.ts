// Tier 1 — Lesson 03: Objects and interfaces
//
// `interface` and `type` are 95% interchangeable for object shapes.
// Rule of thumb: use `interface` for public, extensible shapes; use `type`
// for unions, intersections, mapped types, and anything non-object.

// ---------- inline object type ----------
function distance(p: { x: number; y: number }): number {
    return Math.sqrt(p.x * p.x + p.y * p.y);
}

// ---------- interface ----------
interface User {
    id: number;
    name: string;
    email?: string;        // optional
    readonly createdAt: Date; // can't be reassigned after construction
}

// interfaces can extend other interfaces
interface AdminUser extends User {
    role: "admin" | "super-admin";
}

// ---------- type alias for the same shape ----------
type UserT = {
    id: number;
    name: string;
};

// ---------- intersection: combine shapes ----------
type Timestamped = { createdAt: Date; updatedAt: Date };
type Post = { title: string; body: string } & Timestamped;

// ---------- index signatures: "any key of type K maps to V" ----------
interface StringDict {
    [key: string]: string;
}

// ---------- excess property check ----------
// Object literals get extra checking — typos in field names are caught.
const u: User = {
    id: 1,
    name: "Ada",
    createdAt: new Date(),
    // emaill: "x@y.z", // ← would error: "Object literal may only specify known properties"
};

function main(): void {
    console.log("distance:", distance({ x: 3, y: 4 }));

    const admin: AdminUser = {
        id: 2,
        name: "Root",
        role: "super-admin",
        createdAt: new Date(),
    };
    console.log("admin:", admin.name, admin.role);

    const post: Post = {
        title: "Hi",
        body: "...",
        createdAt: new Date(),
        updatedAt: new Date(),
    };
    console.log("post:", post.title);

    const headers: StringDict = { "x-trace": "abc", "content-type": "json" };
    console.log("headers:", headers);

    console.log("user:", u.name, u.email ?? "(no email)");
}

main();
