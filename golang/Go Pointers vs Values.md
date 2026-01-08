# golang when to use pointer, when to use value semantics?

This is a **core Go design question**, and Go is opinionated but subtle here. I’ll give you **practical rules**, **why they exist**, and **how this plays out in real Go systems** (APIs, structs, slices, concurrency).

---

## The mental model (important)

In Go:

> **Value semantics = ownership + copy**
>
> **Pointer semantics = shared identity + mutation**

Ask yourself:

* Do I want **a copy** or **the same thing**?
* Do I want to **mutate** or **observe**?
* Is this value **small and immutable** or **large / stateful**?

---

## 1️⃣ When to use **value semantics**

### ✅ Use values when:

* The type is **small**
* The value is **immutable or treated as immutable**
* Copying is **cheap and safe**
* You want **clear ownership**
* The type represents a **conceptual value**, not an entity

### Typical examples

```go
int, float64, bool
time.Time
string
structs with few fields
```

### Example: request / DTO / config

```go
type UserInput struct {
    Email string
    Age   int
}

func Validate(in UserInput) error {
    if in.Age < 0 {
        return errors.New("invalid age")
    }
    return nil
}
```

Why value?

* No mutation intended
* Copy is cheap
* Safer API (no unexpected changes)

---

### Example: method receivers (value)

```go
func (u User) IsAdult() bool {
    return u.Age >= 18
}
```

This communicates:

> “Calling this will NOT change the user.”

---

## 2️⃣ When to use **pointer semantics**

### ✅ Use pointers when:

* You need to **modify** the value
* Copying is **expensive**
* The type has **identity**
* `nil` is a meaningful state
* The type holds **internal mutable state**
* The type uses **mutexes or sync primitives**

---

### Example: mutation

```go
func (u *User) SetEmail(email string) {
    u.Email = email
}
```

Pointer clearly signals:

> “This method mutates the receiver.”

---

### Example: large structs

```go
type BigStruct struct {
    A [1024]byte
    B [1024]byte
}
```

Avoid copying:

```go
func Process(b *BigStruct) {}
```

---

### Example: entity with identity

```go
type Account struct {
    ID      string
    Balance int64
}

func (a *Account) Credit(amount int64) {
    a.Balance += amount
}
```

Accounts are **entities**, not values.

---

## 3️⃣ Special case: **slices, maps, channels**

These already have **reference semantics**.

### ❌ You almost never need pointers to them

```go
func f(s []int) {}        // good
func f(s *[]int) {}      // usually wrong
```

Why?

* Slice header is copied
* Underlying array is shared

### When pointer to slice makes sense

Only if you need to **replace the slice itself**:

```go
func Append(s *[]int, v int) {
    *s = append(*s, v)
}
```

---

## 4️⃣ Returning pointers vs values

### Prefer **returning values**

```go
func NewUser(name string) User {
    return User{Name: name}
}
```

Why?

* Escape analysis will decide stack vs heap
* API is simpler
* Caller controls ownership

---

### Return pointer when:

* The type is large
* You expect mutation
* `nil` matters
* It represents a shared entity

```go
func LoadAccount(id string) (*Account, error) {
    if notFound {
        return nil, ErrNotFound
    }
    return &Account{ID: id}, nil
}
```

---

## 5️⃣ Pointer vs value in method sets (important!)

### Value receiver

```go
func (u User) Name() string
```

* Works on both `User` and `*User`

### Pointer receiver

```go
func (u *User) SetName(string)
```

* Only on `*User`

### **Rule of thumb**

> If **any method** needs a pointer receiver,
> **all methods should use pointer receivers**.

This avoids confusing method sets.

---

## 6️⃣ Interfaces & pointers (common pitfall)

Interfaces care about **method sets**, not values.

```go
type Saver interface {
    Save() error
}

func (u *User) Save() error { return nil }

var s Saver = &User{} // OK
var s Saver = User{}  // ❌ does not compile
```

If a type implements an interface with pointer receivers:

* You must use `*T`, not `T`

---

## 7️⃣ Concurrency rule (very important)

### Never copy values containing:

* `sync.Mutex`
* `sync.Once`
* `atomic.*`
* channels used as state

```go
type Cache struct {
    mu sync.Mutex
    m  map[string]string
}
```

Must use pointer:

```go
func NewCache() *Cache { ... }
```

---

## 8️⃣ Practical decision table

| Question                      | Use     |
| ----------------------------- | ------- |
| Is it small & immutable?      | value   |
| Is mutation required?         | pointer |
| Does it have identity?        | pointer |
| Is copying expensive?         | pointer |
| Is `nil` meaningful?          | pointer |
| Is it a DTO / input / output? | value   |
| Does it contain mutexes?      | pointer |
| Slice / map / chan?           | value   |

---

## 9️⃣ Go proverb (this one matters)

> **“Don’t communicate by sharing memory; share memory by communicating.”**

Prefer:

* Values in APIs
* Pointers for internal mutation
* Channels for concurrency

---

## 10️⃣ What senior Go code usually looks like

* **Public APIs** → value-oriented
* **Internal state** → pointer-oriented
* **Business entities** → pointers
* **Requests / responses** → values

---
