# #show A 3-stage pipeline using SequenceBarrier dependencies (Journal → Replication → Business Logic)


Below is a **minimal but realistic 3-stage pipeline** built directly with the core API of **LMAX Disruptor** using **`SequenceBarrier` dependencies**.

This mirrors the architecture used in the original **LMAX Exchange** trading engine:

```
Producer
   |
   v
RingBuffer
   |
   +----> Journal Consumer
   |
   +----> Replication Consumer
            |
            v
        Business Logic Consumer
```

Dependency rule:

```
Business Logic must wait for:
    Journal AND Replication
```

This is enforced using **SequenceBarrier dependencies**.

---

# 1. Event Definition

```java
class TradeEvent {
    long orderId;
}
```

Factory:

```java
import com.lmax.disruptor.EventFactory;

class TradeEventFactory implements EventFactory<TradeEvent> {
    public TradeEvent newInstance() {
        return new TradeEvent();
    }
}
```

---

# 2. Generic Consumer Processor

Each pipeline stage is implemented as a **custom EventProcessor**.

```java
import com.lmax.disruptor.*;

public class PipelineProcessor implements Runnable {

    private final String name;
    private final RingBuffer<TradeEvent> ringBuffer;
    private final SequenceBarrier barrier;
    private final Sequence sequence = new Sequence(-1);

    public PipelineProcessor(
            String name,
            RingBuffer<TradeEvent> ringBuffer,
            SequenceBarrier barrier) {

        this.name = name;
        this.ringBuffer = ringBuffer;
        this.barrier = barrier;
    }

    public Sequence getSequence() {
        return sequence;
    }

    @Override
    public void run() {

        long nextSequence = sequence.get() + 1;

        try {

            while (true) {

                long availableSequence = barrier.waitFor(nextSequence);

                while (nextSequence <= availableSequence) {

                    TradeEvent event = ringBuffer.get(nextSequence);

                    System.out.println(
                        name + " processed order "
                        + event.orderId +
                        " seq=" + nextSequence);

                    nextSequence++;
                }

                sequence.set(availableSequence);
            }

        } catch (AlertException e) {
            System.out.println(name + " stopping.");
        } catch (Exception e) {
            e.printStackTrace();
        }
    }
}
```

Important line:

```
barrier.waitFor(nextSequence)
```

This ensures **dependency ordering**.

---

# 3. Producer

```java
class TradeProducer {

    private final RingBuffer<TradeEvent> ringBuffer;

    public TradeProducer(RingBuffer<TradeEvent> ringBuffer) {
        this.ringBuffer = ringBuffer;
    }

    public void publish(long orderId) {

        long seq = ringBuffer.next();

        try {
            TradeEvent event = ringBuffer.get(seq);
            event.orderId = orderId;
        } finally {
            ringBuffer.publish(seq);
        }
    }
}
```

---

# 4. Build the 3-Stage Pipeline

```java
import com.lmax.disruptor.*;

public class PipelineDemo {

    public static void main(String[] args) throws Exception {

        int bufferSize = 1024;

        RingBuffer<TradeEvent> ringBuffer =
            RingBuffer.createSingleProducer(
                new TradeEventFactory(),
                bufferSize,
                new BusySpinWaitStrategy()
            );

        // stage 1 barriers
        SequenceBarrier journalBarrier = ringBuffer.newBarrier();
        SequenceBarrier replicationBarrier = ringBuffer.newBarrier();

        // processors
        PipelineProcessor journal =
            new PipelineProcessor("Journal", ringBuffer, journalBarrier);

        PipelineProcessor replication =
            new PipelineProcessor("Replication", ringBuffer, replicationBarrier);

        // stage 2 barrier (depends on both)
        SequenceBarrier businessBarrier =
            ringBuffer.newBarrier(
                journal.getSequence(),
                replication.getSequence()
            );

        PipelineProcessor business =
            new PipelineProcessor("BusinessLogic", ringBuffer, businessBarrier);

        // gating
        ringBuffer.addGatingSequences(
            journal.getSequence(),
            replication.getSequence(),
            business.getSequence()
        );

        // start threads
        new Thread(journal).start();
        new Thread(replication).start();
        new Thread(business).start();

        // producer
        TradeProducer producer = new TradeProducer(ringBuffer);

        for (int i = 1; i <= 5; i++) {
            producer.publish(i);
            Thread.sleep(300);
        }

        Thread.sleep(2000);

        journalBarrier.alert();
        replicationBarrier.alert();
        businessBarrier.alert();
    }
}
```

---

# 5. Dependency Graph

The key line is:

```java
SequenceBarrier businessBarrier =
    ringBuffer.newBarrier(
        journal.getSequence(),
        replication.getSequence()
    );
```

Meaning:

```
BusinessLogic waits until:

min(journalSeq, replicationSeq) >= requestedSeq
```

Graph:

```
           +------ Journal
Producer --|
           +------ Replication
                     |
                     v
               BusinessLogic
```

---

# 6. Example Output

Typical execution:

```
Journal processed order 1 seq=0
Replication processed order 1 seq=0
BusinessLogic processed order 1 seq=0

Journal processed order 2 seq=1
Replication processed order 2 seq=1
BusinessLogic processed order 2 seq=1
```

Guarantee:

```
BusinessLogic never runs before Journal and Replication finish
```

---

# 7. Why This Architecture Is Powerful

This pipeline provides **three critical properties**:

### 1️⃣ Parallelism

```
Journal
Replication
```

run **in parallel**.

---

### 2️⃣ Deterministic ordering

```
BusinessLogic waits for both
```

ensuring consistent state.

---

### 3️⃣ Zero locks

Coordination uses only:

```
volatile sequence reads
CPU cache coherence
memory barriers
```

This is why Disruptor achieves **extremely low latency (<1µs)**.

---

# 8. Real Trading Engine Analogy

In a trading system:

```
Producer
   |
   v
Order event
   |
   +--> Journal (disk persistence)
   |
   +--> Replication (send to backup node)
            |
            v
       Matching engine
```

The matching engine runs **only after durability + replication**.

This pattern is a major reason **LMAX Exchange** achieved extremely low latency.

---

✅ **Key takeaway**

`SequenceBarrier` allows building **lock-free dependency graphs between consumers**, enabling highly parallel pipelines while preserving strict processing order.

---

If you'd like, I can also show something **very insightful for performance engineers**:

**How the Disruptor dependency graph is actually implemented internally using `FixedSequenceGroup` and why it avoids contention even with many consumers.**



# #In you above demo, PipelineProcessor is like BatchEventProcessor?

Yes — in the demo I showed, **`PipelineProcessor` is essentially a simplified re-implementation of** **BatchEventProcessor** from **LMAX Disruptor**.

The real `BatchEventProcessor` just adds some production features around the **exact same core loop**.

---

# 1. Core Similarity

Your demo processor:

```java
long availableSequence = barrier.waitFor(nextSequence);

while (nextSequence <= availableSequence) {
    TradeEvent event = ringBuffer.get(nextSequence);
    process(event);
    nextSequence++;
}

sequence.set(availableSequence);
```

This is **almost identical** to the real `BatchEventProcessor.run()` logic.

Simplified real code:

```java
long nextSequence = sequence.get() + 1;

while (running) {

    long availableSequence = sequenceBarrier.waitFor(nextSequence);

    while (nextSequence <= availableSequence) {

        E event = dataProvider.get(nextSequence);

        eventHandler.onEvent(event, nextSequence, nextSequence == availableSequence);

        nextSequence++;
    }

    sequence.set(availableSequence);
}
```

So conceptually:

```text
PipelineProcessor ≈ BatchEventProcessor
```

---

# 2. Why My Demo Used a Custom Processor

I used `PipelineProcessor` to **expose the core mechanics** clearly.

The real `BatchEventProcessor` introduces several abstractions:

| Feature            | Purpose                  |
| ------------------ | ------------------------ |
| `EventHandler`     | separates business logic |
| `LifecycleAware`   | startup/shutdown hooks   |
| `ExceptionHandler` | error handling           |
| `BatchStartAware`  | notify batch start       |
| `TimeoutHandler`   | timeout support          |

For teaching **SequenceBarrier**, those add noise.

---

# 3. How the Real API Looks

In normal Disruptor usage you don't write the loop yourself.

You instead write an **EventHandler**:

```java
class JournalHandler implements EventHandler<TradeEvent> {

    @Override
    public void onEvent(TradeEvent event, long sequence, boolean endOfBatch) {
        System.out.println("Journal " + event.orderId);
    }
}
```

Then attach it to a `BatchEventProcessor`.

---

# 4. Real Equivalent of My Demo

What I manually wrote:

```text
PipelineProcessor
   |
   v
SequenceBarrier
   |
   v
RingBuffer
```

Real Disruptor:

```text
BatchEventProcessor
   |
   v
SequenceBarrier
   |
   v
RingBuffer
```

---

# 5. What `BatchEventProcessor` Actually Contains

Key fields (simplified):

```java
final DataProvider<E> dataProvider;
final SequenceBarrier sequenceBarrier;
final EventHandler<? super E> eventHandler;

final Sequence sequence = new Sequence(-1);
```

Execution flow:

```text
run()
  |
  v
waitFor(nextSequence)
  |
  v
process batch
  |
  v
update sequence
```

Exactly the same logic as the demo.

---

# 6. Why It Is Called **Batch**EventProcessor

Notice this part:

```java
while (nextSequence <= availableSequence)
```

If producer published multiple events:

```text
cursor = 10
consumer wants = 5
```

Consumer processes:

```text
5
6
7
8
9
10
```

**in a single batch**.

Benefits:

* fewer memory fences
* fewer sequence updates
* better cache locality

---

# 7. Why `BatchEventProcessor` Is Extremely Efficient

The hot path typically compiles to something like:

```asm
mov cursor
cmp nextSequence
jl spin
```

Then the batch loop:

```asm
mov event
call handler
inc seq
```

No:

```
locks
queues
syscalls
kernel scheduling
```

This is why Disruptor is used in **ultra-low latency systems** like the original **LMAX Exchange** engine.

---

# 8. Key Insight

The **entire Disruptor consumer model boils down to just this loop**:

```java
while (running) {

    long available = barrier.waitFor(nextSequence);

    while (nextSequence <= available) {
        process(event);
        nextSequence++;
    }

    sequence.set(available);
}
```

Everything else in the framework is **just wiring around this loop**.

---

✅ **Short answer**

Yes — the demo `PipelineProcessor` is basically a **minimal educational version of `BatchEventProcessor`**.

---

If you'd like, I can also show something **very illuminating for understanding Disruptor**:

**A fully annotated 120-line walkthrough of `BatchEventProcessor.run()` explaining every line and why it exists.**

