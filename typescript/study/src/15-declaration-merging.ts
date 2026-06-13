// Tier 3 — Lesson 15: Declaration merging
//
// Multiple `interface` declarations with the same name *merge*. Same for
// namespaces. This is the mechanism behind "module augmentation" — adding
// properties to types from a library you don't own.
//
// Used everywhere in the ecosystem:
//   - Express: `declare global { namespace Express { interface Request { user?: User } } }`
//   - Vue: augmenting component options
//   - Vite/Webpack: declaring `import.meta.env` shape

// ---------- interface merging ----------
interface Person {
    name: string;
}
interface Person {
    age: number; // merged with the above; Person is now { name; age }
}

const p: Person = { name: "Ada", age: 36 }; // both required

// ---------- interface vs type alias ----------
// Type aliases CANNOT be re-declared:
// type T = { a: number };
// type T = { b: number };  // ← Duplicate identifier error
//
// This is one reason library authors prefer `interface` for *public* shapes —
// downstream users can augment them.

// ---------- module augmentation ----------
// Add a method to an existing module's exported type. We can't touch a
// real third-party package here, but the pattern is identical:
//
// declare module "some-lib" {
//     interface SomeLibConfig {
//         customField?: string;
//     }
// }
//
// Below: augment a type from our own ./lib/math.ts as a small demo.

declare module "./lib/math.ts" {
    interface Range {
        label?: string; // adds an optional field to the existing Range interface
    }
}

import type { Range } from "./lib/math.ts";

const r: Range = { min: 0, max: 10, label: "0..10" };

// ---------- global augmentation ----------
// Add a property to a global type (Window, NodeJS.ProcessEnv, etc).
declare global {
    interface ProcessEnvCustom {
        APP_REGION?: "us" | "eu" | "ap";
    }
}

function main(): void {
    console.log("merged Person:", p);
    console.log("augmented Range:", r);
    console.log("(globals also augment — see ProcessEnvCustom in source)");
}

main();
