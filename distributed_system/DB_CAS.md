# DB CAS (compare-and-swap via conditional UPDATE)

"CAS" = compare-and-swap. In the price-monitor fire-gate it's expressed as a
**conditional `UPDATE`** whose `WHERE` clause is the "compare" and whose `SET`
is the "swap" — done atomically in one SQL statement by the DB.

```go
q := tx.Model(&AlertEntry{}).Where("alert_id = ?", e.Id)
case FrequencyOnce:
    q = q.Where("fire_count = ?", 0)   // ← COMPARE: only if still 0
...
res := q.Updates(map[string]any{
    "fire_count":     gorm.Expr("fire_count + 1"),  // ← SWAP
    "last_fired_sec": nowSec,
    "last_fired_day": today,
})
// res.RowsAffected == 1 → we won; 0 → someone else already swapped it
```

compiles to:

```sql
UPDATE alert_entry
   SET fire_count = fire_count + 1, last_fired_sec = ?, last_fired_day = ?
 WHERE alert_id = ? AND fire_count = 0;   -- the compare
```

- `WHERE ... AND fire_count = 0` is the **compare** (expected current value).
- `SET` is the **swap** (new value).
- `RowsAffected` reports whether the swap happened: **1 = won the race**,
  **0 = precondition already false** (another replica got there first / already fired).

It's atomic because the DB takes a row lock for the duration of the `UPDATE`:
two concurrent replicas can't both see `fire_count = 0` and both update — the
second's `WHERE` no longer matches the now-`1` row, so it affects 0 rows.

## Per-frequency compare

The compare value differs per frequency, but the CAS pattern is identical:

| Frequency  | Compare (`WHERE`)            | Meaning                        |
|------------|------------------------------|--------------------------------|
| Once       | `fire_count = 0`             | swap only if never fired       |
| Daily      | `last_fired_day <> :today`   | swap only if not yet fired today |
| Continuous | `last_fired_sec <= :now-60`  | swap only if last fire ≥60s ago |

Only **one** replica inserts the `notify_record` per window: the CAS winner
(`RowsAffected==1`) proceeds to the insert inside the same transaction; the loser
returns `fired=false` and does nothing.

## Nuance vs. hardware CompareAndSwap

Hardware CAS compares against an *exact expected value* you pass in. Here the
Daily/Continuous compares are *predicates* (`<>`, `<=`), not equality — so it's
really a "conditional swap." `Once` is the one that's a literal equality compare
(`fire_count = 0`).
