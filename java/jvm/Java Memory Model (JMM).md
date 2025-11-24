# Explain JMM

The Java Memory Model (JMM) defines how threads interact through memory: what values reads can see, when writes become visible to other threads, and what reordering the compiler/JIT/CPU may legally perform. It’s the foundation for writing correct concurrent code in Java.

Key concepts:

- Shared memory and threads
  - All threads share the heap. Each thread has its own working memory (registers, CPU caches) where it may see stale values unless there’s proper synchronization.
  - The JMM specifies when a read must see a write (visibility) and in what order operations appear (ordering).

- Happens-before relation
  - A “happens-before” edge guarantees visibility and ordering: if A happens-before B, then B observes the effects of A.
  - Important happens-before rules:
    - Program order: Within a single thread, earlier actions happen-before later actions.
    - Monitor locks: An unlock on a given monitor happens-before every subsequent lock of that same monitor. So synchronized blocks/methods establish visibility.
    - Volatile variables: A write to a volatile field happens-before every subsequent read of that same field. Volatile also prevents certain reorderings with respect to that variable.
    - Thread lifecycle:
      - Thread.start(): actions in the parent thread before start() happen-before any actions in the started thread.
      - Thread.join(): all actions in a thread happen-before a successful return from join() on that thread.
      - Interruption: A call to interrupt() happens-before code that detects the interrupt via Thread.interrupted(), isInterrupted(), or InterruptedException.
    - Final fields: After an object’s constructor finishes normally, writes to its final fields happen-before any subsequent read of those fields by another thread that obtains a reference to the object, provided the reference isn’t leaked during construction.
    - Transitivity: If A happens-before B and B happens-before C, then A happens-before C.

- Visibility vs. atomicity vs. ordering
  - Visibility: When one thread’s write becomes observable to others. Achieved via happens-before (locks, volatiles, futures, latches, etc.).
  - Atomicity: Indivisible operations. In Java, reads/writes of references and most primitives are atomic, except long and double were not guaranteed prior to Java 5 on some platforms; since Java 5, they are atomic as well. Compound actions (x++, check-then-act) are not atomic without synchronization.
  - Ordering: The JIT/CPU may reorder instructions as long as it preserves single-thread semantics. Synchronization constructs impose ordering constraints.

- Volatile semantics
  - A volatile read/written field:
    - Is always read/written from main memory (as if flushing/invalidation around the access).
    - Establishes happens-before edges: write to volatile v happens-before subsequent read of v.
    - Prevents reordering of volatile reads/writes with respect to other memory operations across them (acquire/release semantics).
  - Volatile is good for:
    - Flags, publication of immutable or effectively immutable objects.
    - Simple, independent state where you don’t need compound atomicity.
  - Volatile is not enough for:
    - Increments, check-then-act, or any multi-step invariants—use locks or atomic classes.

- Locks and synchronized
  - Entering a synchronized block acquires a monitor; exiting releases it.
  - Release flushes the thread’s writes to main memory; subsequent acquire sees them.
  - Locks also provide mutual exclusion (atomicity for critical sections) in addition to visibility/order.

- Atomic classes and VarHandles
  - java.util.concurrent.atomic (e.g., AtomicInteger, AtomicReference) provide atomic read-modify-write operations with well-defined memory semantics (usually volatile + CAS with acquire/release).
  - VarHandle (Java 9+) exposes fine-grained memory modes: get/set (volatile), getAcquire/setRelease, getOpaque/setOpaque, and compareAndSet, etc.

- Safe publication
  - To safely publish an object so other threads see a fully constructed state, use:
    - Storing a reference to a volatile field or AtomicReference.
    - Storing into a final field of another properly constructed object.
    - Guarding with a lock: write under lock, read under same lock.
    - Publishing via thread-safe containers (ConcurrentHashMap, BlockingQueue).
    - Starting a thread or completing a Future after construction.
  - Unsafe publication can lead to other threads seeing default values in fields (reordering of constructor writes).

- Out-of-thin-air values
  - The JMM forbids “out-of-thin-air” reads (seeing values that could not have been produced by any execution), though specifics are subtle. Races on non-volatile variables can still see stale but previously written values.

- Data races
  - A data race occurs if two threads access the same variable, at least one access is a write, and there’s no happens-before ordering between them.
  - Programs free of data races are guaranteed to be sequentially consistent under the JMM (SC-for-DRF property).

- Double-checked locking
  - Correct form requires volatile on the reference:
    - if (instance == null) { synchronized(...) { if (instance == null) instance = new Foo(); } }
    - Without volatile, reordering could let another thread see a non-null reference to a partially constructed object.

- Final fields
  - Provide special guarantees: once construction finishes normally, other threads will see correct values of finals without synchronization, provided the reference is safely published and not leaked during construction.
  - Finals cannot be modified after construction; reflection can break this only with special flags and may drop guarantees.

- Common patterns and tools
  - Immutability: Prefer immutable objects; no synchronization needed for read-only sharing.
  - Confinement: Keep data thread-confined to avoid sharing.
  - Higher-level concurrency utilities: Executors, Futures/CompletableFuture, Locks, Semaphores, Latches, Barriers, Queues. These are all specified with JMM-compliant happens-before relationships.

- Practical tips
  - If multiple threads read/write shared mutable state, ensure every path of access is ordered by a happens-before relationship.
  - Use synchronized or locks for compound actions. Use volatile only for simple flags or publication.
  - Avoid publishing this from constructors.
  - Favor thread-safe collections and concurrent utilities instead of manual synchronization.
  - Test with tools like JCStress for concurrency correctness, and use race detectors where possible.

If you want, I can show small code examples illustrating volatile, locking, safe publication, and broken patterns.

# Show the code

Here are concise Java examples illustrating key Java Memory Model (JMM) concepts.

1) Volatile for visibility (flag)
- Without volatile, worker might loop forever due to cached value.

```java
public class VolatileFlag {
    private static volatile boolean running = true; // visibility guarantee

    public static void main(String[] args) throws InterruptedException {
        Thread t = new Thread(() -> {
            long c = 0;
            while (running) { c++; }
            System.out.println("Stopped at " + c);
        });
        t.start();

        Thread.sleep(100);     // do some work
        running = false;       // write to volatile happens-before read in thread
        t.join();
    }
}
```

2) Volatile is not enough for compound actions
- This is broken: increments race even if x is volatile.

```java
public class BrokenVolatileIncrement {
    private static volatile int x = 0;

    public static void main(String[] args) throws InterruptedException {
        Thread t1 = new Thread(BrokenVolatileIncrement::work);
        Thread t2 = new Thread(BrokenVolatileIncrement::work);
        t1.start(); t2.start();
        t1.join(); t2.join();
        System.out.println("x = " + x); // often < 2_000_000
    }

    private static void work() {
        for (int i = 0; i < 1_000_000; i++) {
            x++; // read-modify-write is not atomic
        }
    }
}
```

3) Fix with AtomicInteger (atomic read-modify-write)
```java
import java.util.concurrent.atomic.AtomicInteger;

public class AtomicIncrement {
    private static final AtomicInteger x = new AtomicInteger();

    public static void main(String[] args) throws InterruptedException {
        Thread t1 = new Thread(AtomicIncrement::work);
        Thread t2 = new Thread(AtomicIncrement::work);
        t1.start(); t2.start();
        t1.join(); t2.join();
        System.out.println("x = " + x.get()); // exactly 2_000_000
    }

    private static void work() {
        for (int i = 0; i < 1_000_000; i++) {
            x.incrementAndGet(); // CAS loop under the hood; has JMM guarantees
        }
    }
}
```

4) Locks (synchronized) provide mutual exclusion and visibility
```java
public class SynchronizedCounter {
    private int x = 0;

    public synchronized void inc() { // acquire -> critical sect -> release
        x++;
    }

    public synchronized int get() {
        return x;
    }

    public static void main(String[] args) throws InterruptedException {
        SynchronizedCounter c = new SynchronizedCounter();
        Thread t1 = new Thread(() -> { for (int i=0;i<1_000_000;i++) c.inc(); });
        Thread t2 = new Thread(() -> { for (int i=0;i<1_000_000;i++) c.inc(); });
        t1.start(); t2.start();
        t1.join(); t2.join();
        System.out.println("x = " + c.get()); // exactly 2_000_000
    }
}
```

5) Safe publication with volatile
```java
public class SafePublication {
    private static class Config {
        final int port;
        final String host;
        Config(int port, String host) { this.port = port; this.host = host; }
    }

    private static volatile Config config; // safe publication vehicle

    public static void main(String[] args) throws InterruptedException {
        Thread writer = new Thread(() -> {
            Config c = new Config(8080, "localhost");
            config = c; // write to volatile safely publishes fully constructed object
        });
        Thread reader = new Thread(() -> {
            while (config == null) { /* spin */ }
            System.out.println(config.host + ":" + config.port);
        });
        writer.start(); reader.start();
        writer.join(); reader.join();
    }
}
```

6) Unsafe publication (don’t do this)
- Reader might see default 0 or null because reference was published without a happens-before edge.

```java
public class UnsafePublication {
    static Holder holder; // non-volatile, no locking

    static class Holder {
        int x;
        String s;
        Holder() {
            x = 42;
            s = "ready";
        }
    }

    public static void main(String[] args) throws InterruptedException {
        Thread writer = new Thread(() -> holder = new Holder()); // may reorder
        Thread reader = new Thread(() -> {
            while (holder == null) { /* spin */ }
            // Data race: could print "x=0, s=null" on some architectures/JITs
            System.out.println("x=" + holder.x + ", s=" + holder.s);
        });
        writer.start(); reader.start();
        writer.join(); reader.join();
    }
}
```

7) Double-checked locking (correct with volatile)
```java
public class DoubleCheckedLocking {
    private static volatile Foo instance; // volatile is required

    public static Foo getInstance() {
        Foo local = instance;
        if (local == null) {
            synchronized (DoubleCheckedLocking.class) {
                local = instance;
                if (local == null) {
                    local = new Foo(); // fully constructed before publish
                    instance = local;  // volatile write -> safe publication
                }
            }
        }
        return local;
    }

    static class Foo { /* heavy init */ }
}
```

8) Final field guarantees (safe without extra sync if not leaked)
```java
public class FinalsExample {
    static class Point {
        final int x, y;
        Point(int x, int y) {
            this.x = x; this.y = y; // after constructor completes normally,
        }                            // other threads see correct finals
    }

    static volatile Point p;

    public static void main(String[] args) throws Exception {
        Thread writer = new Thread(() -> p = new Point(1, 2)); // publish via volatile
        Thread reader = new Thread(() -> {
            while (p == null) {}
            // JMM guarantees: reads see x=1, y=2
            System.out.println(p.x + "," + p.y);
        });
        writer.start(); reader.start();
        writer.join(); reader.join();
    }
}
```

9) Thread lifecycle happens-before: start and join
```java
public class StartJoinHB {
    static int x = 0;

    public static void main(String[] args) throws InterruptedException {
        Thread t = new Thread(() -> x = 42); // after start(), actions in main happen-before this
        // Writes before start() are visible in thread; writes in thread visible after join()
        t.start();
        t.join(); // all actions in t happen-before returning from join
        System.out.println(x); // guaranteed to print 42
    }
}
```

10) VarHandle with acquire/release/opaque (Java 9+)
```java
import java.lang.invoke.MethodHandles;
import java.lang.invoke.VarHandle;

public class VarHandleModes {
    static class Box {
        volatile int v; // for get/setVolatile; field must exist
        int x;          // for opaque/acquire/release on same field via VH
    }

    private static final VarHandle VH_X;
    static {
        try {
            VH_X = MethodHandles.lookup()
                    .in(Box.class)
                    .findVarHandle(Box.class, "x", int.class);
        } catch (ReflectiveOperationException e) {
            throw new ExceptionInInitializerError(e);
        }
    }

    public static void main(String[] args) {
        Box b = new Box();

        // Release store: prior writes can't move after it
        VH_X.setRelease(b, 123);

        // Acquire load: subsequent reads can't move before it
        int r = (int) VH_X.getAcquire(b);

        // Opaque: very weak ordering, only minimal visibility
        VH_X.setOpaque(b, 7);
        int o = (int) VH_X.getOpaque(b);

        // CAS with full volatile semantics
        boolean ok = VH_X.compareAndSet(b, o, 9);
        System.out.println(r + " " + o + " " + ok);
    }
}
```

11) Using higher-level utilities (happens-before through queues)
```java
import java.util.concurrent.*;

public class QueueHB {
    public static void main(String[] args) throws InterruptedException {
        BlockingQueue<String> q = new LinkedBlockingQueue<>();

        Thread producer = new Thread(() -> {
            // The put establishes a happens-before with the corresponding take
            q.add("ready");
        });
        Thread consumer = new Thread(() -> {
            try {
                String s = q.take();
                System.out.println(s);
            } catch (InterruptedException ignored) {}
        });

        producer.start(); consumer.start();
        producer.join(); consumer.join();
    }
}
```

12) Demonstrating data race causing stale reads
```java
public class DataRaceStale {
    static int a = 0;
    static boolean flag = false;

    public static void writer() {
        a = 42;           // write 1
        flag = true;      // write 2 (no volatile/lock) — may reorder or be unseen
    }

    public static void reader() {
        if (flag) {       // may read true but still see a == 0, or may never see true
            System.out.println(a);
        }
    }

    public static void main(String[] args) throws Exception {
        Thread t1 = new Thread(DataRaceStale::writer);
        Thread t2 = new Thread(DataRaceStale::reader);
        t2.start();
        t1.start();
        t1.join(); t2.join();
    }
}
```
