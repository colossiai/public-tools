# Throughput vs Latency

```
Is this mental model right?

Throughput: how many ops per second, e.g. 1000000 ops per second
Latency: how much time to execute op. e.g. 10 ns/op
```


Yes — your mental model is basically correct, and it’s actually the standard way these terms are used in systems, networking, and benchmarking contexts. Let me clarify a bit more precisely:

---

### **Throughput**

* Definition: Number of operations (or work units) completed per unit time.
* Units: ops/sec, requests/sec, MB/s, etc.
* Example: `1,000,000 ops/sec` → your system can handle one million operations **every second**.
* Key insight: High throughput means the system can handle a lot of work **in parallel or over time**, but doesn’t tell you how long a single operation takes.

---

### **Latency**

* Definition: Time it takes to complete **one operation**.
* Units: seconds, milliseconds, microseconds, nanoseconds, etc.
* Example: `10 ns/op` → a single operation takes 10 nanoseconds to complete.
* Key insight: Low latency means individual operations finish quickly, but it doesn’t directly tell you how many operations the system can handle **overall**.

---

### ⚠️ Important nuance

Throughput and latency are related but **not the same**:

* If you increase parallelism, throughput can go up **without reducing individual latency**.
* Sometimes high throughput can **increase latency**, if the system is overloaded (think queues forming).

So your mental model is correct for raw definitions, but keep in mind the subtle interplay: **latency is per operation; throughput is total operations over time**.

---

If you want, I can draw a little visual diagram that shows throughput vs latency, which makes the distinction really obvious. Do you want me to do that?


# Can we say: roughly, latency = 1/throughput ?

Not exactly — that only works under **very specific conditions**. Let’s break it down carefully.

---

### **When 1/throughput ≈ latency**

* This is true **only in an ideal, perfectly pipelined system** where:

  1. There is **exactly one operation in flight at a time** (no parallelism).
  2. There is **no queuing, contention, or overhead**.

In that case:

**throughput = 1 op / latency => latency = 1 / throughput**

[
\text{throughput} = \frac{1 \text{ op}}{\text{latency}}
\quad\Rightarrow\quad
\text{latency} = \frac{1}{\text{throughput}}
]

Example:

* Latency = 10 ns/op
* Throughput = 1 / (10 ns) = 0.1 Gops/sec = 100 Mops/sec

✅ Works if operations are **serialized** and steady.

---

### **Why it usually doesn’t hold in real systems**

1. **Parallelism / concurrency**:

   * If you have 100 operations in flight at once, each taking 10 ns, the throughput is now 100 ops per 10 ns → 10 Gops/sec, but latency per op is still 10 ns.
   * So throughput is **much higher than 1/latency**.

2. **Queuing effects**:

   * If the system gets overloaded, latency per op rises because operations wait in a queue, even if throughput saturates.

3. **Variable operation times**:

   * Some ops are slower than others. Average latency ≠ 1 / throughput.

---

### ✅ Rule of thumb

* You **can use 1/throughput as an approximate latency** only for **single-threaded, perfectly steady workloads**.
* Otherwise, they are related but not inverses. A better mental model is:

**Throughput is approx to (# of concurrent ops)/(latency per op)**

[
\text{Throughput} \approx \frac{\text{# of concurrent ops}}{\text{latency per op}}
]

* “# of concurrent ops” = how many operations the system can handle at once.

---

If you want, I can draw a **tiny diagram showing latency vs throughput for single vs multi-threaded systems**, which makes this very visual. It’s super handy for system design thinking.

Do you want me to make that diagram?
