// Tier 4 — Lesson 16: Branded (nominal) types
//
// TypeScript is *structurally* typed: two types with the same shape are
// interchangeable. That's usually nice — but disastrous when you want
// UserId and OrderId to NOT be assignable to each other even though both
// are `string`.
//
// The fix: attach a unique "brand" to the type. The brand exists only at
// the type level; at runtime the value is still a plain string/number.

// ---------- the brand trick ----------
// `& { readonly __brand: ... }` makes the type structurally distinct from
// a plain string. Use a unique symbol or a literal as the brand marker.
type Brand<T, B> = T & { readonly __brand: B };

type UserId = Brand<string, "UserId">;
type OrderId = Brand<string, "OrderId">;

// ---------- constructors: the *only* way to mint a branded value ----------
function userId(s: string): UserId {
    if (!s.startsWith("u_")) throw new Error("invalid UserId");
    return s as UserId;
}

function orderId(s: string): OrderId {
    if (!s.startsWith("o_")) throw new Error("invalid OrderId");
    return s as OrderId;
}

// ---------- usage ----------
function deleteUser(id: UserId): void {
    console.log("deleting user", id);
}

// ---------- works for numbers too ----------
type Cents = Brand<number, "Cents">;
type Dollars = Brand<number, "Dollars">;

function dollarsToCents(d: Dollars): Cents {
    return (d * 100) as Cents;
}

function chargeCents(amount: Cents): void {
    console.log("charging", amount, "cents");
}

// ---------- branded "validated" types ----------
// A pattern: brand a type *after* validation. The brand is your proof.
type Email = Brand<string, "Email">;

function parseEmail(s: string): Email | null {
    return /^[^@\s]+@[^@\s]+\.[^@\s]+$/.test(s) ? (s as Email) : null;
}

function sendEmail(to: Email, body: string): void {
    console.log(`to=${to} body=${body}`);
}

function main(): void {
    const u = userId("u_42");
    const o = orderId("o_99");

    deleteUser(u);
    // deleteUser(o);            // ← compile error: OrderId is not UserId
    // deleteUser("u_42");        // ← compile error: raw string is not UserId

    const price = 9.99 as Dollars;
    chargeCents(dollarsToCents(price));

    const email = parseEmail("ada@example.com");
    if (email) sendEmail(email, "welcome");
    // sendEmail("not-an-email", "..."); // ← compile error
}

main();
