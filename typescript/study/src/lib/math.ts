// Tier 2 — Lesson 10 support module
//
// Demonstrates ESM exports: named, default, re-export, and type-only.

export const PI = 3.14159;

export function square(n: number): number {
    return n * n;
}

export interface Range {
    min: number;
    max: number;
}

// default export — discouraged in libraries (harder to rename, no tooling
// guarantee on the import name) but valid syntax to know.
export default function cube(n: number): number {
    return n * n * n;
}
