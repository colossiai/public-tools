# In gorm library, ErrRecordNotFound seems like business error, why gorm mix ErrRecordNotFound with the same category of IO errors


Good question — this confusion is very common, and it comes from **GORM’s historical and pragmatic design choices**, not from clean domain modeling.

### Short answer

**`ErrRecordNotFound` is *not* an I/O error conceptually**, but GORM exposes it as an `error` **for API ergonomics and backward compatibility**, not because it thinks “not found” is the same kind of failure as DB I/O errors.

---

## Why GORM treats `ErrRecordNotFound` as `error`

### 1. Go’s `error` is a *control channel*, not strictly “errors”

In Go, `error` is often used for:

* failures (I/O, network, corruption)
* **absence of data**
* control-flow signals

Classic examples:

```go
io.EOF              // not really an error
sql.ErrNoRows       // not a DB failure
context.Canceled   // expected control signal
```

`gorm.ErrRecordNotFound` follows this pattern.

---

### 2. GORM is built on `database/sql`

`database/sql` already established the precedent:

```go
sql.ErrNoRows
```

GORM intentionally mirrors this behavior:

* Developers already expect to check:

  ```go
  errors.Is(err, gorm.ErrRecordNotFound)
  ```
* Mapping it to `error` avoids inventing a new return channel

This is **inheritance of ecosystem convention**, not ideal modeling.

---

### 3. GORM is a data-access library, not a domain layer

From GORM’s perspective:

> “Did the query succeed?”

A query that returns zero rows is *not fully successful*, so it reports via `error`.

But:

* GORM **does not claim** this is a business error
* It simply exposes a **data-access outcome**

**Interpreting it as business meaning is the caller’s responsibility.**

---

### 4. Historical API compatibility (v1 → v2)

Older GORM versions:

* Returned `ErrRecordNotFound` *only via `error`*
* Counted on callers to branch on it

Changing this would:

* Break millions of lines of code
* Force every call site to change signature

So v2 keeps it, but improves detection:

```go
errors.Is(err, gorm.ErrRecordNotFound)
```

---

## Why this feels wrong in clean architecture

You’re absolutely right architecturally:

| Layer            | “Record not found” should be  |
| ---------------- | ----------------------------- |
| DAO / Repository | Data absence signal           |
| Domain           | Valid state (optional entity) |
| Application      | Possibly business error       |
| Transport        | 404 / empty response          |

But GORM **lives only in the DAO layer**.

---

## Correct way to handle this (recommended)

### ❌ What *not* to do

```go
if err != nil {
    return err // leaks GORM semantics upward
}
```

### ✅ Proper repository boundary

```go
func (r *UserRepo) GetByID(id int64) (*User, error) {
    var u User
    err := r.db.First(&u, id).Error

    if errors.Is(err, gorm.ErrRecordNotFound) {
        return nil, nil // or custom NotFound error
    }
    if err != nil {
        return nil, err
    }
    return &u, nil
}
```

Or with explicit domain error:

```go
var ErrUserNotFound = errors.New("user not found")

if errors.Is(err, gorm.ErrRecordNotFound) {
    return nil, ErrUserNotFound
}
```

---

## Why GORM didn’t choose a better API

They could have done:

```go
result := db.First(&u)
if result.RowsAffected == 0 { ... }
```

But that would:

* Be verbose
* Be inconsistent with `database/sql`
* Break existing mental models

So they chose **pragmatism over purity**.

---

## Mental model to keep

> **`gorm.ErrRecordNotFound` is a DAO-level sentinel, not a failure.**

Treat it like:

* `sql.ErrNoRows`
* `io.EOF`

**Never let it escape your repository layer unchanged.**

---

If you want, I can:

* Show a **clean repository interface pattern**
* Compare GORM vs sqlc behavior
* Help you design a typed `Option[T]` / `Result[T]` wrapper to avoid this entirely (which fits nicely with your config-registry work)

Just say the word.

# Show clean repository interface pattern

Below is a **clean, production-grade repository interface pattern** that **fully isolates GORM** and **eliminates `ErrRecordNotFound` leakage**, while staying idiomatic Go.

I’ll show **three levels**, from simplest → most explicit.
Given your backend/API background, **Level 2 is the sweet spot**.

---

## Level 1 — Minimal & idiomatic (nil means not found)

### Domain

```go
type User struct {
	ID   int64
	Name string
}
```

### Repository interface (domain-facing)

```go
type UserRepository interface {
	FindByID(ctx context.Context, id int64) (*User, error)
}
```

### GORM implementation (infra layer)

```go
type userRepoGorm struct {
	db *gorm.DB
}

func (r *userRepoGorm) FindByID(ctx context.Context, id int64) (*User, error) {
	var u User
	err := r.db.WithContext(ctx).First(&u, id).Error

	if errors.Is(err, gorm.ErrRecordNotFound) {
		return nil, nil
	}
	if err != nil {
		return nil, err
	}
	return &u, nil
}
```

### Service usage

```go
u, err := repo.FindByID(ctx, id)
if err != nil {
	return err
}
if u == nil {
	return ErrUserNotFound
}
```

✅ Simple
⚠️ Caller must remember `nil == not found`

---

## Level 2 — Explicit domain error (recommended)

### Domain error

```go
var ErrUserNotFound = errors.New("user not found")
```

### Repository interface

```go
type UserRepository interface {
	GetByID(ctx context.Context, id int64) (*User, error)
}
```

### GORM implementation

```go
func (r *userRepoGorm) GetByID(ctx context.Context, id int64) (*User, error) {
	var u User
	err := r.db.WithContext(ctx).First(&u, id).Error

	if errors.Is(err, gorm.ErrRecordNotFound) {
		return nil, ErrUserNotFound
	}
	if err != nil {
		return nil, err
	}
	return &u, nil
}
```

### Service layer

```go
u, err := repo.GetByID(ctx, id)
if err != nil {
	if errors.Is(err, ErrUserNotFound) {
		return nil // or map to 404
	}
	return err
}
```

✅ Explicit
✅ No GORM leakage
✅ Easy HTTP mapping (404)

---

## Level 3 — Result / Option type (maximum purity)

### Option type

```go
type Option[T any] struct {
	val *T
}

func Some[T any](v T) Option[T] { return Option[T]{&v} }
func None[T any]() Option[T]    { return Option[T]{nil} }

func (o Option[T]) IsSome() bool { return o.val != nil }
func (o Option[T]) Unwrap() T    { return *o.val }
```

### Repository interface

```go
type UserRepository interface {
	FindByID(ctx context.Context, id int64) (Option[User], error)
}
```

### GORM implementation

```go
func (r *userRepoGorm) FindByID(ctx context.Context, id int64) (Option[User], error) {
	var u User
	err := r.db.WithContext(ctx).First(&u, id).Error

	if errors.Is(err, gorm.ErrRecordNotFound) {
		return None[User](), nil
	}
	if err != nil {
		return None[User](), err
	}
	return Some(u), nil
}
```

### Service usage

```go
res, err := repo.FindByID(ctx, id)
if err != nil {
	return err
}
if !res.IsSome() {
	return ErrUserNotFound
}
user := res.Unwrap()
```

✅ No nils
✅ No sentinel errors
⚠️ More code / abstraction

---

## What NOT to expose from repository

🚫 Do **not** expose:

```go
*gorm.DB
gorm.ErrRecordNotFound
RowsAffected
gorm.Model
```

Repository **translates persistence semantics → domain semantics**.

---

## Mapping to HTTP (clean)

```go
if errors.Is(err, ErrUserNotFound) {
	c.JSON(404, gin.H{"error": "user not found"})
	return
}
```

---

## Rule of thumb

| Layer      | Responsibility       |
| ---------- | -------------------- |
| GORM       | SQL & persistence    |
| Repository | Translate DB results |
| Service    | Business rules       |
| Handler    | Protocol (HTTP/GRPC) |

> **“No ORM types cross the repository boundary.”**

---

## Recommendation for your style

Given your recent work on:

* typed registries
* sentinel errors
* strong layering

👉 **Use Level 2**
It’s explicit, testable, and doesn’t over-abstract.

If you want, I can:

* Add **transaction-aware repositories**
* Show **batch query patterns** (no N+1)
* Integrate with **Gin error middleware**
* Compare this with **sqlc-generated repos**

Just tell me which one.
