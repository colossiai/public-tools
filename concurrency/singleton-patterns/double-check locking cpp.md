# Show Double-Checked Locking in C++.


Below is **Double-Checked Locking (DCL) in modern C++**, explained carefully—because **naive C++ DCL is broken unless done correctly**.

---

## ❌ Broken (classic) C++ double-checked locking

```cpp
class Singleton {
public:
    static Singleton* instance() {
        if (instance_ == nullptr) {            // 1st check
            std::lock_guard<std::mutex> lock(m_);
            if (instance_ == nullptr) {        // 2nd check
                instance_ = new Singleton();   // ❌ data race / reordering
            }
        }
        return instance_;
    }

private:
    Singleton() = default;

    static Singleton* instance_;
    static std::mutex m_;
};
```

### Why this is broken

* `instance_` is a **plain pointer**
* Writes can be **reordered**
* Another thread may observe a **partially constructed object**
* This is **undefined behavior** in C++

This is exactly the same problem Java had *before `volatile`*.

---

## ✅ Correct Double-Checked Locking in C++11+

C++ requires **`std::atomic` + acquire/release semantics**.

```cpp
#include <atomic>
#include <mutex>

class Singleton {
public:
    static Singleton* instance() {
        Singleton* tmp = instance_.load(std::memory_order_acquire);
        if (tmp == nullptr) {                          // 1st check (no lock)
            std::lock_guard<std::mutex> lock(m_);
            tmp = instance_.load(std::memory_order_relaxed);
            if (tmp == nullptr) {                      // 2nd check (with lock)
                tmp = new Singleton();
                instance_.store(tmp, std::memory_order_release);
            }
        }
        return tmp;
    }

private:
    Singleton() = default;

    static std::atomic<Singleton*> instance_;
    static std::mutex m_;
};

// static definitions
std::atomic<Singleton*> Singleton::instance_{nullptr};
std::mutex Singleton::m_;
```

---

## Why this version is correct

### 1️⃣ `std::atomic<Singleton*>`

Prevents data races on the pointer.

---

### 2️⃣ `memory_order_release` on store

Ensures:

* Object is **fully constructed**
* All writes are visible **before** pointer is published

---

### 3️⃣ `memory_order_acquire` on load

Ensures:

* If pointer is non-null
* The object is **fully initialized**

This matches Java’s `volatile` semantics exactly.

---

## Execution flow (thread-safe)

```text
Thread A:
  new Singleton()
  release-store(instance)

Thread B:
  acquire-load(instance)
  sees fully constructed object
```

---

## Performance characteristics

| Phase                 | Cost                |
| --------------------- | ------------------- |
| Before initialization | atomic load + mutex |
| After initialization  | atomic load only    |
| Contention            | minimal             |

---

## ⚠️ Important: memory leak & lifetime

This pattern:

* Leaks the singleton (never deleted)
* This is **usually intentional** for process-lifetime singletons

If destruction is required → complexity increases significantly.

---

## ✅ Recommended C++ alternative (DON’T use DCL)

### Meyers Singleton (BEST)

```cpp
class Singleton {
public:
    static Singleton& instance() {
        static Singleton instance; // thread-safe since C++11
        return instance;
    }

private:
    Singleton() = default;
};
```

### Why this is better

* Lazy
* Thread-safe
* Zero atomics
* Zero mutexes
* Correct destruction at program exit
* Guaranteed by the standard

---

## Comparison

| Pattern              | Correct | Lazy | Simple | Recommended |
| -------------------- | ------- | ---- | ------ | ----------- |
| Naive DCL            | ❌       | ✅    | ❌      | ❌           |
| Atomic DCL           | ✅       | ✅    | ❌      | ⚠️ Rare     |
| **Meyers Singleton** | ✅       | ✅    | ✅      | ✅           |

---

## One-sentence takeaway

> **Double-Checked Locking in C++ is only correct when using `std::atomic` with acquire-release semantics, but in practice it should be avoided in favor of function-local static initialization.**

If you want next:

* Compare **C++ vs Java memory models**
* Show **why DCL fails without atomics**
* Discuss **static initialization order fiasco**
* Show a **lock-free singleton (why it’s a bad idea)**


# Meyers Singleton is like Java's Holder pattern?

**Short answer:**
👉 **Yes — conceptually they are the same idea.**
**Long answer:** They are *equivalent in spirit* but implemented via **different language mechanisms**.

---

## The core idea they share

Both **Meyers Singleton (C++)** and **Java’s Holder pattern** rely on:

> **Lazy, thread-safe initialization guaranteed by the language runtime, not by explicit locks.**

Neither uses:

* `synchronized` / `mutex`
* `volatile` / `atomic`
* double-checked locking

They both let the **runtime** do the hard work.

---

## Side-by-side comparison

### C++: Meyers Singleton

```cpp
class Singleton {
public:
    static Singleton& instance() {
        static Singleton instance; // initialized on first call
        return instance;
    }

private:
    Singleton() = default;
};
```

### Java: Holder Pattern

```java
class Singleton {
    private Singleton() {}

    private static class Holder {
        static final Singleton INSTANCE = new Singleton();
    }

    public static Singleton getInstance() {
        return Holder.INSTANCE;
    }
}
```

---

## Why they are conceptually the same

| Aspect                 | Meyers (C++)               | Holder (Java)               |
| ---------------------- | -------------------------- | --------------------------- |
| Lazy                   | Yes                        | Yes                         |
| Thread-safe            | Yes                        | Yes                         |
| Who guarantees safety  | C++ runtime                | JVM                         |
| When object is created | First call to `instance()` | First reference to `Holder` |
| Locks/atomics          | None                       | None                        |

**Key similarity**:

> The object is initialized *exactly once* at first use, and all threads see a fully constructed instance.

---

## What mechanism makes them safe?

### 🔹 C++ (since C++11)

* Function-local `static` initialization is:

  * **Lazy**
  * **Thread-safe**
  * **Sequenced-before all uses**

(Standard guarantee: §6.7 [stmt.dcl])

---

### 🔹 Java

* Class initialization is:

  * **Lazy**
  * **Synchronized**
  * Has a **happens-before guarantee**

(JLS §12.4)

---

## Key difference (important nuance)

### 1️⃣ Initialization unit

| Language | Unit                           |
| -------- | ------------------------------ |
| C++      | Function-local static variable |
| Java     | Nested class                   |

Java **cannot** do this safely with a method-local static variable (doesn’t exist), so it uses a **class-loading trick**.

---

### 2️⃣ Destruction / lifetime

| Aspect       | C++ Meyers                     | Java Holder               |
| ------------ | ------------------------------ | ------------------------- |
| Destruction  | Automatic at program exit      | Typically never destroyed |
| Order issues | Possible (static deinit order) | Not applicable            |
| Control      | Limited                        | Managed by GC             |

---

### 3️⃣ Serialization & reflection

| Issue             | Java Holder                       | C++ Meyers     |
| ----------------- | --------------------------------- | -------------- |
| Reflection attack | Possible (unless guarded)         | Not applicable |
| Serialization     | Can break without `readResolve()` | N/A            |

(Java enums handle these better.)

---

## Mental model (use this in interviews)

> **Meyers Singleton is the C++ equivalent of Java’s Holder pattern: both rely on lazy, runtime-guaranteed initialization instead of explicit synchronization.**

---

## When to prefer something else

### Java

* Prefer **`enum` singleton** if possible
* Use Holder when:

  * Lazy
  * Non-enum API
  * Framework compatibility

### C++

* Prefer **Meyers Singleton**
* Avoid DCL unless you have a *very specific* reason

---

## Final takeaway

✔ Same **pattern philosophy**
✔ Same **performance profile**
✔ Different **language-level mechanisms**

If you want, I can:

* Map **Java volatile ↔ C++ atomic**
* Explain **why Java cannot do Meyers directly**
* Show **why enum has no C++ equivalent**
* Discuss **shutdown/destruction pitfalls**
