# show how the producer side (RingBuffer.next() + publish()) works internally (SINGLE)

**sequencer.next()** is like waitAndClaimNextSlot()


In LMAX Disruptor, the **producer side** is implemented in `RingBuffer`, but the real logic lives in **`Sequencer`** implementations:

* `SingleProducerSequencer`
* `MultiProducerSequencer`

The **two key producer operations** are:

```java
long seq = ringBuffer.next();   // claim slot
ringBuffer.publish(seq);        // make event visible
```

Below is the **actual internal mechanism**.

---

# 1. RingBuffer producer API

Simplified from source:

```java
public long next()
{
    return sequencer.next();
}

public void publish(long sequence)
{
    sequencer.publish(sequence);
}
```

So everything happens inside the **Sequencer**.

---

# 2. SingleProducerSequencer.next()

Used when **only one producer thread exists** (fastest mode).

### Core source (simplified but structurally identical)

```java
@Override
public long next()
{
    long nextSequence = nextValue + 1;
    long wrapPoint = nextSequence - bufferSize;
    long cachedGatingSequence = cachedValue;

    if (wrapPoint > cachedGatingSequence || cachedGatingSequence > nextValue)
    {
        long minSequence;

        while (wrapPoint > (minSequence = Util.getMinimumSequence(gatingSequences)))
        {
            LockSupport.parkNanos(1L);
        }

        cachedValue = minSequence;
    }

    nextValue = nextSequence;

    return nextSequence;
}
```

---

# 3. What the producer is checking

The **ring buffer cannot overwrite unconsumed events**.

Condition checked:

```text
(nextSequence - bufferSize) > minConsumerSequence
```

If true:

```
BUFFER FULL
```

Producer must wait.

---

# 4. Visualization

Example:

```
bufferSize = 8
```

Current state:

```
producer nextValue = 15
consumer min = 10
```

Buffer contains:

```
10 11 12 13 14 15
```

Producer tries:

```
nextSequence = 16
wrapPoint = 16 - 8 = 8
```

Check:

```
8 > 10 ?  false
```

Safe to proceed.

---

# 5. Slot index calculation

RingBuffer uses **power-of-two masking**.

Index calculation:

```java
index = sequence & (bufferSize - 1);
```

Example:

```
bufferSize = 1024
sequence = 2050
```

Index:

```
2050 & 1023 = 2
```

This avoids `%` division.

---

# 6. Writing the event

Typical producer code:

```java
long seq = ringBuffer.next();

try
{
    Event e = ringBuffer.get(seq);
    e.value = data;
}
finally
{
    ringBuffer.publish(seq);
}
```

Important:

```
event write happens BEFORE publish
```

---

# 7. publish()

From `SingleProducerSequencer`:

```java
@Override
public void publish(long sequence)
{
    cursor.set(sequence);
    waitStrategy.signalAllWhenBlocking();
}
```

Two things happen:

1️⃣ publish visibility

```
cursor = sequence
```

2️⃣ wake blocked consumers

```
Condition.signalAll()
```

(if using blocking strategy)

---

# 8. Why this is safe (memory ordering)

`cursor.set(sequence)` uses a **volatile write**.

In the Java Memory Model:

```
WRITE event fields
WRITE cursor (volatile)
```

Guarantees:

```
consumer reading cursor
→ sees event data
```

Equivalent to:

```
store-store barrier
store-load barrier
```

---

# 9. Consumer side visibility

Consumer checks:

```java
cursorSequence.get()
```

Once it observes:

```
cursor >= requestedSequence
```

Event is guaranteed visible.

---

# 10. MultiProducerSequencer (more complex)

When multiple producers exist, CAS is required.

Core claim logic:

```java
do
{
    current = cursor.get();
    next = current + n;

    wrapPoint = next - bufferSize;
    gatingSequence = minConsumerSequence;

    if (wrapPoint > gatingSequence)
        spin;
}
while (!cursor.compareAndSet(current, next));
```

So multi-producer requires:

```
CAS loop
```

while single producer does **not**.

---

# 11. Full producer timeline

Example:

```
Producer thread
```

Step 1 — claim

```
seq = next()
```

Step 2 — write

```
ringBuffer[seq] = event
```

Step 3 — publish

```
cursor = seq
```

Step 4 — consumer sees

```
cursor >= seq
```

Step 5 — consumer processes event

---

# 12. Key insight: zero allocation

Unlike queues:

```
ArrayBlockingQueue
LinkedBlockingQueue
```

Disruptor does **not allocate per message**.

All objects are pre-created.

Memory layout:

```
RingBuffer
 ├── Event[0]
 ├── Event[1]
 ├── Event[2]
 ...
```

This avoids:

```
GC
pointer chasing
cache misses
```

---

# 13. Entire producer hot path (compressed)

The full algorithm is basically:

```java
seq = next();

buffer[seq & mask] = event;

cursor = seq;
```

Three operations.

This is why Disruptor can reach:

```
50M – 100M ops/sec
```

on modern CPUs.

---

✅ If you'd like, I can also show something **very interesting for low-latency engineers**:

**The exact CPU assembly instructions produced by the JIT for `cursor.set()` and `cursor.get()`**, and why they map to **`lock addl`, `mov`, and memory fences** on x86. That part connects directly to your earlier question about `lock addl`.
