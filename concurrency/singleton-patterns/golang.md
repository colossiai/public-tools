# How about Double-Check Locking in go?



**Short answer:**
👉 **Don’t use Double-Checked Locking in Go.**
Go already provides **simpler, safer, faster primitives** that make DCL unnecessary and unidiomatic.

Below I’ll still show what DCL *would* look like, **why it’s risky**, and **what you should use instead**.

---

## Why Double-Checked Locking is the wrong tool in Go

Double-Checked Locking exists to:

* Avoid locking after initialization
* Work around expensive synchronization
* Rely on memory-model subtleties (`volatile`, atomics)

**Go was explicitly designed to avoid this.**

Go provides:

* `sync.Once`
* Package-level initialization
* Clear memory visibility guarantees

---

## ❌ Naive DCL in Go (broken / racy)

```go
var (
    instance *Singleton
    mu       sync.Mutex
)

func GetInstance() *Singleton {
    if instance == nil {          // ❌ data race
        mu.Lock()
        defer mu.Unlock()
        if instance == nil {
            instance = &Singleton{}
        }
    }
    return instance
}
```

### What’s wrong?

* `instance` is read without synchronization
* Data race → **undefined behavior**
* Go race detector will flag this immediately

---

## ⚠️ “Fixed” DCL using atomics (still discouraged)

```go
import (
    "sync"
    "sync/atomic"
    "unsafe"
)

var (
    instance unsafe.Pointer
    mu       sync.Mutex
)

func GetInstance() *Singleton {
    p := atomic.LoadPointer(&instance)
    if p == nil {
        mu.Lock()
        defer mu.Unlock()

        p = atomic.LoadPointer(&instance)
        if p == nil {
            s := &Singleton{}
            atomic.StorePointer(&instance, unsafe.Pointer(s))
            return s
        }
    }
    return (*Singleton)(p)
}
```

### Why this is still bad

* Uses `unsafe`
* Easy to get wrong
* Hard to read and maintain
* No real benefit vs `sync.Once`

This is **technically correct** under Go’s memory model—but **no Go engineer will accept this in review**.

---

## ✅ Correct and idiomatic Go solution: `sync.Once`

```go
var (
    instance *Singleton
    once     sync.Once
)

func GetInstance() *Singleton {
    once.Do(func() {
        instance = &Singleton{}
    })
    return instance
}
```

### Why this is better

* Lazy
* Thread-safe
* Zero data races
* Very fast (lock-free after first call)
* Designed specifically for this use case

---

## How `sync.Once` compares to DCL

| Feature       | DCL             | sync.Once |
| ------------- | --------------- | --------- |
| Lazy          | ✅               | ✅         |
| Thread-safe   | ⚠️ tricky       | ✅         |
| Readability   | ❌               | ✅         |
| Memory safety | ❌ easy to break | ✅         |
| Idiomatic Go  | ❌               | ✅         |

Internally, `sync.Once` already uses:

* Atomics
* Fast path / slow path
* Memory barriers

**You get DCL-level performance without DCL-level bugs.**

---

## Even simpler: package initialization (often best)

```go
var Instance = &Singleton{}
```

Go guarantees:

* Package init runs once
* Thread-safe
* No races

Use this if laziness is **not required**.

---

## Mapping to other languages

| Language   | Best practice    |
| ---------- | ---------------- |
| Java       | Holder / enum    |
| C++        | Meyers singleton |
| Go         | `sync.Once`      |
| Go (eager) | Package init     |

---

## One-sentence takeaway

> **Double-Checked Locking is unnecessary and unidiomatic in Go—`sync.Once` already provides a safe, fast, and simpler solution.**

If you want, I can:

* Show `sync.Once` internals
* Compare Go memory model vs Java/C++
* Explain why Go forbids data races by design
* Show how race detector catches DCL immediately
