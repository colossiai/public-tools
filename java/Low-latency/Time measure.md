# Java measure time in low-latency context

In **low-latency Java systems** (trading systems, high-frequency services, benchmarking), the main requirement is **high-resolution and monotonic time**. The correct tool is almost always:

👉 **`System.nanoTime()`**

---

# 1. The Correct Method: `System.nanoTime()`

`System.nanoTime()` is designed for **measuring elapsed time**, not wall clock time.

Characteristics:

| Property                    | Behavior                                           |
| --------------------------- | -------------------------------------------------- |
| Resolution                  | Nanoseconds (actual precision depends on hardware) |
| Monotonic                   | ✅ Never goes backwards                             |
| Affected by NTP/time change | ❌ No                                               |
| Best for                    | Latency measurement                                |

### Example

```java
long start = System.nanoTime();

// code to measure
doWork();

long end = System.nanoTime();
long latencyNs = end - start;

System.out.println("Latency: " + latencyNs + " ns");
```

Convert if needed:

```java
long micros = latencyNs / 1_000;
long millis = latencyNs / 1_000_000;
```

---

# 2. Why NOT `System.currentTimeMillis()`

```java
long start = System.currentTimeMillis();
```

Problems:

| Problem         | Reason                         |
| --------------- | ------------------------------ |
| Low resolution  | ~1–10 ms                       |
| Not monotonic   | Clock can move backwards       |
| NTP adjustments | Can break latency measurements |

Example issue:

```
t1 = 1000 ms
NTP correction happens
t2 = 995 ms
```

Your latency becomes **negative**.

---

# 3. Typical Low-Latency Measurement Pattern

Avoid allocations and extra work.

```java
long start = System.nanoTime();

processOrder(order);

long latency = System.nanoTime() - start;
histogram.recordValue(latency);
```

Many trading systems store the latency in **nanoseconds**.

---

# 4. Ultra-Low Latency Pattern (Avoiding Repeated Calls)

In hot loops:

```java
long t = System.nanoTime();

for (int i = 0; i < N; i++) {
    work();
}

long elapsed = System.nanoTime() - t;
```

Calling `nanoTime()` itself costs **~20–80 ns** depending on CPU.

---

# 5. What Happens Under the Hood

On modern systems Java maps `nanoTime()` to hardware timers:

| Platform | Source                           |
| -------- | -------------------------------- |
| Linux    | `clock_gettime(CLOCK_MONOTONIC)` |
| x86 CPUs | TSC (Time Stamp Counter)         |
| macOS    | `mach_absolute_time()`           |

When using **TSC**, latency can be **~20ns**.

---

# 6. For Real Benchmarking Use JMH

Manual timing is often wrong due to:

* JIT compilation
* dead code elimination
* warmup effects
* CPU scaling

The official tool is:

👉 **Java Microbenchmark Harness (JMH)** from **OpenJDK**

Example:

```java
@Benchmark
public void testMethod() {
    doWork();
}
```

Run:

```
mvn clean install
java -jar target/benchmarks.jar
```

---

# 7. Real Low-Latency Production Trick (Used in Trading)

Instead of measuring everywhere:

Use **HDR Histograms**:

```java
Histogram histogram = new Histogram(3);

long start = System.nanoTime();
process();
histogram.recordValue(System.nanoTime() - start);
```

Library from **Gil Tene**.

---

# 8. Typical Latency Numbers (Reality Check)

| Operation           | Latency     |
| ------------------- | ----------- |
| `System.nanoTime()` | ~20–80 ns   |
| L1 cache access     | ~1 ns       |
| L3 cache            | ~10–20 ns   |
| Memory access       | ~80–120 ns  |
| Lock contention     | 100 ns – µs |
| Network             | µs – ms     |

So timing calls are **not free**.

---

# 9. Pro Tip (Important for HFT / Low Latency)

Avoid this:

```java
long start = System.nanoTime();
try {
    work();
} finally {
    log(System.nanoTime() - start);
}
```

Logging in hot paths destroys latency.

Instead:

```
measure → record → analyze offline
```

---

✅ **Summary**

Best practice:

```java
long start = System.nanoTime();
work();
long elapsed = System.nanoTime() - start;
```

Use:

* `System.nanoTime()` → latency measurement
* JMH → benchmarking
* HDR Histogram → production latency tracking

---

If you'd like, I can also show:

* **How `System.nanoTime()` is implemented inside the JVM (HotSpot source code)**
* **How high-frequency trading engines measure latency with <100ns overhead**
* **How to build a zero-allocation Java latency profiler (very cool trick)**.

