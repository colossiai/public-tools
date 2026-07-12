// ============================================================================
// 04 — Traits: coherence, blanket impls, and static vs dynamic dispatch
// Run:  cargo run --example 04_traits_and_dispatch
// ----------------------------------------------------------------------------
// Java:  interfaces are nominal and must be declared AT the class definition
//        ("class C implements I"). You can't add an interface to a type you
//        don't own.
// Go:    interfaces are structural and implicit — but there's no coherence, no
//        generics-with-constraints story like this, and no zero-cost monomorph.
// C++:   concepts/templates give monomorphization, but no orphan rule and the
//        error messages are famously rough.
//
// Rust traits combine the best parts and add rules of their own:
//   • You can implement YOUR trait for a FOREIGN type (extension methods).
//   • Blanket impls: implement a trait for ALL types satisfying a bound.
//   • Two dispatch modes: generics (static, monomorphized, zero-cost) OR
//     `dyn Trait` (dynamic, vtable) — YOU choose per call site.
//   • The orphan/coherence rule guarantees one impl globally (no conflicts).
// ============================================================================

fn main() {
    extension_on_a_foreign_type();
    blanket_impl();
    static_vs_dynamic_dispatch();
}

// --- Implement your trait for a type you don't own (here: i32 and str) -------
trait Summary {
    fn summary(&self) -> String;
}
impl Summary for i32 {
    fn summary(&self) -> String {
        format!("the integer {self}")
    }
}
impl Summary for String {
    fn summary(&self) -> String {
        format!("a {}-char string", self.len())
    }
}
fn extension_on_a_foreign_type() {
    println!("[extension] {}", 42.summary());
    println!("[extension] {}", String::from("hello").summary());
    // In Java you could never add a method to Integer or String like this.
}

// --- Blanket impl: define behavior for EVERY type meeting a bound ------------
trait Loud {
    fn shout(&self) -> String;
}
impl<T: Summary> Loud for T {
    // Every T that is Summary automatically gets shout(), for free.
    fn shout(&self) -> String {
        self.summary().to_uppercase() + "!!!"
    }
}
fn blanket_impl() {
    println!("[blanket] {}", 7.shout());
    println!("[blanket] {}", String::from("buy").shout());
}

// --- Static dispatch (generic) vs dynamic dispatch (dyn) ---------------------
// generic fn: the compiler stamps out a specialized copy per concrete type
// (monomorphization) — inlinable, zero indirection, larger binary.
fn describe_static<T: Summary>(x: &T) -> String {
    x.summary()
}
// dyn fn: one copy, a vtable pointer chosen at runtime — smaller binary,
// heterogeneous collections, one pointer of indirection.
fn describe_dynamic(x: &dyn Summary) -> String {
    x.summary()
}
fn static_vs_dynamic_dispatch() {
    println!("[static]  {}", describe_static(&99));

    // A heterogeneous list is only possible via trait objects:
    let items: Vec<Box<dyn Summary>> = vec![Box::new(1), Box::new(2)];
    for it in &items {
        println!("[dynamic] {}", describe_dynamic(it.as_ref()));
    }
}
