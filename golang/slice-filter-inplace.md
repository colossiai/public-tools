# Go Slice Filter-In-Place (`deduped[:0]`)

## Q1: explain `deduped[:0]`

`deduped[:0]` is a Go **slice expression** that produces a slice with **length 0 but the same underlying array (and capacity)** as `deduped`.

### What it does

For a slice `s`, the expression `s[low:high]` yields a slice covering elements `[low, high)`. So `deduped[:0]` means `deduped[0:0]` — start at 0, end at 0 → **zero elements**.

Key point: it does **not** allocate. The result shares `deduped`'s backing array, so:
- `len(result) == 0`
- `cap(result) == cap(deduped)` (capacity from index 0 to the end of the array is preserved)

### Why it's used — the classic "filter in place" idiom

```go
deduped := deduped[:0]              // reset length, keep the backing array
seen := map[string]bool{}
for _, x := range items {
    if !seen[x] {
        seen[x] = true
        deduped = append(deduped, x)  // reuses existing storage, no new alloc
    }
}
```

Because `append` writes back into the same array that already had capacity, this avoids allocating a second slice. It's the standard trick for de-duplicating or filtering a slice while reusing memory.

### Caveat

Since it shares storage, the original data is overwritten as you `append`. If you still need the old contents, don't use this pattern. Also, elements beyond the new length aren't garbage-collected (the array still references them) — for pointer/slice elements you may want to nil them out to avoid leaks.

---

## Q2: Is `eligible := deduped[:0]` equal to `eligible = make([]xxx, 0, len(deduped))`?

Code in question:

```go
eligible := deduped[:0]
for _, row := range deduped {
    if nowMs >= holidayCreateAtNY(row.HolidayDate) {
        eligible = append(eligible, row)
    }
}
```

Not quite — they behave the same **length-wise**, but they differ in two important ways:

### 1. Memory: shared array vs. new allocation

| | `deduped[:0]` | `make([]T, 0, len(deduped))` |
|---|---|---|
| Backing array | **Same** as `deduped` | **New**, freshly allocated |
| Allocation | Zero — reuses storage | One heap allocation |
| Effect of `append` | **Overwrites `deduped`'s elements** | Leaves `deduped` untouched |

### 2. Capacity

- `deduped[:0]` → `cap == cap(deduped)`, which can be **larger** than `len(deduped)` if the slice was over-allocated.
- `make([]T, 0, len(deduped))` → `cap == len(deduped)` exactly.

### Why this specific code is safe (and clever)

This is the **filter-in-place** idiom. It works here precisely because of the aliasing:

```go
eligible := deduped[:0]       // same array, len 0
for _, row := range deduped { // reads deduped[i]
    if ... {
        eligible = append(eligible, row)  // writes eligible[j], where j <= i
    }
}
```

The write index `j` is always **≤** the read index `i` (you never keep more than you've read), so each `append` overwrites a slot that has already been read this iteration or earlier. No data is clobbered before it's used. The payoff is **zero allocation**.

The `make(...)` version produces the same `eligible` values, but allocates a separate array and leaves `deduped` intact.

### The one gotcha

After this loop, `deduped` is effectively **destroyed** — its leading elements now hold the filtered results, and its tail holds stale duplicates. If any code after this point still reads `deduped`, you must use the `make` version instead. If `deduped` is never touched again, `deduped[:0]` is the better choice.

---

## Q3: Will the tail of `eligible` contain stale items of `deduped`?

No — **`eligible` itself does not contain stale items.**

A slice only exposes elements in the range `[0, len)`. Since `len(eligible)` equals exactly the number of rows that passed the filter, indexing or ranging over `eligible` only ever touches the filtered results. The stale duplicates live **beyond `len(eligible)`**, in the capacity region of the shared backing array.

### Where the stale items actually are

```
backing array (shared):
index:     0     1     2     3     4     5
        [ okA  okB  okC | staleD staleE staleF ]
          └──────────────┘ └──────────────────┘
          eligible[0:3]      capacity region
          len=3              (not part of eligible)
```

- `eligible` → clean: `[okA, okB, okC]`, `len == 3`
- The stale tail is only reachable if you **deliberately re-slice past the length**, e.g. `eligible[:cap(eligible)]` or via the old `deduped` variable (`deduped[3:]`).

### The practical implications

1. **Ranging/indexing `eligible`** → totally safe, no stale data.
2. **`deduped` is now corrupted** → `deduped[0:len(eligible)]` holds the filtered copies, and its tail holds leftover duplicates. Don't read `deduped` after this loop.
3. **GC / memory leak note** → if `row` holds pointers (or is a struct with pointer fields), the stale copies in the capacity region are *still referenced* by the backing array, so they won't be garbage-collected while `eligible` is alive. Usually negligible here, but worth knowing if the elements are large or hold references you want freed.

So: clean slice, but at the cost of leaving `deduped`'s backing array scrambled behind it.
