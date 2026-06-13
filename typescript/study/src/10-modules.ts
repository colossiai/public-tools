// Tier 2 — Lesson 10: Modules (ESM imports/exports)
//
// Every `.ts` file with an import/export is an ESM module. Importing happens
// at the *file* level — no globals.
//
// Note `.ts` extensions in imports: with `"moduleResolution": "Bundler"` (our
// tsconfig) the tooling handles this. In Node-native ESM you'd write `.js`
// (the post-compile path) even when the source is `.ts`.

// named imports
import { PI, square } from "./lib/math.ts";

// default import (renames freely)
import cube from "./lib/math.ts";

// type-only import — fully erased at runtime, no JS emit
import type { Range } from "./lib/math.ts";

// namespace import — collects everything in one object
import * as math from "./lib/math.ts";

function inRange(n: number, r: Range): boolean {
    return n >= r.min && n <= r.max;
}

function main(): void {
    console.log("PI:", PI);
    console.log("square(5):", square(5));
    console.log("cube(3):", cube(3));
    console.log("inRange(5, [1,10]):", inRange(5, { min: 1, max: 10 }));
    console.log("math.* keys:", Object.keys(math));
}

main();

// ---------- about type-only imports ----------
// Use `import type { Foo }` when you ONLY use Foo in type positions. The
// compiler/bundler can then drop the import entirely. This avoids accidental
// runtime imports of files that only exist for types (common in monorepos
// with strict layering).
