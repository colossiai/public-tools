# What log message in ZGC gc-*.log indicate problems? show detail and full information.

Alright, let’s put on the GC detective hat 🕵️‍♂️
Below is a **complete, practical checklist of ZGC log messages that indicate real or potential problems**, what they *mean internally*, **why they happen**, and **what to do about them**.

This is based on how ZGC is designed to behave—so anything that breaks its “mostly concurrent, tiny pauses” promise deserves attention.

---

# 🚨 ZGC log messages that indicate problems

I’ll group these by **severity**, from *critical* → *early warning*.

---

## 🔥 CRITICAL (these are never normal)

### 1️⃣ **Allocation Stall**

```
Allocation Stall
```

or

```
Allocation Stall <n>ms
```

### What it means

Your application **requested memory but ZGC could not provide it immediately**, so **application threads were blocked**.

This is the **worst thing you can see in ZGC logs**.

### Why this happens

* Heap is too small
* Allocation rate is too high
* Long-lived objects prevent space reuse
* ZGC can’t relocate fast enough

### What it causes

* Latency spikes
* Throughput collapse
* Cascading GC pressure

### What to do

* Increase heap size
* Reduce allocation rate
* Look for memory leaks
* Check object lifetime patterns

🚨 **If you see this repeatedly, your ZGC configuration is broken.**

---

## 🔥 CRITICAL

### 2️⃣ **Out Of Memory (even with ZGC)**

```
OutOfMemoryError: Java heap space
```

### What it means

ZGC failed to free memory fast enough or at all.

### Why it happens

* Legitimate memory exhaustion
* Heap severely undersized
* Unbounded caches
* Memory leak

ZGC does *not* magically prevent OOM.

### What to do

* Heap dump
* Leak analysis
* Revisit max heap sizing

---

## ⚠️ HIGH SEVERITY (very bad for latency)

### 3️⃣ **Pause times growing beyond expectations**

```
Pause Mark Start 8.4ms
Pause Relocate Start 12.1ms
```

### Why this is bad

ZGC is designed for **sub-millisecond to ~2ms pauses**.

Pauses above:

* 5ms → concerning
* 10ms → unhealthy
* 20ms → serious issue

### Root causes

* Too many GC roots
* Huge thread counts
* JNI-heavy applications
* Large class metadata footprint

### What to do

* Reduce thread count
* Investigate JNI usage
* Check metaspace size

---

## ⚠️ HIGH SEVERITY

### 4️⃣ **Relocation taking excessively long**

```
Concurrent Relocate 1500ms
```

### What it means

ZGC is struggling to compact memory.

### Common causes

* Heap almost full
* Fragmentation pressure
* Large live object set
* Objects pinned by JNI

### Symptoms

* Increased GC frequency
* Risk of allocation stalls

### What to do

* Increase heap
* Reduce long-lived objects
* Audit native memory pinning

---

## ⚠️ MEDIUM SEVERITY (early warning signs)

### 5️⃣ **Back-to-back GC cycles**

```
GC(101)
GC(102)
GC(103)
```

with very little time between them.

### What it means

ZGC is constantly under pressure.

### Root causes

* Heap occupancy too high
* Allocation rate exceeds reclamation rate

### Why it matters

This is how allocation stalls *start*.

### What to do

* Increase heap
* Reduce object churn
* Tune application memory behavior

---

## ⚠️ MEDIUM SEVERITY

### 6️⃣ **High heap occupancy after GC**

```
Heap Used: 92%
```

### Why this matters

ZGC needs **free headroom** to stay concurrent.

Healthy ZGC:

* Typically < 70–75% after GC

Danger zone:

* > 85% consistently

### What to do

* Increase heap
* Reduce retained objects

---

## ⚠️ MEDIUM SEVERITY

### 7️⃣ **Long Concurrent Mark**

```
Concurrent Mark 2000ms
```

### What it means

Large live object graph or complex references.

### Not always bad — but:

If it keeps increasing over time → memory leak likely.

### What to watch

* Growth trend, not absolute value

---

## ⚠️ LOW–MEDIUM SEVERITY (configuration or environment issues)

### 8️⃣ **GC workers underutilized**

```
GC Workers: 1 active
```

### Why this matters

ZGC relies on parallelism.

### Causes

* CPU starvation
* Container CPU limits
* OS scheduling pressure

### What to do

* Check CPU quotas
* Increase available cores

---

## ⚠️ LOW SEVERITY (but still useful signals)

### 9️⃣ **Metaspace pressure**

```
Metaspace allocation failure
```

### What it means

Class metadata pressure, not heap pressure.

### Causes

* Dynamic class generation
* Excessive class loading

### Fix

* Increase metaspace
* Fix classloader leaks

---

## ❌ NOT PROBLEMS (often misunderstood)

These are **normal** in ZGC:

```
Concurrent Mark
Concurrent Select Relocation Set
Pause Mark Start (≤ 2ms)
Pause Relocate Start (≤ 2ms)
```

High *concurrent* times alone are **not** an issue.

---

# 🧠 How to judge ZGC health at a glance

### ✅ Healthy ZGC

* No allocation stalls
* Pauses < 2ms
* Heap occupancy < 75%
* GC cycles well spaced

### 🚨 Unhealthy ZGC

* Allocation stalls
* Pauses > 10ms
* Heap > 85%
* Back-to-back GC cycles

---

# Want a real diagnosis?

If you paste:

* **10–20 lines from gc-*.log**, or
* Heap size + JDK version + workload type

I’ll tell you *exactly* what’s wrong (or happily say “this is fine” 😄).

