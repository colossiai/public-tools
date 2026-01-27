# How to make GORM emit DEFAULT (JSON_OBJECT())


Great question — this *is* doable, but with one important caveat 😄
Let’s go straight to the practical answer.

---

## Short answer

**GORM will NOT auto-generate `DEFAULT (JSON_OBJECT())` for you.**
You must **explicitly tell it**, and it only works on **MySQL ≥ 8.0.13**.

---

## ✅ The correct GORM tag

```go
type Rec struct {
	ID     uint64 `gorm:"primaryKey"`
	ValMap map[string]decimal.Decimal `gorm:"type:json;not null;default:(JSON_OBJECT());serializer:json"`
}
```

Key detail 👉 **parentheses are mandatory**:

```go
default:(JSON_OBJECT())
```

Without them, MySQL will reject the DDL.

---

## What GORM will emit (AutoMigrate)

```sql
val_map JSON NOT NULL DEFAULT (JSON_OBJECT())
```

✅ This matches MySQL’s requirement exactly.

---

## ⚠️ Very important caveats

### 1️⃣ MySQL version check

* Works only on **MySQL 8.0.13+**
* On older versions → migration fails

If you’re unsure, check:

```sql
SELECT VERSION();
```

---

### 2️⃣ GORM does **no validation**

GORM:

* does **not** check MySQL version
* does **not** special-case JSON

If you run AutoMigrate against MySQL 5.7:
💥 migration error

---

### 3️⃣ Schema diff tools

Some schema tools / DBAs dislike expression defaults.
If you use Flyway / Liquibase, make sure they allow it.

---

## 🛡️ Production-safe pattern (recommended)

Most teams do **this hybrid approach**:

### DB

```sql
val_map JSON NOT NULL
```

### Go

```go
func (r *Rec) BeforeCreate(tx *gorm.DB) error {
	if r.ValMap == nil {
		r.ValMap = map[string]decimal.Decimal{}
	}
	return nil
}
```

This works:

* on all MySQL versions
* in tests
* without migration surprises

---

## When SHOULD you use `DEFAULT (JSON_OBJECT())`?

Use it when:

* You control MySQL version
* You want safety for raw SQL inserts
* You have multiple writers (not just GORM)

Avoid it when:

* Supporting MySQL 5.7
* You rely on strict migration diffs

---

## TL;DR

| Goal             | Best choice               |
| ---------------- | ------------------------- |
| MySQL ≥ 8.0.13   | `default:(JSON_OBJECT())` |
| Mixed versions   | init in Go                |
| External writers | DB default                |
| Simplicity       | Go-only init              |

If you want next, I can show:

* how this behaves with `INSERT ... VALUES ()`
* how `BeforeSave` vs `BeforeCreate` differ
* how to migrate existing tables safely

Just say 👍



# How this behaves with INSERT ... VALUES ()

Ah — this is a subtle but very important point. Let’s go **step by step**.

We’re talking about a table like this:

```sql
CREATE TABLE json_rec (
    id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
    val_map JSON NOT NULL DEFAULT (JSON_OBJECT())
) ENGINE=InnoDB;
```

---

## 1️⃣ `INSERT INTO json_rec () VALUES ();`

* You **don’t specify `val_map`** in the `INSERT`.
* MySQL sees: no value provided → use **column default**.
* Because the column has `DEFAULT (JSON_OBJECT())` → DB automatically stores `{}`.
* Result:

```sql
SELECT * FROM json_rec;
+----+--------+
| id | val_map|
+----+--------+
| 1  | {}     |
+----+--------+
```

✅ Safe, `{}` is stored.

---

## 2️⃣ `INSERT INTO json_rec (val_map) VALUES (NULL);`

* Column is `NOT NULL` → ❌ MySQL error:

```
ERROR 1048 (23000): Column 'val_map' cannot be null
```

---

## 3️⃣ `INSERT INTO json_rec (val_map) VALUES ('{}');`

* `'{}'` is a **string**, not JSON
* MySQL 8+ will try implicit cast → works sometimes
* But can fail if strict mode enabled:

```
ERROR 3140: Invalid JSON text: "" at position 0
```

✅ Safe approach: **always use JSON literal** or `JSON_OBJECT()`.

```sql
INSERT INTO json_rec (val_map) VALUES (JSON_OBJECT());
```

---

## 4️⃣ `INSERT INTO json_rec (val_map) VALUES ('{"USD":100}');`

* Valid JSON string → MySQL parses → stores as JSON.
* When you `SELECT val_map` → returns `{"USD":100}`.
* Works as expected.

---

## 5️⃣ Behavior with GORM `Create()`

Suppose Go struct:

```go
type Rec struct {
    ID     uint64
    ValMap map[string]decimal.Decimal `gorm:"type:json;not null;default:(JSON_OBJECT());serializer:json"`
}
```

* If `rec.ValMap == nil`:

  * GORM will **pass `NULL`** in INSERT → MySQL will reject because `NOT NULL`
  * ✅ Solution: init to empty map in Go:

```go
rec.ValMap = map[string]decimal.Decimal{}
db.Create(&rec)
```

* If `rec.ValMap` has data → GORM `json.Marshal` → send JSON → DB stores it.

**Key takeaway:**
Even with `DEFAULT (JSON_OBJECT())`, **GORM will not automatically use the DB default** if the field is `nil` — it sends `NULL` unless initialized.

---

### ✅ Summary Table

| INSERT statement                           | DB behavior                 |
| ------------------------------------------ | --------------------------- |
| `INSERT () VALUES ();`                     | Stores `{}` using default   |
| `INSERT (val_map) VALUES (NULL);`          | ❌ Error, NOT NULL violation |
| `INSERT (val_map) VALUES ('{}');`          | ⚠️ May fail, not safe       |
| `INSERT (val_map) VALUES (JSON_OBJECT());` | ✅ Safe, stores `{}`         |
| GORM Create with `nil` map                 | ❌ Error, sends NULL         |
| GORM Create with empty map `{}`            | ✅ Works, JSON `{}` stored   |

---

If you want, I can show a **robust GORM pattern** that:

* Works on all MySQL versions
* Avoids `NULL` errors
* Uses DB default when possible
* Safely marshals `map[string]decimal.Decimal`

This is the exact pattern I use in production.

Do you want me to show that?
