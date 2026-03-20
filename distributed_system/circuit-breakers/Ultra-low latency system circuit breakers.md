# #Show How circuit breakers are implemented inside high-performance systems (LMAX / trading systems) where latency is microseconds and you cannot afford locks or timeouts.


In **ultra-low latency systems** (like exchanges or HFT platforms), the classic circuit breaker design used in web systems (timeouts, thread pools, retries) is **too slow**.

Systems such as **LMAX Exchange** instead use **lock-free, branch-predictable, nanosecond checks**.

Key principle:

> The circuit breaker must cost **~1–2 CPU instructions** in the fast path.

No locks.
No timers.
No thread pools.

---

# 1. Typical Web Circuit Breaker (Too Slow)

Typical libraries (like **Resilience4j**) do:

```
request
   │
   ├─ timer
   ├─ metrics update
   ├─ rolling window
   └─ synchronization
```

Latency cost:

```
5–50 microseconds
```

For trading systems:

```
budget ≈ 1 microsecond
```

So this is unacceptable.

---

# 2. HFT Circuit Breaker Idea

Instead of tracking statistics continuously, HFT systems use:

```
atomic state + fast timestamp check
```

Core data:

```
state
failureCount
openUntilTimestamp
```

All reads must be **lock-free**.

---

# 3. Minimal Lock-Free Circuit Breaker

```java
import java.util.concurrent.atomic.AtomicInteger;
import java.util.concurrent.atomic.AtomicLong;

public class FastCircuitBreaker {

    private static final int CLOSED = 0;
    private static final int OPEN = 1;

    private final AtomicInteger state = new AtomicInteger(CLOSED);
    private final AtomicInteger failures = new AtomicInteger(0);

    private final AtomicLong openUntil = new AtomicLong(0);

    private final int threshold = 5;
    private final long cooldownNs = 5_000_000_000L; // 5s

    public boolean allowRequest(long now) {

        if (state.get() == OPEN) {
            if (now > openUntil.get()) {
                state.set(CLOSED);
                failures.set(0);
                return true;
            }
            return false;
        }

        return true;
    }

    public void recordFailure(long now) {

        if (failures.incrementAndGet() >= threshold) {
            state.set(OPEN);
            openUntil.set(now + cooldownNs);
        }
    }

    public void recordSuccess() {
        failures.set(0);
    }
}
```

---

# 4. Ultra-Fast Call Path

Critical path:

```java
long now = System.nanoTime();

if (!breaker.allowRequest(now)) {
    return FALLBACK;
}

try {
    service.call();
    breaker.recordSuccess();
} catch (Exception e) {
    breaker.recordFailure(now);
}
```

Hot path when system healthy:

```
1 atomic read
1 branch
```

Cost:

```
~5–20 ns
```

Which is **1000x faster** than typical frameworks.

---

# 5. What Real Trading Systems Do

Real trading systems improve further.

### 1️⃣ No Atomic Writes on Fast Path

Writes only happen on failure.

Healthy path:

```
if (state == CLOSED)
    proceed
```

This avoids cache-line contention.

---

### 2️⃣ Single-Writer Model

Systems inspired by **LMAX Disruptor** avoid atomics entirely.

One thread owns the state.

```
MarketDataThread
      │
      ├─ update breaker state
      │
StrategyThread
      │
      └─ read breaker state
```

Memory barrier ensures visibility.

---

### 3️⃣ Per-Dependency Breakers

Large trading systems maintain breakers for:

```
market data feed
risk engine
exchange gateway
pricing engine
database
```

Example:

```
breaker_marketdata
breaker_risk
breaker_exchange
```

Each check is:

```
if (!breaker_exchange.allow())
    reject order
```

---

# 6. Hardware-Friendly Layout

In extreme low latency, structures are **cache aligned**.

Example:

```
| cache line |
state
failureCount
openUntil
padding
```

Avoids **false sharing** between CPU cores.

---

# 7. Circuit Breakers in Real Trading Architecture

Typical architecture:

```
        Market Feed
             │
             ▼
     MarketData Handler
             │
      (breaker check)
             │
             ▼
        Strategy Engine
             │
      (breaker check)
             │
             ▼
       Risk Engine
             │
      (breaker check)
             │
             ▼
      Exchange Gateway
```

Each stage has its own breaker.

---

# 8. Another Trick: Latency Breakers

Trading systems often break **on latency**, not only failures.

Example:

```
if (latency > 50us)
    open breaker
```

Reason:

A slow service can be **worse than a failed service**.

---

# 9. Extreme HFT Version (Branch-Only)

Fastest form:

```java
if (breakerOpen) {
    return;
}
```

`breakerOpen` is just a **volatile boolean**.

That’s it.

Cost:

```
~1–2 ns
```

---

# 10. Key Philosophy in HFT

Classic microservices thinking:

```
retry
timeout
fallback
```

HFT thinking:

```
fail immediately
protect latency
recover later
```

---

✅ **Rule used in trading systems**

> "If something is slow, treat it as broken."

---

If you'd like, I can also show something **very interesting and rarely explained outside trading firms**:

**How exchanges implement “market-wide circuit breakers” (the ones that halt trading like during crashes).**

These are implemented in **matching engines themselves**, and the design is extremely elegant.
