# Introduce com.lmax.disruptor.Sequence

In the **LMAX Disruptor**, the class **com.lmax.disruptor.Sequence** is one of the **core building blocks** used to coordinate producers and consumers in a lock-free ring buffer.

Below is a clear breakdown.

---

# 1. What `Sequence` Is

`Sequence` is a **thread-safe long value** representing a **position in the ring buffer**.

Think of it as a **monotonically increasing cursor**.

Typical sequences:

| Component  | Sequence Meaning        |
| ---------- | ----------------------- |
| Producer   | Last published event    |
| Consumer   | Last consumed event     |
| RingBuffer | Highest available event |

Example:

```
RingBuffer size = 1024

Producer publishes events
Sequence increases:

0 → 1 → 2 → 3 → ...
```

Consumers track their own sequence to know:

```
Which event should I process next?
```

---

# 2. Why Disruptor Uses `Sequence`

In high-performance systems (like trading), locks are avoided.

Instead of locks:

* threads communicate using **sequence numbers**
* memory barriers guarantee visibility
* CAS ensures atomic updates

`Sequence` provides:

```
atomic long
+ padding
+ memory ordering
```

So it avoids:

```
false sharing
locks
cache line contention
```

---

# 3. Internal Structure

Simplified version:

```java
public class Sequence extends RhsPadding {

    volatile long value;

    public Sequence(long initialValue) {
        this.value = initialValue;
    }

    public long get() {
        return value;
    }

    public void set(long value) {
        this.value = value;
    }

    public boolean compareAndSet(long expectedValue, long newValue) {
        return UNSAFE.compareAndSwapLong(this, VALUE_OFFSET,
                                         expectedValue, newValue);
    }
}
```

Key properties:

| Feature    | Purpose                   |
| ---------- | ------------------------- |
| `volatile` | visibility across threads |
| CAS        | lock-free updates         |
| padding    | avoid false sharing       |

---

# 4. Why Padding Is Critical

`Sequence` extends padding classes:

```
LhsPadding
Value
RhsPadding
```

Goal:

```
| cache line |
| padding    |
| value      |
| padding    |
```

Without padding:

```
Producer thread modifies sequence
Consumer thread modifies another variable

→ same cache line
→ cache ping-pong
→ massive latency
```

Padding ensures **one sequence = one cache line**.

This is critical in **low latency systems**.

---

# 5. How `Sequence` Is Used in the Disruptor

Typical flow:

### Producer

```
next = sequencer.next()

ringBuffer[next] = event

sequencer.publish(next)
```

Producer sequence increases.

---

### Consumer

Consumer tracks its own `Sequence`.

```
available = sequencer.getCursor()

while (sequence <= available)
    process(event)
    sequence++
```

Consumer updates its `Sequence` when finished.

---

# 6. Gating Sequences

Consumers register their sequence as **gating sequences**.

Purpose:

Prevent producer overwriting unconsumed data.

Example:

```
RingBuffer size = 1024

Producer cursor = 2000
Slowest consumer = 1000

Producer cannot wrap past:

1000 + 1024
```

So `Sequence` protects against:

```
data overwrite
consumer lag
```

---

# 7. Why `Sequence` Is Faster Than `AtomicLong`

`Sequence` is optimized for **CPU cache behavior**.

Comparison:

| Feature                  | AtomicLong | Sequence |
| ------------------------ | ---------- | -------- |
| CAS                      | yes        | yes      |
| padding                  | no         | yes      |
| false sharing protection | no         | yes      |
| low latency tuning       | no         | yes      |

In high-throughput systems this matters a lot.

Typical improvement:

```
AtomicLong contention → 10–40ns
Sequence padded → 3–10ns
```

---

# 8. Typical Initial Value

Initial sequence is:

```
-1
```

Meaning:

```
no event published yet
```

After first event:

```
0
```

---

# 9. Real Example

Producer:

```java
long seq = ringBuffer.next();

try {
    Event e = ringBuffer.get(seq);
    e.setValue(data);
} finally {
    ringBuffer.publish(seq);
}
```

Consumer:

```java
public void onEvent(Event e, long sequence, boolean endOfBatch)
{
    process(e);
}
```

Sequence tells:

```
which event index
```

---

# 10. Mental Model (Important)

Think of `Sequence` as:

```
a lock-free progress marker
```

Diagram:

```
Producer Cursor
        │
        ▼
   0 1 2 3 4 5 6 7
  [ ][ ][ ][ ][ ][ ][ ][ ]
        ▲
        │
   Consumer Sequence
```

---

# 11. Why HFT Systems Love Disruptor

The **LMAX Exchange** designed Disruptor for:

```
6M+ messages/sec
sub-microsecond latency
```

`Sequence` is the primitive that enables:

```
lock-free coordination
predictable latency
no GC pressure
```

---

✅ **In one sentence**

`Sequence` is a **cache-line-padded atomic counter used by Disruptor to track producer and consumer positions in the ring buffer without locks.**

---

If you'd like, I can also show **5 internal tricks in Disruptor's `Sequence` that most engineers miss (VarHandle, ordered writes, memory barriers, etc.)** — these are extremely relevant for **HFT / low latency engineers**.



# Seems like com.lmax.disruptor.Sequence is a padding wrapper of "volatile long" ?

Yes — that’s **essentially correct**, but there are a few subtle details that make **com.lmax.disruptor.Sequence** more than just a padded `volatile long`.

Short answer:

> `Sequence` is a **cache-line padded wrapper around a `volatile long` that provides atomic and ordered updates optimized for low-latency concurrency.**

Let’s break it down.

---

# 1. The Core Value Really Is a `volatile long`

At the heart of the class:

```java
protected volatile long value;
```

This value represents the **current position in the ring buffer** used by the **LMAX Disruptor**.

Example values:

```
Producer cursor sequence
Consumer progress sequence
Gating sequence
```

The `volatile` ensures:

```
visibility between threads
```

Meaning:

```
Producer writes → consumer sees it immediately
```

---

# 2. Padding Is the Key Reason the Class Exists

The real motivation is **false sharing avoidance**.

Modern CPUs use **64-byte cache lines**.

If two hot variables share the same cache line:

```
core A writes
core B writes
```

The cache line constantly **bounces between cores**.

This is called:

```
cache line ping-pong
```

Which can add **100ns+ latency** in worst cases.

So `Sequence` adds padding.

Simplified layout:

```
| padding | value | padding |
```

Typical implementation pattern (simplified):

```java
class LhsPadding {
    long p1,p2,p3,p4,p5,p6,p7;
}

class Value extends LhsPadding {
    volatile long value;
}

class RhsPadding extends Value {
    long p9,p10,p11,p12,p13,p14,p15;
}
```

Total ≈ **128 bytes**, guaranteeing the value occupies its own cache line.

---

# 3. Why Not Just Use `AtomicLong`?

Because **`AtomicLong` is not padded**.

Example memory layout:

```
AtomicLong
| value | other fields |
```

Multiple `AtomicLong` objects may share cache lines.

In high-frequency systems this causes heavy contention.

`Sequence` avoids this entirely.

---

# 4. It Also Provides CAS and Ordered Writes

`Sequence` provides methods like:

```java
get()
set()
setVolatile()
compareAndSet()
incrementAndGet()
addAndGet()
```

Under the hood they use:

```
Unsafe.compareAndSwapLong
or VarHandle
```

Example:

```java
public boolean compareAndSet(long expected, long newValue) {
    return UNSAFE.compareAndSwapLong(this, VALUE_OFFSET, expected, newValue);
}
```

This allows **lock-free updates**.

---

# 5. Ordered Writes (Important for Disruptor)

Disruptor uses **lazySet / ordered writes** for performance.

Example:

```java
setOrdered(long value)
```

This uses a **store-store barrier** instead of full volatile semantics.

Meaning:

```
faster write
still correctly ordered
```

Very important for:

```
publish → consumer visibility
```

---

# 6. Why This Matters in Disruptor

In a **ring buffer pipeline**:

```
Producer sequence
Consumer sequence
Worker sequence
Gating sequence
```

All of them are `Sequence`.

And they are **written extremely frequently**.

Example throughput target:

```
10M+ updates per second
```

Without padding:

```
cache contention → latency spikes
```

---

# 7. Mental Model

You can think of `Sequence` as:

```
class Sequence {
    padded volatile long value
    + CAS operations
    + ordered writes
}
```

or in one line:

> **A cache-line-isolated atomic counter optimized for inter-thread progress tracking.**

---

# 8. Why This Tiny Class Is So Important

In **LMAX Disruptor**, nearly every critical coordination uses `Sequence`.

Examples:

```
RingBuffer cursor
Consumer progress
Barrier gating
Producer claim
```

So the class is tiny, but it is on the **hottest path in the entire library**.

---

✅ **Conclusion**

Yes — conceptually:

```
Sequence ≈ padded volatile long + CAS utilities
```

But the padding and ordered memory semantics are what make it **extremely fast for low-latency messaging systems**.

---

If you're interested, I can also show **the exact memory layout of Sequence on a 64-byte cache CPU and why the Disruptor team chose 7 padding longs instead of 8** — a very clever trick used in many **HFT Java systems**.
