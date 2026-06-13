// Tier 4 — Lesson 20: Decorators (TC39 stage-3, the modern variant)
//
// TS shipped two decorator systems:
//   - "Legacy" decorators behind `experimentalDecorators` — what NestJS / TypeORM use.
//   - "Modern" stage-3 decorators (TS 5.0+) — standards-track, no flag needed.
//
// This lesson uses the modern variant. Our tsconfig has
// `experimentalDecorators: false` to confirm we're on the standard syntax.
//
// A decorator is a function called with (value, context). It can wrap, replace,
// or annotate the decorated member.

// ---------- a simple method decorator: log calls ----------
function log<This, Args extends unknown[], Return>(
    original: (this: This, ...args: Args) => Return,
    context: ClassMethodDecoratorContext<This, (this: This, ...args: Args) => Return>,
): (this: This, ...args: Args) => Return {
    const methodName = String(context.name);
    return function (this: This, ...args: Args): Return {
        console.log(`→ ${methodName}(${args.map(String).join(", ")})`);
        const result = original.call(this, ...args);
        console.log(`← ${methodName} = ${String(result)}`);
        return result;
    };
}

// ---------- a getter decorator that memoizes ----------
function memoize<This, Return>(
    original: (this: This) => Return,
    _context: ClassGetterDecoratorContext<This, Return>,
): (this: This) => Return {
    const cache = new WeakMap<object, Return>();
    return function (this: This): Return {
        const key = this as unknown as object;
        if (!cache.has(key)) cache.set(key, original.call(this));
        return cache.get(key)!;
    };
}

// ---------- an accessor decorator: validate on set ----------
// `accessor x: T` (TS 5.0+) auto-generates a private slot + get/set pair.
// An accessor decorator can wrap either side; here we intercept the setter
// to reject negative values *every* time the field is written.
function positive<This>(
    target: ClassAccessorDecoratorTarget<This, number>,
    context: ClassAccessorDecoratorContext<This, number>,
): ClassAccessorDecoratorResult<This, number> {
    return {
        get(this: This): number {
            return target.get.call(this);
        },
        set(this: This, value: number): void {
            if (value < 0) throw new Error(`${String(context.name)} must be >= 0`);
            target.set.call(this, value);
        },
    };
}

// ---------- usage ----------
class Calculator {
    @positive accessor base: number = 10;

    @log
    add(n: number): number {
        return this.base + n;
    }

    @memoize
    get expensive(): number {
        // Pretend this is expensive — compute once, cache thereafter.
        console.log("  (computing expensive...)");
        return this.base * 1000;
    }
}

function main(): void {
    const c = new Calculator();

    c.add(5);
    c.add(7);

    console.log("expensive #1:", c.expensive);
    console.log("expensive #2:", c.expensive); // no recompute log

    try {
        c.base = -1;
    } catch (e) {
        console.log("validator caught:", (e as Error).message);
    }
}

main();
