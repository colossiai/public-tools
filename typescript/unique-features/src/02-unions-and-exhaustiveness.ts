// ════════════════════════════════════════════════════════════════════
// 02 · Union types, literal types, flow narrowing, exhaustiveness
// ════════════════════════════════════════════════════════════════════
//
// C++:   std::variant<A,B,C> + std::visit — verbose, no flow narrowing.
// Java:  sealed interfaces + pattern-matching switch (new, still clunkier).
// Go:    interface{} + type switch — no compile-time exhaustiveness.
//
// TS unions are a first-class, everyday tool. The compiler NARROWS the type
// as it flows through if/switch, and a `never` check gives you compile-time
// exhaustiveness for free — add a variant, get a compile error at every
// switch that forgot it.

// ---------- literal types: a value IS a type ----------
type Direction = "N" | "S" | "E" | "W"; // four specific strings, nothing else
type Bit = 0 | 1;

function step(d: Direction): [number, number] {
    // Inside each branch, `d` is narrowed to that single literal.
    switch (d) {
        case "N": return [0, 1];
        case "S": return [0, -1];
        case "E": return [1, 0];
        case "W": return [-1, 0];
    }
}

// ---------- discriminated unions: the workhorse ----------
// A shared literal field (`kind`) lets the compiler pick the right member.
type Shape =
    | { kind: "circle"; radius: number }
    | { kind: "rect"; w: number; h: number }
    | { kind: "triangle"; base: number; height: number };

function area(s: Shape): number {
    switch (s.kind) {
        case "circle":
            return Math.PI * s.radius ** 2; // s is the circle member here
        case "rect":
            return s.w * s.h;
        case "triangle":
            return 0.5 * s.base * s.height;
        default:
            // EXHAUSTIVENESS: if all cases are handled, `s` is `never` here.
            // Add a 4th Shape variant and forget a case → this line fails to
            // compile ("Type '{...}' is not assignable to 'never'").
            return assertNever(s);
    }
}

function assertNever(x: never): never {
    throw new Error(`unhandled variant: ${JSON.stringify(x)}`);
}

// ---------- narrowing operators ----------
// typeof (primitives), in (property presence), instanceof (classes),
// truthiness, and equality all narrow the static type.
function describe(x: string | number | null): string {
    if (x === null) return "null";
    if (typeof x === "string") return `string(len ${x.length})`; // x: string
    return `number(${x.toFixed(2)})`; // x: number
}

type Cat = { meow: () => string };
type Dog = { bark: () => string };
function speak(pet: Cat | Dog): string {
    return "meow" in pet ? pet.meow() : pet.bark(); // `in` narrows the union
}

function main(): void {
    console.log("step N:", step("N"));
    const shapes: Shape[] = [
        { kind: "circle", radius: 2 },
        { kind: "rect", w: 3, h: 4 },
        { kind: "triangle", base: 6, height: 2 },
    ];
    for (const s of shapes) console.log(s.kind, "area =", area(s).toFixed(2));

    console.log(describe("hello"), describe(3.14159), describe(null));
    console.log(speak({ meow: () => "purr" }));
}

main();

// TAKEAWAY: model "one of N shapes" as a discriminated union, not a class
// hierarchy. The `assertNever` default turns "did I handle every case?" from
// a code-review worry into a compile error.
