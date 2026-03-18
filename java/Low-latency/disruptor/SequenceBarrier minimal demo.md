Below is a **minimal runnable demo** showing how **`SequenceBarrier`** is used inside the **LMAX Disruptor** core API (without the higher-level DSL).

This example demonstrates:

1. Producer publishing events to a `RingBuffer`
2. A consumer using `SequenceBarrier.waitFor()`
3. The consumer processing events **only when they become available**

---

# 1. Maven Dependency

```xml
<dependency>
    <groupId>com.lmax</groupId>
    <artifactId>disruptor</artifactId>
    <version>3.4.4</version>
</dependency>
```

---

# 2. Event Object

Simple event stored in the ring buffer.

```java
class MyEvent {
    long value;
}
```

Factory required by Disruptor:

```java
import com.lmax.disruptor.EventFactory;

class MyEventFactory implements EventFactory<MyEvent> {
    public MyEvent newInstance() {
        return new MyEvent();
    }
}
```

---

# 3. Minimal Consumer Using `SequenceBarrier`

This shows the **core usage pattern**.

```java
import com.lmax.disruptor.*;

public class SimpleEventProcessor implements Runnable {

    private final RingBuffer<MyEvent> ringBuffer;
    private final SequenceBarrier barrier;
    private final Sequence sequence = new Sequence(-1);

    public SimpleEventProcessor(RingBuffer<MyEvent> ringBuffer,
                                SequenceBarrier barrier) {
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

                // WAIT HERE
                long availableSequence = barrier.waitFor(nextSequence);

                while (nextSequence <= availableSequence) {

                    MyEvent event = ringBuffer.get(nextSequence);

                    System.out.println(
                        "Consumed: " + event.value +
                        " seq=" + nextSequence);

                    nextSequence++;
                }

                sequence.set(availableSequence);
            }

        } catch (AlertException e) {
            System.out.println("Processor stopped");
        } catch (Exception e) {
            e.printStackTrace();
        }
    }
}
```

Important line:

```java
long availableSequence = barrier.waitFor(nextSequence);
```

This blocks/spins until the event is **published by the producer**.

---

# 4. Producer

Producer publishes events into the ring buffer.

```java
class Producer {

    private final RingBuffer<MyEvent> ringBuffer;

    Producer(RingBuffer<MyEvent> ringBuffer) {
        this.ringBuffer = ringBuffer;
    }

    public void publish(long value) {

        long sequence = ringBuffer.next();

        try {
            MyEvent event = ringBuffer.get(sequence);
            event.value = value;
        }
        finally {
            ringBuffer.publish(sequence);
        }
    }
}
```

Publishing increases the **cursor sequence**.

---

# 5. Main Program

Putting everything together.

```java
import com.lmax.disruptor.*;
import com.lmax.disruptor.dsl.ProducerType;

import java.util.concurrent.Executors;

public class DisruptorBarrierDemo {

    public static void main(String[] args) throws Exception {

        int bufferSize = 1024;

        RingBuffer<MyEvent> ringBuffer =
            RingBuffer.createSingleProducer(
                new MyEventFactory(),
                bufferSize,
                new BusySpinWaitStrategy()
            );

        // create barrier
        SequenceBarrier barrier = ringBuffer.newBarrier();

        // consumer
        SimpleEventProcessor processor =
            new SimpleEventProcessor(ringBuffer, barrier);

        ringBuffer.addGatingSequences(processor.getSequence());

        Thread consumerThread = new Thread(processor);
        consumerThread.start();

        Producer producer = new Producer(ringBuffer);

        for (int i = 0; i < 10; i++) {
            producer.publish(i);
            Thread.sleep(500);
        }

        barrier.alert();
    }
}
```

---

# 6. Execution Flow

Runtime behavior:

```
Producer publishes event
        |
        v
RingBuffer cursor increases
        |
        v
SequenceBarrier.waitFor()
        |
        v
Consumer wakes up
        |
        v
Event processed
```

Example output:

```
Consumed: 0 seq=0
Consumed: 1 seq=1
Consumed: 2 seq=2
Consumed: 3 seq=3
...
```

---

# 7. Why `SequenceBarrier` Matters

Without it, the consumer would have to **poll blindly**:

```
while(cursor < nextSequence)
    spin
```

`SequenceBarrier` adds:

* dependency tracking
* wait strategy
* shutdown signalling
* safe publication checks

---

# 8. Minimal Conceptual Diagram

```
Producer
   |
   v
RingBuffer
   |
cursor sequence
   |
   v
SequenceBarrier
   |
   v
EventProcessor
   |
   v
Consumer Logic
```

---

💡 **Important takeaway**

`SequenceBarrier` is the **core synchronization point** between producers and consumers in Disruptor.
Every consumer thread waits on it to know **when it can safely read events**.

---

If you'd like, I can also show a **much more interesting demo**:

**A 3-stage pipeline using SequenceBarrier dependencies (Journal → Replication → Business Logic)** — this is exactly how Disruptor was used in the original **LMAX Exchange** trading engine.
