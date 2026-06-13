// Tier 4 — Lesson 17: Variance and function types
//
// Variance describes how subtyping interacts with type constructors.
//
//   Covariant     → if Cat extends Animal, then Box<Cat>  is a Box<Animal>.
//   Contravariant → if Cat extends Animal, then Box<Animal> is a Box<Cat>.   (flipped!)
//
// Function parameters are CONTRAVARIANT: a function taking `Animal` is a
// *subtype* of one taking `Cat`, because anywhere you can pass a Cat you can
// also call something that handles any Animal.
//
// Function return types are COVARIANT: returning a Cat is a subtype of
// returning an Animal.
//
// `strictFunctionTypes` (on with `strict`) enables proper contravariance for
// function-typed parameters. Without it, TS uses *bivariance* — looser, but
// occasionally unsafe.

class Animal { eat(): void { console.log("eating"); } }
class Cat extends Animal { meow(): void { console.log("meow"); } }
class Persian extends Cat { groom(): void { console.log("brushed"); } }

// ---------- return-type covariance ----------
type Make<T> = () => T;

const makeCat: Make<Cat> = () => new Cat();
const makeAnimal: Make<Animal> = makeCat; // ✓ Cat <: Animal, so returning Cat is ok where Animal is expected

// ---------- parameter contravariance ----------
type Consume<T> = (x: T) => void;

const consumeAnimal: Consume<Animal> = (a) => a.eat();
const consumeCat: Consume<Cat> = consumeAnimal; // ✓ a function that handles ANY animal also handles a Cat

// the reverse fails (good — would be unsafe):
// const consumeCat2: Consume<Cat> = (c) => c.meow();
// const consumeAnimal2: Consume<Animal> = consumeCat2; // ✗ animals don't necessarily meow

// ---------- method parameters are STILL bivariant ----------
// Methods declared with shorthand syntax `foo(x: T): void` are bivariant
// even under `strictFunctionTypes`. This is a deliberate compat exception.
// Use the property-arrow form to opt into strict contravariance:
interface StrictHandler {
    onClick: (e: Cat) => void;   // contravariant under strict mode
}
interface LooseHandler {
    onClick(e: Cat): void;       // bivariant (method form)
}

// ---------- covariance of readonly arrays; invariance of mutable arrays ----------
const cats: Cat[] = [new Cat()];
// const animals: Animal[] = cats;        // ✗ NOT allowed: you could push an Animal that isn't a Cat
const roAnimals: readonly Animal[] = cats; // ✓ readonly arrays ARE covariant (no push hazard)

// ---------- practical takeaway ----------
// When designing function types, prefer:
//   - Narrow output types (return what you actually have)
//   - Wide input types (accept the broadest thing you can handle)
// This is "Postel's law" in type-system form.

function main(): void {
    makeAnimal().eat();
    consumeCat(new Cat());

    const handler: StrictHandler = { onClick: (c) => c.meow() };
    handler.onClick(new Persian());

    console.log("readonly view length:", roAnimals.length);
}

main();
