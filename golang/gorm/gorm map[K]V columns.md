# gorm map[K]V column handling

```go

I insert table with go gorm create() for following struct

type Rec struct {
	Ccy                               string                     `gorm:"column:ccy;type:varchar(32);not null;uniqueIndex:idx_bill_date_ccy,priority:2;"`     
	BillDate                          time.Time                  `gorm:"column:bill_date;type:datetime;not null;uniqueIndex:idx_bill_date_ccy,priority:1;"`  
	AssetsCustomMap                   map[string]decimal.Decimal `gorm:"column:assets_custom_map;type:json;not null;"`                                       
}

got error:

err:sql: converting argument $10 type: unsupported type map[string]decimal.Decimal, a map
```


Yep — this is a classic GORM + `database/sql` gotcha 👍
The short version: **`database/sql` cannot bind a Go `map` directly**, even if your column type is `JSON`. GORM doesn’t magically serialize arbitrary maps unless you tell it how.

That’s exactly what this error means:

> `unsupported type map[string]decimal.Decimal, a map`

---

## Why this happens

* MySQL `JSON` column expects **string / []byte**
* `database/sql` only knows how to send:

  * basic types (`string`, `int`, `[]byte`, `time.Time`, etc.)
  * OR types implementing **`driver.Valuer`**
* `map[string]decimal.Decimal` does **neither**

So GORM has no idea how to convert it before sending it to MySQL.

---

## ✅ Correct solutions (pick one)

### **Option 1 (Recommended): Use GORM’s built-in JSON serializer**

This is the cleanest solution in modern GORM.

```go
type Rec struct {
	Ccy      string    `gorm:"column:ccy;type:varchar(32);not null;uniqueIndex:idx_bill_date_ccy,priority:2"`
	BillDate time.Time `gorm:"column:bill_date;type:datetime;not null;uniqueIndex:idx_bill_date_ccy,priority:1"`

	AssetsCustomMap map[string]decimal.Decimal `gorm:"column:assets_custom_map;type:json;not null;serializer:json"`
}
```

✅ What this does:

* GORM auto `json.Marshal` on INSERT/UPDATE
* Auto `json.Unmarshal` on SELECT
* No custom code needed

📌 **Works with `decimal.Decimal`** because it already supports JSON marshal/unmarshal.

---

### **Option 2: Use `datatypes.JSONMap` (simple but less precise)**

```go
import "gorm.io/datatypes"

type Rec struct {
	AssetsCustomMap datatypes.JSONMap `gorm:"column:assets_custom_map;type:json;not null"`
}
```

⚠️ Downside:

* Values become `interface{}`
* You lose `decimal.Decimal` typing (numbers become `float64`)

Use this only if precision doesn’t matter.

---

### **Option 3: Custom type implementing `Scanner` / `Valuer` (most control)**

Best if you want **strict typing + validation**.

```go
type DecimalMap map[string]decimal.Decimal

func (m DecimalMap) Value() (driver.Value, error) {
	if m == nil {
		return []byte(`{}`), nil
	}
	return json.Marshal(m)
}

func (m *DecimalMap) Scan(value interface{}) error {
	if value == nil {
		*m = make(DecimalMap)
		return nil
	}

	bytes, ok := value.([]byte)
	if !ok {
		return fmt.Errorf("failed to scan DecimalMap")
	}

	return json.Unmarshal(bytes, m)
}
```

Then:

```go
type Rec struct {
	AssetsCustomMap DecimalMap `gorm:"column:assets_custom_map;type:json;not null"`
}
```

---

## 🚫 What does NOT work

```go
map[string]decimal.Decimal // ❌ without serializer or Valuer
```

GORM will always fail with the error you saw.

---

## TL;DR (What you should do)

👉 **Add `serializer:json` to your field tag**

```go
AssetsCustomMap map[string]decimal.Decimal `gorm:"type:json;not null;serializer:json"`
```

That’s it. Your `Create()` will work immediately.

If you want, I can also show:

* how GORM handles `NULL / '' / '{}'` for JSON columns
* MySQL JSON indexing strategies
* how this behaves with `Find()` / `Scan()` results

Just say the word 👌



# Add serializer:json just affect GORM, not related to mysql DDL?


Exactly 👍 — **you’ve got it right.**

### Short answer

**`serializer:json` affects only GORM’s behavior, not MySQL DDL.**

---

### What `serializer:json` actually does

* Tells **GORM** how to:

  * ✅ convert Go ↔ DB values
  * `json.Marshal` **before INSERT / UPDATE**
  * `json.Unmarshal` **after SELECT**
* It makes your field implement the equivalent of:

  * `driver.Valuer`
  * `sql.Scanner`
* This happens **inside GORM**, *before* `database/sql` talks to MySQL

➡️ MySQL never sees a `map` — it only ever receives `[]byte` / `string`.

---

### What it does **NOT** do

❌ Does **not** change:

* Column type
* Indexes
* Constraints
* Table schema
* Generated SQL DDL

This tag:

```go
AssetsCustomMap map[string]decimal.Decimal `gorm:"type:json;serializer:json;not null"`
```

Produces the **same MySQL column** as:

```sql
assets_custom_map JSON NOT NULL
```

Whether `serializer:json` exists or not.

---

### Mental model (important)

Think of it as **two layers**:

```
Go struct
   ↓ (serializer:json)
database/sql arguments (string / []byte)
   ↓
MySQL JSON column
```

* `type:json` → **DDL concern**
* `serializer:json` → **ORM runtime concern**

They live in totally different worlds.

---

### Bonus: why GORM splits this

GORM supports **many serializers**:

* `json`
* `gob`
* `unixtime`
* custom serializers

So serialization is intentionally **decoupled from schema**.

---

### One more subtle but useful tip ⚠️

If you run **AutoMigrate**:

```go
gorm:"type:json;serializer:json"
```

* `type:json` → affects `ALTER TABLE`
* `serializer:json` → ignored by migration logic

So migrations stay deterministic 👍

---

### TL;DR

| Tag part          | Affects                             |
| ----------------- | ----------------------------------- |
| `type:json`       | MySQL column type                   |
| `serializer:json` | GORM runtime (Create / Find / Scan) |
| MySQL             | Completely unaware                  |

If you want, I can also explain how this compares with:

* `datatypes.JSON`
* custom `Scanner/Valuer`
* what happens if DB value is `''`, `NULL`, or `{}`

Just ask 😄


# What happens if DB value is '', NULL, or {}

Great question — this is where JSON columns + GORM get *subtle* 👀
Let’s break it down **exactly** for `serializer:json` with:

```go
AssetsCustomMap map[string]decimal.Decimal `gorm:"type:json;serializer:json;not null"`
```

I’ll cover **what MySQL allows**, **what GORM sees**, and **what you get in Go**.

---

## 1️⃣ DB value = `NULL`

### MySQL side

* Allowed **only if column is nullable**
* With `NOT NULL` → ❌ insert/update fails

### GORM behavior

* DB returns `NULL`
* Serializer receives `nil`

### Go result

```go
AssetsCustomMap == nil
```

⚠️ Important:

* Even if your struct field is `map`, GORM does **not auto-init** it
* Accessing it without checking → panic

```go
m := rec.AssetsCustomMap
fmt.Println(len(m))   // OK (0)
m["a"] = decimal.Zero // ❌ panic if m == nil
```

---

## 2️⃣ DB value = `{}` (empty JSON object) ✅ **BEST PRACTICE**

### MySQL side

* Valid JSON
* Works with `NOT NULL`
* Ideal default

### GORM behavior

* `json.Unmarshal([]byte("{}"), &map)`

### Go result

```go
AssetsCustomMap != nil
len(AssetsCustomMap) == 0
```

✅ Safe to write to immediately:

```go
rec.AssetsCustomMap["USD"] = decimal.NewFromInt(100)
```

📌 **Recommendation**
Always use `{}` as the default JSON value.

---

## 3️⃣ DB value = `''` (empty string) ❌ **BAD**

### MySQL side

* **Invalid JSON**
* MySQL 5.7+:

  ```sql
  ERROR 3140: Invalid JSON text
  ```
* Only possible if:

  * column is `TEXT`
  * OR bad legacy data
  * OR `sql_mode` is very permissive

### GORM behavior

* MySQL returns `[]byte("")`
* `json.Unmarshal("")` → error

### Result

```text
invalid character ' ' looking for beginning of value
```

➡️ Your `Find()` or `Scan()` will **fail**

---

## Comparison table (quick scan)

| DB value | Allowed in JSON col | Go value        | Safe? |
| -------- | ------------------- | --------------- | ----- |
| `NULL`   | ✔ (nullable only)   | `nil` map       | ⚠️    |
| `{}`     | ✔                   | empty map       | ✅     |
| `''`     | ❌                   | unmarshal error | 💥    |

---

## 💡 Best practices (production-safe)

### 1. Use `NOT NULL` + default `{}`

```sql
assets_custom_map JSON NOT NULL DEFAULT (JSON_OBJECT())
```

or in GORM:

```go
gorm:"type:json;not null;default:'{}';serializer:json"
```

(MySQL requires quotes around `{}` in default)

---

### 2. Defensive initialization (optional)

If you *might* read legacy data:

```go
if rec.AssetsCustomMap == nil {
	rec.AssetsCustomMap = make(map[string]decimal.Decimal)
}
```

---

### 3. Never use empty string for JSON

If you see this in prod:

```sql
UPDATE t SET assets_custom_map = '{}' WHERE assets_custom_map = '';
```

Run. Fix. Never look back 😄

---

## 🔥 One subtle GORM detail (advanced)

When **inserting**:

```go
rec.AssetsCustomMap == nil
```

* With `NOT NULL` → ❌ insert fails
* With nullable → DB stores `NULL`, not `{}`

So if you want `{}`:

```go
rec.AssetsCustomMap = map[string]decimal.Decimal{}
```

---

## TL;DR

* ✅ `{}` → perfect
* ⚠️ `NULL` → usable but map is nil
* ❌ `''` → breaks JSON unmarshal

If you want, next we can dive into:

* JSON partial updates (`JSON_SET`) with GORM
* indexing JSON fields
* handling precision with `decimal.Decimal` in MySQL JSON

Just say 👌

# error: mysql DDL for json default

```sql
CREATE TABLE `json_rec` (
  `id` bigint unsigned NOT NULL AUTO_INCREMENT,
  `created_at` datetime(3) NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
  `updated_at` datetime(3) NOT NULL DEFAULT CURRENT_TIMESTAMP(3) ON UPDATE CURRENT_TIMESTAMP(3),
  `val_map` json NOT NULL DEFAULT '',
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;


got error:
Error Code: 1101. BLOB, TEXT, GEOMETRY or JSON column 'val_map' can't have a default value	
```

Yep — this one is **100% MySQL**, not GORM 😄
And the error message is actually spot-on.

---

## Why this fails

```sql
`val_map` json NOT NULL DEFAULT '',
```

Two problems at once:

1️⃣ **JSON columns cannot have string defaults**

* `''` is a **string**, not JSON
* Even `{}` as a literal is still not allowed (see below)

2️⃣ **MySQL does not allow DEFAULT values for JSON**

* JSON is treated like `BLOB / TEXT`
* Those types **cannot have a DEFAULT** (except expressions in newer versions)

That’s why MySQL throws:

> `BLOB, TEXT, GEOMETRY or JSON column 'val_map' can't have a default value`

---

## What MySQL allows (by version)

### ❌ This is NEVER allowed

```sql
json NOT NULL DEFAULT ''
json NOT NULL DEFAULT '{}'
```

Even though `{}` is valid JSON, MySQL still forbids it as a default literal.

---

### ✅ MySQL 8.0.13+ — **functional default (expression)**

This **does work**:

```sql
val_map JSON NOT NULL DEFAULT (JSON_OBJECT())
```

Key points:

* Must be an **expression**
* Must be wrapped in parentheses
* `JSON_OBJECT()` returns `{}`

This is the **only correct way** to have a default `{}` at the DB level.

---

### ❌ MySQL < 8.0.13

No defaults at all for JSON. Period.

You must handle it in the application layer.

---

## What GORM does (important)

If you use:

```go
gorm:"type:json;not null;default:'{}';serializer:json"
```

⚠️ **GORM will happily generate invalid DDL** unless:

* You’re on MySQL 8.0.13+
* AND you manually override it

GORM **does not automatically translate** `'{}'` → `JSON_OBJECT()`.

---

## ✅ Correct table definitions

### Best (MySQL 8.0.13+)

```sql
CREATE TABLE json_rec (
  id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  created_at DATETIME(3) NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
  updated_at DATETIME(3) NOT NULL DEFAULT CURRENT_TIMESTAMP(3)
    ON UPDATE CURRENT_TIMESTAMP(3),
  val_map JSON NOT NULL DEFAULT (JSON_OBJECT()),
  PRIMARY KEY (id)
) ENGINE=InnoDB;
```

---

### Safe (any MySQL version)

```sql
val_map JSON NOT NULL
```

Then in Go **always initialize**:

```go
rec.ValMap = map[string]decimal.Decimal{}
db.Create(&rec)
```

---

## 💡 Production best practice (real talk)

**Do both if you can:**

* DB: `NOT NULL`
* App: always initialize to `{}`

This guarantees:

* No `NULL`
* No panics
* No broken reads
* No reliance on MySQL quirks

---

## TL;DR

| Attempt                   | Result           |
| ------------------------- | ---------------- |
| `DEFAULT ''`              | ❌ invalid        |
| `DEFAULT '{}'`            | ❌ invalid        |
| `DEFAULT (JSON_OBJECT())` | ✅ MySQL ≥ 8.0.13 |
| No default + init in Go   | ✅ always safe    |

If you want, I can show:

* how to make GORM emit `DEFAULT (JSON_OBJECT())`
* how to backfill bad legacy rows
* how this behaves with `INSERT ... VALUES ()`

Just say the word 👌


# 💡 Production best practice (real talk)

**Do both if you can:**

* DB: `NOT NULL` (even better: DEFAULT (JSON_OBJECT()))
* App: always initialize to `{}`
