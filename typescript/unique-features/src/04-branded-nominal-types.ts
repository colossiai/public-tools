// ════════════════════════════════════════════════════════════════════
// 04 · Branded (nominal) types — opting BACK IN to name-based safety
// ════════════════════════════════════════════════════════════════════
//
// Because TS is structural (see 01), `type UserId = string` and
// `type OrderId = string` are the SAME type — freely swappable. In Java/C++
// you'd just write `class UserId` and the compiler keeps them apart. In TS
// you have to simulate nominal typing with a "brand".
//
// A brand is a phantom field that exists ONLY in the type system. At runtime
// the value is still a plain string/number — zero overhead, no wrapper
// object. This pattern has no direct equivalent in your three languages; it
// falls out of structural typing.

// The brand adds a marker field that a plain string can never have, making
// the branded type structurally distinct.
declare const brand: unique symbol;
type Brand<T, B extends string> = T & { readonly [brand]: B };

type UserId = Brand<string, "UserId">;
type OrderId = Brand<string, "OrderId">;
type Cents = Brand<number, "Cents">;

// Constructors are the ONLY sanctioned way to mint a branded value: validate,
// then assert the brand. The `as` cast is the trust boundary.
function userId(s: string): UserId {
    if (!s.startsWith("u_")) throw new Error(`bad UserId: ${s}`);
    return s as UserId;
}
function orderId(s: string): OrderId {
    if (!s.startsWith("o_")) throw new Error(`bad OrderId: ${s}`);
    return s as OrderId;
}
function cents(n: number): Cents {
    if (!Number.isInteger(n)) throw new Error(`cents must be integer: ${n}`);
    return n as Cents;
}

function fetchUser(id: UserId): string {
    return `user<${id}>`; // id is still just a string at runtime
}
function refund(amount: Cents): void {
    console.log("refunding", amount, "cents");
}

function main(): void {
    const u = userId("u_42");
    const o = orderId("o_7");

    console.log(fetchUser(u));
    console.log("branded value is a plain string at runtime:", typeof u, u);

    refund(cents(1999));

    // ── would-be compile errors (the whole point) ──
    // fetchUser(o);          // OrderId is not UserId
    // fetchUser("u_42");     // raw string is not UserId — must go through userId()
    // refund(1999);          // raw number is not Cents

    // But branded types still behave like their base at runtime:
    console.log("concat still works:", u + "!" /* : string, brand lost */);
}

main();

// TAKEAWAY: reach for a brand whenever two values share a primitive
// representation but must NOT be interchangeable — IDs, units (Cents vs
// Dollars), validated strings (Email, Url), unsanitized-vs-sanitized input.
// The brand is a compile-time proof carried on a zero-cost value.
