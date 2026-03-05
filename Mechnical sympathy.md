# Mechanical Sympathy in Software

**Mechanical sympathy** is a software engineering principle that means:

> *Designing software with a deep understanding of how the underlying hardware actually works — so your code works **with** the machine, not against it.*

The term became popular in high-performance systems engineering, especially in the Java low-latency community.

---

## Origin

The concept was heavily promoted by **Martin Thompson**, co-founder of **Real Logic** and creator of **LMAX Disruptor**.

It comes from racing — a driver who understands the engine, gearbox, and tires can extract maximum performance without damaging the car.

---

# What It Means in Software

Mechanical sympathy means understanding:

### 1️⃣ CPU behavior

* CPU caches (L1, L2, L3)
* Cache lines (usually 64 bytes)
* Branch prediction
* Out-of-order execution
* Pipeline stalls

### 2️⃣ Memory layout

* Heap vs off-heap
* Object allocation cost
* False sharing
* Memory alignment
* NUMA effects

### 3️⃣ Concurrency mechanics

* Lock contention
* CAS (Compare-And-Swap)
* Memory barriers
* Volatile semantics

### 4️⃣ I/O characteristics

* Syscall cost
* Disk latency vs memory latency
* Network round-trip time

---

# Simple Example

### ❌ Without Mechanical Sympathy

```java
for (Object obj : list) {
    process(obj);
}
```

If `list` is a `LinkedList`, this causes:

* Pointer chasing
* Cache misses
* Poor CPU locality

---

### ✅ With Mechanical Sympathy

```java
for (int i = 0; i < array.length; i++) {
    process(array[i]);
}
```

Why better?

* Contiguous memory
* Fewer cache misses
* Better branch prediction
* Better JIT optimization

---

# In Low-Latency Trading Systems (Relevant to You)

Since you work on low-latency bots, this matters a lot:

Mechanical sympathy principles used in trading systems:

* Avoid GC pauses (use object pooling / off-heap)
* Use single-writer principle
* Avoid locks; prefer ring buffers
* Pin threads to cores
* Use busy-spin instead of blocking
* Pre-size data structures
* Avoid false sharing (use padding)

That’s why frameworks like:

* **LMAX Disruptor**
* **Aeron**
* **Chronicle Queue**

are built around mechanical sympathy.

---

# Why It Matters

Without mechanical sympathy:

* Latency spikes
* Unpredictable performance
* Throughput collapse under load

With mechanical sympathy:

* Stable p99 latency
* Deterministic behavior
* Better CPU efficiency

---

# Short Definition

> Mechanical sympathy = **understanding CPU + memory + OS behavior and writing code that aligns with it for performance and predictability.**

---

If you'd like, I can next show:

* A practical mechanical sympathy checklist for Java low-latency bots
* Or a false sharing demo
* Or how JVM JIT interacts with mechanical sympathy

Which direction do you want?

# A practical mechanical sympathy checklist for Java low-latency bots

Since you're building **Java low-latency bots**, here’s a **practical, production-oriented mechanical sympathy checklist** — optimized for trading/market-data style workloads (µs–ms sensitive).

I’ll group it by layer so you can use it as a deployment review sheet.

---

# 🧠 1. CPU & Core Usage

### ✅ Single Writer Principle

* One thread owns a data structure.
* Avoid multiple writers to same memory region.
* Reduces cache coherency traffic.

### ✅ Core Pinning

* Pin critical threads to dedicated cores.
* Avoid context switching.
* Use `taskset`, `cset shield`, or `isolcpus`.

### ✅ Avoid Oversubscription

* `#hot threads ≤ physical cores`
* Do NOT count hyperthreads as real cores for critical paths.

### ✅ Busy Spin for Critical Path

* Use busy-spin instead of blocking for ultra-low latency.
* Example: Disruptor `BusySpinWaitStrategy`.

Used in:

* LMAX Disruptor
* Aeron

---

# 🧵 2. Threading & Concurrency

### ❌ Avoid

* `synchronized`
* `ReentrantLock`
* Contended `Atomic*`
* Thread pools on hot path

### ✅ Prefer

* Lock-free ring buffers
* Single producer / single consumer queues
* `LongAdder` over `AtomicLong` for counters
* Pre-allocated executors

### ⚠ False Sharing Prevention

* Pad frequently updated fields
* Use `@Contended` (with JVM flag)

False sharing = different threads modifying variables on the same 64-byte cache line → massive performance drop.

---

# 💾 3. Memory & GC

### ✅ Allocation Discipline

* Zero allocations on hot path
* Reuse objects
* Pre-size collections
* Avoid boxing

Bad:

```java
new BigDecimal(price)
```

Better:

```java
long priceTicks
```

---

### ✅ Choose the Right GC

For low-latency bots:

* G1 (tuned) → most common
* ZGC → predictable pauses
* Shenandoah → ultra low pause

Avoid:

* Parallel GC for latency-sensitive bots

---

### ✅ Heap Sizing

* Fixed heap size:

```
-Xms = -Xmx
```

* Prevent heap resizing pauses

---

### ✅ Off-Heap for Critical Buffers

* `DirectByteBuffer`
* Unsafe / MemorySegment (Panama)
* Chronicle libraries

Used by:

* Chronicle Queue

---

# 🧮 4. Data Structures

### ✅ Prefer

* Arrays over LinkedList
* Primitive collections (fastutil, HPPC)
* Flat objects (avoid deep object graphs)

### ❌ Avoid

* `HashMap` in hot path (unless pre-sized)
* Streams API in critical loops
* Reflection

---

# 🔥 5. JIT & JVM Behavior

### ✅ Warmup Phase

* Always warm up before measuring.
* Let C2 JIT optimize hot methods.

### ✅ Keep Methods Small

* JVM inlining limit matters.
* Avoid megamorphic call sites.

### ✅ Avoid Exception-Based Flow

Exceptions are slow on hot path.

---

# 🌐 6. Networking

### ✅ Use

* TCP_NODELAY
* SO_REUSEADDR
* SO_RCVBUF tuned

### ✅ Kernel Tuning

Linux production checklist:

* `net.core.rmem_max`
* `net.core.wmem_max`
* `net.ipv4.tcp_low_latency=1`
* Disable Transparent Huge Pages
* Disable CPU frequency scaling
* Set `performance` governor

---

# 💽 7. Disk / Persistence

If journaling:

* Use sequential writes
* Memory-mapped files
* Avoid fsync on hot path (batch instead)

Mechanical sympathy systems:

* Chronicle Queue
* Aeron Archive

---

# 📊 8. Measurement Discipline

### ✅ Measure Correctly

* Use JMH for microbenchmarks
* Measure p99 / p999 latency
* Never trust averages

### ✅ Observe

* `perf`
* `async-profiler`
* GC logs
* CPU cache misses

---

# 🧊 9. Avoid Latency Killers

| Killer              | Why                  |
| ------------------- | -------------------- |
| Logging on hot path | Syscalls             |
| JSON serialization  | Allocation + parsing |
| DNS lookup          | Blocking             |
| Blocking I/O        | Context switch       |
| GC promotion        | STW pause            |
| Page faults         | µs–ms spike          |

---

# ⚙️ 10. Production Runtime Checklist

* [ ] Dedicated machine (no noisy neighbors)
* [ ] Isolated cores
* [ ] Fixed heap size
* [ ] Disabled swap
* [ ] HugePages tuned
* [ ] Monitoring p99 latency
* [ ] GC pause < SLA
* [ ] No allocation in matching loop
* [ ] No locks in hot path
* [ ] Warmed-up before trading session

---

# 🎯 Mechanical Sympathy Mindset

Always ask:

* Is this contiguous in memory?
* Is this predictable for branch predictor?
* Will this cause cache line bouncing?
* Will this allocate?
* Will this block?

---

Since you're working on **low-latency bot deployment**, if you want I can next give you:

* A concrete JVM startup template for production trading bots
* A Linux tuning checklist (copy-paste ready)
* Or a “latency debugging playbook” for p99 spikes

Pick one.
