// Tier 2 — Lesson 08: Enums vs `as const` unions
//
// `enum` is one of TS's oldest features and one of its most controversial.
// Most modern codebases (including the TS team itself in newer code) prefer
// `as const` + literal unions. This lesson shows why.

// ---------- numeric enum (default) ----------
enum LogLevelEnum {
    Debug,   // 0
    Info,    // 1
    Warn,    // 2
    Error,   // 3
}
// Compiles to a JS object — *exists at runtime*. Also creates reverse mapping
// (LogLevelEnum[0] === "Debug"), which surprises people and bloats output.

// ---------- string enum ----------
enum Color {
    Red = "red",
    Green = "green",
    Blue = "blue",
}

// ---------- the modern alternative: as const object + derived union ----------
const LogLevel = {
    Debug: 0,
    Info: 1,
    Warn: 2,
    Error: 3,
} as const;
type LogLevel = typeof LogLevel[keyof typeof LogLevel];
// type LogLevel = 0 | 1 | 2 | 3

function shouldLog(level: LogLevel, threshold: LogLevel): boolean {
    return level >= threshold;
}

// ---------- or just: literal union directly ----------
type Theme = "light" | "dark" | "system";
function applyTheme(t: Theme): void {
    console.log("theme:", t);
}

// ---------- why `as const` wins for most teams ----------
// 1. Smaller compiled output (no enum runtime object).
// 2. No reverse mapping surprises.
// 3. Works with `isolatedModules` / Bundler module mode without quirks.
// 4. Easier to JSON-serialize and inspect.
// 5. Plays nicely with libraries like zod / valibot.
//
// Stick with `enum` when:
// - You're maintaining existing code that uses it.
// - You need the runtime object AND the type from the same identifier.

function main(): void {
    console.log("enum LogLevelEnum.Info:", LogLevelEnum.Info, LogLevelEnum[1]);
    console.log("enum Color.Red:", Color.Red);

    console.log("shouldLog(Info, Warn):", shouldLog(LogLevel.Info, LogLevel.Warn));
    applyTheme("dark");
}

main();
