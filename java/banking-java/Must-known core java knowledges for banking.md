# Must known Java skills in banking

Love this direction — this is exactly how banks think about Java.
Below is a **bank-grade breakdown of MUST-KNOW Core Java**, the stuff interviewers *actually probe* and the stuff you’ll use daily in trading/risk systems.

I’ll go from **fundamentals → JVM internals → concurrency → performance**, with **what banks expect you to know vs just “heard of.”**

---

# 🧠 1. Java Memory Model (ABSOLUTELY CRITICAL)

This is the #1 differentiator in banking interviews.

### You must understand:

* **Heap vs Stack**
* Object lifecycle
* Escape analysis
* How references work

### Java Memory Areas:

| Area       | Purpose                                    |
| ---------- | ------------------------------------------ |
| Heap       | Objects, arrays                            |
| Stack      | Method calls, local primitives, references |
| Metaspace  | Class metadata                             |
| Code Cache | JIT-compiled bytecode                      |

### Interview-level knowledge:

* Why passing an object reference ≠ pass by reference
* Why local variables are thread-safe but fields aren’t
* How memory leaks happen without native memory

---

# 🧠 2. Garbage Collection (They Will Ask This)

Banks care deeply about **GC pauses**.

### You must know:

* How GC works conceptually
* Tradeoffs between GC algorithms

### Common GCs:

| GC               | Use case                              |
| ---------------- | ------------------------------------- |
| Serial           | Small apps                            |
| Parallel         | High throughput                       |
| G1               | Balanced latency/throughput (default) |
| ZGC / Shenandoah | Ultra-low latency                     |

### Key concepts:

* Young vs Old generation
* Minor vs Major GC
* Stop-the-world pauses
* Allocation rate vs promotion rate

💡 **Bank-level insight**:

> Many systems are designed to **avoid object allocation entirely** in hot paths.

---

# 🧵 3. Java Concurrency (THIS GETS YOU HIRED)

### Must-know primitives:

* `synchronized`
* `volatile`
* Happens-before relationship
* Memory visibility

### Concurrency utilities:

* `ExecutorService`
* `ThreadPoolExecutor`
* `ForkJoinPool`
* `CompletableFuture`
* `CountDownLatch`, `CyclicBarrier`, `Semaphore`

### Atomic classes:

* `AtomicInteger`
* `AtomicReference`
* CAS (Compare-And-Swap)

### Interview traps:

* Difference between **race condition vs deadlock**
* Why `volatile` ≠ atomic
* Why double-checked locking was broken pre-Java 5

---

# ⚙️ 4. JVM Internals & JIT Compilation

This separates **enterprise devs** from **bank devs**.

### You should understand:

* Bytecode vs machine code
* Class loading phases
* JIT compilation (C1 vs C2)
* Warm-up behavior

### Key topics:

* Inlining
* Escape analysis
* Dead code elimination
* De-optimization

💡 Bank reality:

> JVMs are warmed up before market open to avoid latency spikes.

---

# 📦 5. Object-Oriented Design (Beyond Textbook OOP)

Banks want **predictable, maintainable systems**.

### Must-know:

* Immutability (why it matters for concurrency)
* Composition > inheritance
* Value objects vs entities
* Defensive copying

### Immutability benefits:

* Thread-safe by design
* Easier reasoning
* GC friendly

---

# 🧬 6. Collections Framework (DEEP KNOWLEDGE EXPECTED)

### Must-know collections:

| Collection        | Key details                   |
| ----------------- | ----------------------------- |
| ArrayList         | Resizing cost, random access  |
| LinkedList        | Rarely used, cache-unfriendly |
| HashMap           | Hashing, collisions, resizing |
| ConcurrentHashMap | Lock striping, CAS            |
| TreeMap           | Sorted, red-black tree        |

### Interview topics:

* Why HashMap treeifies after many collisions
* Difference between fail-fast vs fail-safe iterators
* Why LinkedList is almost always a bad idea

---

# 🔍 7. Equals, HashCode & Identity

**Many real production bugs live here.**

### You must know:

* Contract of `equals()` and `hashCode()`
* When to override
* Why mutable keys break maps
* `==` vs `.equals()`

💥 Bank horror story:

> Trade disappeared from risk because key object mutated after insertion into a HashMap.

---

# 🧾 8. Exceptions & Error Handling

Banks hate unpredictable behavior.

### Must-know:

* Checked vs unchecked exceptions
* When to use which
* Exception cost
* Try-with-resources

### Bank rule of thumb:

> Exceptions are for **exceptional cases**, not flow control.

---

# 🧪 9. Java I/O & NIO

Used heavily in market data & file-based feeds.

### Must-know:

* Blocking vs non-blocking I/O
* ByteBuffers
* Memory-mapped files
* Backpressure

💡 Low-latency systems often use **NIO + off-heap buffers**.

---

# 🧩 10. Serialization & Object Layout

### Must-know:

* Java serialization pitfalls
* Custom serialization
* External formats (JSON, Avro, Protobuf)
* Object size awareness

Banks often avoid Java serialization entirely.

---

# 📈 11. Performance Profiling & Diagnostics

### You should know:

* JVM flags basics
* Heap dumps
* Thread dumps
* Profilers (JFR, async-profiler)

### Typical bank problem:

> “Latency spikes at 9:30am — explain why.”

---

# 🧠 What Banks EXPECT You To Explain Clearly

You should be able to explain:

* How a Java object is created and collected
* Why a system pauses during GC
* How threads safely share data
* Why a HashMap can become slow
* How JVM warmup affects latency

---

## 🚨 Reality Check

If you master just **these core Java areas**, you will:

* Pass **90% of IB Java interviews**
* Be productive in front-office systems
* Understand why systems fail under load

---

If you want, I can:

* 🔥 Create **bank-style Java interview questions**
* 🧪 Show **real trading-system Java patterns**
* 🗺️ Build a **90-day Java-for-investment-banks roadmap**

Just tell me your next move 👀
