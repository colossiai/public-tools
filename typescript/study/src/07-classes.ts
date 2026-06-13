// Tier 2 — Lesson 07: Classes
//
// TS classes are JS classes + access modifiers + types.

// ---------- access modifiers + parameter properties ----------
// `private name: string` in the constructor declares AND assigns the field.
// This is one of TS's nicest shorthands.
class Account {
    constructor(
        public readonly id: string,
        private balance: number,
    ) {}

    deposit(amount: number): void {
        if (amount <= 0) throw new Error("amount must be positive");
        this.balance += amount;
    }

    getBalance(): number {
        return this.balance;
    }
}

// ---------- # for *true* runtime private (preferred over `private` for new code) ----------
// `private` is compile-time only — `(obj as any).balance` still reaches it at runtime.
// `#field` (ECMAScript private) is enforced by the JS runtime.
class SecureAccount {
    #balance: number;
    constructor(initial: number) { this.#balance = initial; }
    deposit(n: number): void { this.#balance += n; }
    balance(): number { return this.#balance; }
}

// ---------- abstract classes ----------
abstract class Shape {
    abstract area(): number;
    describe(): string {
        return `area=${this.area().toFixed(2)}`;
    }
}

class Circle extends Shape {
    constructor(private radius: number) { super(); }
    override area(): number {
        return Math.PI * this.radius ** 2;
    }
}

class Square extends Shape {
    constructor(private side: number) { super(); }
    override area(): number { return this.side ** 2; }
}

// ---------- implements ----------
interface Logger {
    log(msg: string): void;
}

class ConsoleLogger implements Logger {
    log(msg: string): void {
        console.log(`[LOG] ${msg}`);
    }
}

function main(): void {
    const acc = new Account("acc_1", 100);
    acc.deposit(50);
    console.log("account:", acc.id, acc.getBalance());

    const sec = new SecureAccount(1_000);
    sec.deposit(500);
    console.log("secure account:", sec.balance());

    const shapes: Shape[] = [new Circle(5), new Square(4)];
    for (const sh of shapes) console.log(sh.constructor.name, sh.describe());

    new ConsoleLogger().log("hi from a logger");
}

main();
