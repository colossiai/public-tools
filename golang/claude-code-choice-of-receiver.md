# #Why in most place, you prefer (a Foo), not (a *Foo)

* 2026-MAY

## Short answer: I don't have a blanket preference — the choice follows Go conventions based on what the method does.

I lean toward value receivers (a Foo) when:
- The method only reads fields (no mutation).
- Foo is small (a few words: ints, pointers, small structs) — copying is cheaper than the indirection + escape-to-heap that pointer receivers often cause.
- I want the zero value to be usable safely without nil checks.
- The type is effectively a value (think time.Time, decimal.Decimal, IDs, enums).

I switch to pointer receivers (a *Foo) when:
- The method mutates state.
- Foo is large or contains arrays/many fields (copy cost matters).
- Foo contains a sync.Mutex, sync.WaitGroup, or other no-copy types (vet will complain otherwise).
- Some methods on the type already need *Foo — Go style says keep the receiver type consistent across all methods.
- The type represents an entity with identity (a long-lived service, a connection, a manager).
