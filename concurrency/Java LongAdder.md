# Java AtomicInteger vs LongAdder

Good question — both `AtomicInteger` and `LongAdder` are **atomic counter** classes in Java, but they behave quite differently under high contention. Let’s break it down clearly:

---

### 🔹 1. Basic Purpose

| Class           | Purpose                                                                                                                                        |
| --------------- | ---------------------------------------------------------------------------------------------------------------------------------------------- |
| `AtomicInteger` | Atomic integer operations with compare-and-swap (CAS). Suitable for **low to moderate contention**.                                            |
| `LongAdder`     | Designed for **highly concurrent** updates (e.g. counters in multi-threaded environments). Reduces contention internally by spreading updates. |

---

### 🔹 2. Implementation Difference

| Aspect              | `AtomicInteger`                                                   | `LongAdder`                                                                                                                                 |
| ------------------- | ----------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------- |
| Core Mechanism      | Single variable, all threads use CAS on the same memory location. | Internally maintains multiple “cells”, each cell is an independent counter updated by different threads. The total is the sum of all cells. |
| Contention Behavior | High contention → frequent CAS retries → performance drops.       | Low contention impact — threads update different cells → better throughput under load.                                                      |
| Memory Usage        | Very small (one int).                                             | Larger (an array of cells internally).                                                                                                      |

---

### 🔹 3. Usage Example

#### `AtomicInteger`

```java
AtomicInteger counter = new AtomicInteger();

counter.incrementAndGet();
counter.addAndGet(5);
int value = counter.get();
```

#### `LongAdder`

```java
LongAdder counter = new LongAdder();

counter.increment();
counter.add(5);
long sum = counter.sum(); // Must call sum() to get the total
```

---

### 🔹 4. Performance

| Scenario                                               | Recommended Class                                          |
| ------------------------------------------------------ | ---------------------------------------------------------- |
| Single-threaded                                        | `AtomicInteger` (simpler, less memory)                     |
| Low-contention (few threads)                           | `AtomicInteger`                                            |
| High-contention (many threads incrementing frequently) | ✅ `LongAdder`                                              |
| You need atomic operations like compareAndSet          | Only `AtomicInteger` supports this. (`LongAdder` doesn’t.) |

---

### 🔹 5. Example Benchmark (rough idea)

Under heavy multithreaded increments (e.g., 32+ threads):

| Class           | Relative Throughput |
| --------------- | ------------------- |
| `AtomicInteger` | ~1x (baseline)      |
| `LongAdder`     | ~5–10x faster       |

---

### 🔹 6. Summary

| Feature                        | `AtomicInteger`               | `LongAdder`                    |
| ------------------------------ | ----------------------------- | ------------------------------ |
| Thread-safety                  | ✅                             | ✅                              |
| Compare-and-swap (CAS) support | ✅                             | ❌                              |
| Best for                       | Counters under low contention | Counters under high contention |
| Method to get value            | `get()`                       | `sum()`                        |
| Memory footprint               | Smaller                       | Larger                         |

---

✅ **Rule of thumb:**

* Use **`AtomicInteger`** when atomic semantics (CAS, compareAndSet) are needed or few threads update the value.
* Use **`LongAdder`** for **high-frequency counters**, like metrics or request counting in servers.

---

Would you like me to show a **micro-benchmark example** comparing their throughput (using `JMH`)?
