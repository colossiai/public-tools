# show how the producer side (RingBuffer.next() + publish()) works internally (MULTI)


In LMAX Disruptor the producer side revolves around **`RingBuffer.next()` → write event → `publish()`**.
The logic is implemented mostly in **`MultiProducerSequencer`** or **`SingleProducerSequencer`**, depending on configuration.

I'll show the **core internal source patterns** for the most common case: **`MultiProducerSequencer`**.

---

# 1️⃣ Producer workflow (user code)

Typical producer code:

```java
long seq = ringBuffer.next();

try {
    Event e = ringBuffer.get(seq);
    e.value = 42;
}
finally {
    ringBuffer.publish(seq);
}
```

Execution path:

```
RingBuffer.next()
   ↓
Sequencer.next()
   ↓
claim slot in ring buffer

write event

RingBuffer.publish()
   ↓
Sequencer.publish()
   ↓
make event visible to consumers
```

---

# 2️⃣ `RingBuffer.next()` (delegates to sequencer)

Simplified source:

```java
public long next()
{
    return sequencer.next();
}
```

All real logic lives inside the **Sequencer**.

---

# 3️⃣ Core source: `MultiProducerSequencer.next()`

This is the **slot reservation algorithm**.

```java
@Override
public long next()
{
    return next(1);
}
```

The real logic:

```java
@Override
public long next(int n)
{
    long current;
    long next;

    do
    {
        current = cursor.get();
        next = current + n;

        long wrapPoint = next - bufferSize;
        long cachedGatingSequence = gatingSequenceCache.get();

        if (wrapPoint > cachedGatingSequence || cachedGatingSequence > current)
        {
            long minSequence = Util.getMinimumSequence(gatingSequences, current);
            gatingSequenceCache.set(minSequence);

            if (wrapPoint > minSequence)
            {
                LockSupport.parkNanos(1L);
                continue;
            }
        }
    }
    while (!cursor.compareAndSet(current, next));

    return next;
}
```

---

# 4️⃣ What the code does

### Step 1 — read current cursor

```java
current = cursor.get();
```

Example:

```
cursor = 100
```

---

### Step 2 — compute next sequence

```java
next = current + n;
```

Example:

```
next = 101
```

---

### Step 3 — detect ring buffer wrap

```java
wrapPoint = next - bufferSize
```

Example:

```
bufferSize = 1024
next = 1050

wrapPoint = 26
```

Meaning producer would overwrite slot **26**.

---

### Step 4 — check consumer progress

```java
minSequence = Util.getMinimumSequence(gatingSequences)
```

Example:

```
consumer1 = 80
consumer2 = 75

min = 75
```

Producer must **not overwrite** until:

```
min > wrapPoint
```

---

### Step 5 — reserve slot via CAS

```java
cursor.compareAndSet(current, next)
```

Example:

```
CAS(100 → 101)
```

If another producer wins:

```
CAS fails → retry loop
```

---

# 5️⃣ Writing event into ring buffer

After `next()` returns:

```java
Event e = ringBuffer.get(seq);
```

Implementation:

```java
public E get(long sequence)
{
    return entries[(int) sequence & indexMask];
}
```

Index calculation:

```
index = sequence & (bufferSize - 1)
```

This is a **bitmask instead of modulo**.

Example:

```
bufferSize = 1024
indexMask = 1023

index = seq & 1023
```

Extremely fast.

---

# 6️⃣ Publishing event

After writing the event:

```java
ringBuffer.publish(seq);
```

Source:

```java
public void publish(long sequence)
{
    sequencer.publish(sequence);
}
```

---

# 7️⃣ `MultiProducerSequencer.publish()`

```java
@Override
public void publish(final long sequence)
{
    setAvailable(sequence);
    waitStrategy.signalAllWhenBlocking();
}
```

---

# 8️⃣ Marking slot as available

This is how consumers detect **published slots**.

```java
private void setAvailable(final long sequence)
{
    int index = calculateIndex(sequence);
    int flag = calculateAvailabilityFlag(sequence);

    AVAILABLE_ARRAY.set(index, flag);
}
```

Where:

```
index = sequence & indexMask
flag = sequence >>> indexShift
```

This solves the **ring wrap problem**.

---

# 9️⃣ Consumer checks availability

Consumers call:

```java
sequencer.isAvailable(sequence)
```

Source:

```java
@Override
public boolean isAvailable(long sequence)
{
    int index = calculateIndex(sequence);
    int flag = calculateAvailabilityFlag(sequence);

    return AVAILABLE_ARRAY.get(index) == flag;
}
```

So if the ring wraps, the **flag changes**, preventing stale reads.

---

# 🔟 Why this design is brilliant

Key properties:

| Feature           | Benefit                 |
| ----------------- | ----------------------- |
| CAS cursor        | multiple producers safe |
| bitmask index     | no modulo cost          |
| availability flag | correct wrap detection  |
| gating sequences  | prevent overwrite       |
| no locks          | ultra low latency       |

---

# End-to-end producer timeline

Example:

```
bufferSize = 1024
cursor = 100
consumer min = 80
```

Producer calls:

```
next()
```

Result:

```
sequence = 101
```

Producer writes:

```
entries[101 & 1023]
```

Producer publishes:

```
availableBuffer[index] = flag
```

Consumers then see:

```
sequenceBarrier.waitFor()
```

returning the new sequence.

---

# Ultra-simplified producer algorithm

Core logic reduces to:

```
loop:
    current = cursor
    next = current + 1

    if next would overwrite slowest consumer
        wait

    CAS(cursor, current → next)
```

Then:

```
write event
mark slot available
```

---

💡 **Deep insight**

The Disruptor producer side achieves:

```
multi-producer lock-free slot reservation
+
wait-free event publication
```

using just:

```
CAS
volatile loads
array writes
```

No locks anywhere.

---

If you'd like, I can also show something **very few people notice in Disruptor**:

**Why `SingleProducerSequencer` is 2–3× faster than `MultiProducerSequencer`** and what trick it uses to completely eliminate CAS.
