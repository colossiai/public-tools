# #show disruptor SequenceBarrier concrete class source

In LMAX Disruptor, the **`SequenceBarrier`** is an interface. The main concrete implementation used internally is:

**`ProcessingSequenceBarrier`**

This class coordinates **consumer waiting logic** and ensures that a consumer only processes events after the required sequences are available.

---

# 1. `SequenceBarrier` interface

First, the interface (simplified):

```java
public interface SequenceBarrier
{
    long waitFor(long sequence) throws AlertException, InterruptedException, TimeoutException;

    long getCursor();

    boolean isAlerted();

    void alert();

    void clearAlert();

    void checkAlert() throws AlertException;
}
```

Key responsibilities:

| Method         | Purpose                             |
| -------------- | ----------------------------------- |
| `waitFor()`    | block/spin until sequence available |
| `getCursor()`  | producer cursor                     |
| `alert()`      | shutdown signal                     |
| `checkAlert()` | throw if barrier alerted            |

---

# 2. Concrete implementation: `ProcessingSequenceBarrier`

Below is the **core real source structure** from Disruptor (trimmed only for comments).

```java
final class ProcessingSequenceBarrier implements SequenceBarrier
{
    private final WaitStrategy waitStrategy;
    private final Sequence cursorSequence;
    private final Sequence dependentSequence;
    private volatile boolean alerted = false;

    ProcessingSequenceBarrier(
        final WaitStrategy waitStrategy,
        final Sequence cursorSequence,
        final Sequence[] dependentSequences)
    {
        this.waitStrategy = waitStrategy;
        this.cursorSequence = cursorSequence;

        if (dependentSequences.length == 0)
        {
            dependentSequence = cursorSequence;
        }
        else
        {
            dependentSequence = new FixedSequenceGroup(dependentSequences);
        }
    }

    @Override
    public long waitFor(final long sequence)
        throws AlertException, InterruptedException, TimeoutException
    {
        checkAlert();

        long availableSequence = waitStrategy.waitFor(
            sequence,
            cursorSequence,
            dependentSequence,
            this
        );

        if (availableSequence < sequence)
        {
            return availableSequence;
        }

        return availableSequence;
    }

    @Override
    public long getCursor()
    {
        return dependentSequence.get();
    }

    @Override
    public boolean isAlerted()
    {
        return alerted;
    }

    @Override
    public void alert()
    {
        alerted = true;
        waitStrategy.signalAllWhenBlocking();
    }

    @Override
    public void clearAlert()
    {
        alerted = false;
    }

    @Override
    public void checkAlert() throws AlertException
    {
        if (alerted)
        {
            throw AlertException.INSTANCE;
        }
    }
}
```

---

# 3. Important internal dependencies

### `Sequence`

A padded `volatile long` wrapper used to avoid false sharing.

```java
public class Sequence extends RhsPadding
{
    protected volatile long value;

    public long get() { return value; }

    public void set(long value) { this.value = value; }
}
```

---

### `WaitStrategy`

Controls **how waiting happens**.

Examples:

| Strategy               | Behavior                |
| ---------------------- | ----------------------- |
| `BusySpinWaitStrategy` | pure CPU spin           |
| `YieldingWaitStrategy` | spin + `Thread.yield()` |
| `BlockingWaitStrategy` | `Lock + Condition`      |
| `SleepingWaitStrategy` | spin + park             |

All the real waiting logic lives here.

Example method signature:

```java
long waitFor(
    long sequence,
    Sequence cursor,
    Sequence dependentSequence,
    SequenceBarrier barrier
)
```

---

# 4. Core waiting flow

Pipeline when consumer calls:

```
barrier.waitFor(100)
```

Flow:

```
BatchEventProcessor
      │
      ▼
SequenceBarrier.waitFor(100)
      │
      ▼
WaitStrategy.waitFor(...)
      │
      ├─ spin / yield / block
      │
      ▼
dependentSequence.get()
      │
      ▼
return available sequence
```

---

# 5. Key design trick

Notice this line:

```java
dependentSequence = new FixedSequenceGroup(dependentSequences);
```

This lets a barrier depend on **multiple consumers**.

Example pipeline:

```
Producer
   │
   ▼
Journal
   │
   ▼
Replication
   │
   ▼
BusinessLogic
```

`BusinessLogic` barrier depends on:

```
min(Journal.sequence, Replication.sequence)
```

That is computed by `FixedSequenceGroup`.

---

# 6. Why `SequenceBarrier` exists

Without it, consumer would need to manually coordinate:

```
while (producerCursor < nextSequence ||
       journalSequence < nextSequence ||
       replicationSequence < nextSequence)
{
    spin();
}
```

`SequenceBarrier` encapsulates this logic.

---

# 7. Real disruptor consumer loop

Inside `BatchEventProcessor`:

```java
while (true)
{
    long availableSequence = sequenceBarrier.waitFor(nextSequence);

    while (nextSequence <= availableSequence)
    {
        E event = ringBuffer.get(nextSequence);
        handler.onEvent(event);
        nextSequence++;
    }

    sequence.set(availableSequence);
}
```

---

✅ **Summary**

`ProcessingSequenceBarrier` responsibilities:

1. Manage **dependency sequences**
2. Delegate waiting to **WaitStrategy**
3. Handle **shutdown signaling**
4. Provide **memory visibility boundary**

---

If you'd like, I can also show **a full 150-line minimal Disruptor reimplementation** (RingBuffer + SequenceBarrier + WaitStrategy) so you can understand the whole mechanism in one page. It's a great way to truly internalize how Disruptor works.


# #show the source of the core waitFor dependentSeqs in this code `waitStrategy.waitFor( sequence, cursorSequence, dependentSequence, this );`

## especially for FixedSequenceGroup

The logic you’re asking about lives inside the **`WaitStrategy` implementations** in LMAX Disruptor.
Every strategy implements the same method:

```java
long waitFor(
    long sequence,
    Sequence cursor,
    Sequence dependentSequence,
    SequenceBarrier barrier
)
```

The **core check for dependent sequences** is always something like:

```java
availableSequence = dependentSequence.get();
```

This ensures the consumer does **not run ahead of upstream consumers**.

Below are the **real source patterns** from the main strategies.

---

# 1. `BlockingWaitStrategy.waitFor()` (simplified real source)

This is the easiest one to read.

```java
@Override
public long waitFor(
    long sequence,
    Sequence cursorSequence,
    Sequence dependentSequence,
    SequenceBarrier barrier)
    throws AlertException, InterruptedException
{
    long availableSequence;

    if (cursorSequence.get() < sequence)
    {
        lock.lock();
        try
        {
            while (cursorSequence.get() < sequence)
            {
                barrier.checkAlert();
                processorNotifyCondition.await();
            }
        }
        finally
        {
            lock.unlock();
        }
    }

    while ((availableSequence = dependentSequence.get()) < sequence)
    {
        barrier.checkAlert();
    }

    return availableSequence;
}
```

### Important parts

Producer wait:

```java
while (cursorSequence.get() < sequence)
```

Dependency wait:

```java
while ((availableSequence = dependentSequence.get()) < sequence)
```

So the consumer must wait for:

```
producer cursor >= requested sequence
AND
all dependent consumers >= requested sequence
```

---

# 2. `BusySpinWaitStrategy.waitFor()` (ultra low latency)

Used in **HFT / LMAX** setups.

```java
@Override
public long waitFor(
    long sequence,
    Sequence cursor,
    Sequence dependentSequence,
    SequenceBarrier barrier)
    throws AlertException
{
    long availableSequence;

    while ((availableSequence = dependentSequence.get()) < sequence)
    {
        barrier.checkAlert();
    }

    return availableSequence;
}
```

This is literally **pure CPU spinning**.

No locks.
No syscalls.
No parking.

Latency ~ **tens of nanoseconds**.

---

# 3. `YieldingWaitStrategy.waitFor()`

Spin first, then yield CPU.

```java
@Override
public long waitFor(
    long sequence,
    Sequence cursor,
    Sequence dependentSequence,
    SequenceBarrier barrier)
    throws AlertException
{
    long availableSequence;
    int counter = SPIN_TRIES;

    while ((availableSequence = dependentSequence.get()) < sequence)
    {
        barrier.checkAlert();

        if (counter == 0)
        {
            Thread.yield();
        }
        else
        {
            --counter;
        }
    }

    return availableSequence;
}
```

Used when CPU contention exists.

---

# 4. Where `dependentSequence` comes from

From `ProcessingSequenceBarrier` constructor:

```java
if (dependentSequences.length == 0)
{
    dependentSequence = cursorSequence;
}
else
{
    dependentSequence = new FixedSequenceGroup(dependentSequences);
}
```

---

# 5. `FixedSequenceGroup` source (important)

This computes the **minimum sequence across dependencies**.

```java
final class FixedSequenceGroup extends Sequence
{
    private final Sequence[] sequences;

    FixedSequenceGroup(Sequence[] sequences)
    {
        this.sequences = sequences;
    }

    @Override
    public long get()
    {
        long min = Long.MAX_VALUE;

        for (Sequence seq : sequences)
        {
            long value = seq.get();
            min = Math.min(min, value);
        }

        return min;
    }
}
```

So if dependencies are:

```
Journal = 100
Replication = 98
```

Then

```
dependentSequence.get() = 98
```

The next stage **must stop at 98**.

---

# 6. Visual pipeline

Example Disruptor graph:

```
Producer
   │
   ▼
RingBuffer cursor = 105
   │
   ▼
Journal (seq=102)
   │
   ▼
Replication (seq=98)
   │
   ▼
BusinessLogic (waiting)
```

BusinessLogic `waitFor(99)`:

```
cursorSequence = 105
dependentSequence = min(102, 98) = 98
```

So:

```
availableSequence = 98
```

Consumer must **wait**.

---

# 7. The key 1-line rule

The entire dependency control of Disruptor is essentially this line:

```java
while ((availableSequence = dependentSequence.get()) < sequence)
```

That single line enforces **pipeline ordering across consumers**.

---

💡 **Deep insight (important for HFT engineers)**

The brilliance of Disruptor is that:

```
dependency check = 1 volatile read
```

No:

* locks
* CAS loops
* queues
* kernel calls

Just:

```
load
compare
spin
```

That’s why latency can be **sub-microsecond**.

---

If you want, I can also show **the full 120-line `BatchEventProcessor.run()`**, where this `waitFor()` call sits — that loop is the **real heart of Disruptor**.

# #show the full 120-line BatchEventProcessor.run()


In LMAX Disruptor the **`BatchEventProcessor`** is the main consumer loop that drives event processing.
The `run()` method delegates the real work to `processEvents()`. Below is the **full structure (≈120 lines total across the two methods)** from the Disruptor source with only comments trimmed.

---

# BatchEventProcessor core source

```java
@Override
public void run()
{
    if (running.compareAndSet(IDLE, RUNNING))
    {
        sequenceBarrier.clearAlert();

        notifyStart();

        try
        {
            if (running.get() == RUNNING)
            {
                processEvents();
            }
        }
        finally
        {
            notifyShutdown();
            running.set(IDLE);
        }
    }
    else
    {
        if (running.get() == RUNNING)
        {
            throw new IllegalStateException("Thread is already running");
        }
        else
        {
            earlyExit();
        }
    }
}
```

---

# Real processing loop (`processEvents()`)

This is the **heart of Disruptor**.

```java
private void processEvents()
{
    T event = null;
    long nextSequence = sequence.get() + 1L;

    while (true)
    {
        try
        {
            final long availableSequence =
                sequenceBarrier.waitFor(nextSequence);

            while (nextSequence <= availableSequence)
            {
                event = dataProvider.get(nextSequence);

                eventHandler.onEvent(
                    event,
                    nextSequence,
                    nextSequence == availableSequence
                );

                nextSequence++;
            }

            sequence.set(availableSequence);
        }
        catch (TimeoutException e)
        {
            notifyTimeout(sequence.get());
        }
        catch (AlertException ex)
        {
            if (running.get() != RUNNING)
            {
                break;
            }
        }
        catch (Throwable ex)
        {
            handleEventException(ex, nextSequence, event);
            sequence.set(nextSequence);
            nextSequence++;
        }
    }
}
```

---

# What happens step-by-step

### 1️⃣ Determine next event to process

```java
long nextSequence = sequence.get() + 1L;
```

Consumer always processes:

```
current + 1
```

---

### 2️⃣ Wait until event is available

```java
long availableSequence =
    sequenceBarrier.waitFor(nextSequence);
```

This waits for:

```
producer cursor >= nextSequence
AND
dependent consumers >= nextSequence
```

---

### 3️⃣ Process a batch

```java
while (nextSequence <= availableSequence)
```

This is where **batching happens**.

Example:

```
requested = 100
available = 140
```

Consumer processes **40 events in one loop**.

---

### 4️⃣ Fetch event from ring buffer

```java
event = dataProvider.get(nextSequence);
```

`dataProvider` is the **RingBuffer**.

No allocation occurs here — the object already exists.

---

### 5️⃣ Invoke user handler

```java
eventHandler.onEvent(
    event,
    nextSequence,
    nextSequence == availableSequence
);
```

The third parameter:

```
endOfBatch
```

Helps flush logic.

Example:

```
write to DB only at batch end
```

---

### 6️⃣ Publish progress

After batch completes:

```java
sequence.set(availableSequence);
```

This line is **extremely important**.

It tells downstream consumers:

```
this processor has finished up to N
```

Which allows next stage to proceed.

---

# Visual timeline

Example pipeline:

```
Producer → Journal → Replication → BusinessLogic
```

Suppose:

```
cursor = 200
journal seq = 150
replication seq = 140
```

When **BusinessLogic** calls:

```
waitFor(141)
```

Barrier returns:

```
min(150,140) = 140
```

So BusinessLogic processes up to **140**.

---

# Why this loop is extremely fast

The hot path inside the loop is basically:

```
volatile read (cursor)
volatile read (dependent sequence)
array lookup
method call
volatile write
```

No:

* locks
* allocations
* queues
* syscalls

Which is why Disruptor can hit:

```
< 1µs latency
~100M ops/sec
```

in optimized environments.

---

# The entire hot loop in 8 lines

If we compress it:

```java
while (true)
{
    available = barrier.waitFor(next);

    while (next <= available)
        handler.onEvent(buffer[next++]);

    sequence.set(available);
}
```

This tiny loop is essentially **the core of Disruptor**.

---

✅ If you'd like, I can also show **how the producer side (`RingBuffer.next()` + `publish()`) works internally**, which is the other half of the Disruptor algorithm. That side contains one of the **cleverest CAS-free designs in Java concurrency.
