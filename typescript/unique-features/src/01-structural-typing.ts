// ════════════════════════════════════════════════════════════════════
// 01 · Structural typing — the biggest mental shift from Java/C++
// ════════════════════════════════════════════════════════════════════
//
// Java/C++: types are NOMINAL. A value fits a type only if its class was
// *declared* to be that type (`class Foo implements Bar`, inheritance).
// Names are the identity.
//
// Go: interfaces are structural — a type satisfies an interface if it has
// the methods, no `implements` needed. TS takes that idea and applies it
// to EVERYTHING: object literals, function types, class instances, fields.
//
// TS rule: type A is assignable to type B if A has (at least) B's shape.
// The names are irrelevant.

interface Point2D {
    x: number;
    y: number;
}

interface Vector2D {
    x: number;
    y: number;
}

// No `implements`, no shared base. Different names. Fully interchangeable,
// because the *shape* matches. In Java these would be incompatible types.
function lengthOf(p: Point2D): number {
    return Math.hypot(p.x, p.y);
}

// ---------- object literals satisfy interfaces implicitly ----------
// You never write `new Point2D(...)`. Any object with the right shape IS a
// Point2D. This is closest to Go's implicit interface satisfaction.
const raw = { x: 3, y: 4 };
const asVector: Vector2D = raw; // fine — shape matches

// ---------- classes are structural too ----------
// A class instance is assignable to ANY type with a compatible shape,
// even a totally unrelated class. Coming from C++/Java this is startling.
class Celsius {
    constructor(public value: number) {}
}
class Fahrenheit {
    constructor(public value: number) {}
}
function printValue(x: { value: number }): void {
    console.log("value =", x.value);
}

// ---------- the "excess property check" wrinkle ----------
// Structural typing is loose, EXCEPT for fresh object literals assigned
// directly: TS flags extra properties as a likely typo. Assign via a
// variable first (as `raw` above) and the check is bypassed.
function move(p: Point2D): Point2D {
    return { x: p.x + 1, y: p.y + 1 };
}

// ---------- "more is fine, less is not" ----------
// A wider object (extra fields) is assignable to a narrower type.
const point3d = { x: 1, y: 2, z: 3 };
const flat: Point2D = point3d; // ok — z is just ignored, x/y satisfy Point2D

function main(): void {
    console.log("lengthOf(Point2D):", lengthOf({ x: 3, y: 4 }));
    console.log("Vector fed to a Point2D fn:", lengthOf(asVector));

    // Two unrelated classes, same shape — both accepted structurally:
    printValue(new Celsius(100));
    printValue(new Fahrenheit(212));

    console.log("moved:", move({ x: 1, y: 1 }));
    console.log("3d narrowed to 2d:", flat);

    // ── would-be compile errors (uncomment to see) ──
    // lengthOf({ x: 1 });                 // missing y
    // move({ x: 1, y: 2, z: 3 });         // excess property on a fresh literal
}

main();

// TAKEAWAY: stop thinking "is it declared as type X". Think "does it have
// X's shape". To FORCE name-based distinctness (UserId ≠ OrderId), you must
// opt back in with branded types — see 04-branded-nominal-types.ts.
