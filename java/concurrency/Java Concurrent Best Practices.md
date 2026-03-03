# Show best practices and caveats to use Java concurrent utilities, output in simple list for code Agent demo

Here’s a **concise, code-agent-friendly checklist** of best practices and caveats when using Java concurrent utilities (mainly from `java.util.concurrent`).

---

# ✅ Java Concurrent Utilities – Best Practices

## 1. Prefer High-Level Utilities Over Low-Level Threads

* Use `ExecutorService` instead of manually creating `Thread`
* Use `CompletableFuture` for async pipelines
* Use `BlockingQueue` for producer-consumer
* Use `ConcurrentHashMap` instead of synchronized `HashMap`

---

## 2. Always Use Bounded Thread Pools

❌ Avoid:

```java
Executors.newCachedThreadPool();
Executors.newFixedThreadPool(1000);
```

✅ Prefer:

```java
new ThreadPoolExecutor(
    4, 8,
    60, TimeUnit.SECONDS,
    new ArrayBlockingQueue<>(1000),
    new ThreadPoolExecutor.CallerRunsPolicy()
);
```

Why:

* Prevent OOM
* Prevent unbounded queue growth
* Control backpressure

---

## 3. Always Shutdown Executors Properly

```java
executor.shutdown();
if (!executor.awaitTermination(30, TimeUnit.SECONDS)) {
    executor.shutdownNow();
}
```

Caveat:

* Forgetting shutdown → memory leak
* JVM may not exit

---

## 4. Avoid Blocking Inside Thread Pools

❌ Bad:

```java
executor.submit(() -> future.get());
```

Why:

* Thread starvation
* Deadlocks in small pools

---

## 5. Prefer `ConcurrentHashMap` Atomic APIs

❌ Bad:

```java
if (!map.containsKey(k)) {
    map.put(k, v);
}
```

✅ Good:

```java
map.computeIfAbsent(k, key -> createValue());
```

Why:

* Avoid race condition

---

## 6. Use `CompletableFuture` Carefully

### Prefer async chaining:

```java
CompletableFuture
    .supplyAsync(this::task, executor)
    .thenApply(this::transform)
    .exceptionally(ex -> fallback());
```

Caveats:

* `join()` wraps exception in `CompletionException`
* `get()` throws checked exception
* Default async uses ForkJoinPool.commonPool()

---

## 7. Be Careful with ForkJoinPool

* Designed for CPU-bound tasks
* Avoid blocking IO inside it
* If blocking, use:

```java
ForkJoinPool.managedBlock(...)
```

---

## 8. Avoid Shared Mutable State

❌ Bad:

```java
int counter = 0;
executor.submit(() -> counter++);
```

✅ Use:

```java
AtomicInteger counter = new AtomicInteger();
counter.incrementAndGet();
```

---

## 9. Use Correct Synchronization Primitive

| Scenario         | Use               |
| ---------------- | ----------------- |
| Counter          | AtomicLong        |
| Read-heavy map   | ConcurrentHashMap |
| Limited permits  | Semaphore         |
| Reusable barrier | CyclicBarrier     |
| One-time latch   | CountDownLatch    |
| Coordination     | Phaser            |

---

## 10. Beware of Deadlocks

Common causes:

* Nested locks
* Calling blocking get() inside same pool
* Lock ordering inconsistency

Best practice:

* Define strict lock ordering
* Avoid blocking in synchronized block

---

## 11. Measure Before Optimizing

* Use JMH for benchmarking
* Use async-profiler for contention
* Check:

  * Context switching
  * Lock contention
  * False sharing

---

## 12. Watch for False Sharing

Use:

```java
@Contended
```

(Requires JVM flag: `-XX:-RestrictContended`)

---

## 13. Always Handle RejectedExecutionException

```java
new ThreadPoolExecutor(..., new CallerRunsPolicy());
```

Otherwise:

* Silent task drop
* Production outage

---

## 14. Avoid Oversized Thread Pools

Rule of thumb:

CPU-bound:

```
threads = #cores
```

IO-bound:

```
threads = #cores * (1 + waitTime/computeTime)
```

---

## 15. Don’t Swallow Exceptions

❌ Bad:

```java
executor.submit(() -> {
    try {
        task();
    } catch (Exception ignored) {}
});
```

Why:

* Silent failures
* Hard debugging

---

# ⚠️ Common Production Pitfalls

* Unbounded queue → OOM
* Using commonPool in high-load service
* Blocking inside CompletableFuture
* Forgetting timeout
* Using synchronized instead of concurrent collections
* Not handling interruption
* Using parallelStream in server apps
* Mixing virtual threads (Java 21) incorrectly with blocking pools

---

# 🧠 Golden Rules

1. Always bound resources
2. Never block inside CPU pool
3. Prefer immutable data
4. Always shut down executors
5. Measure before tuning

---

If you want, I can also generate:

* 🔥 A “bad vs good” production-ready template
* 🚀 Low-latency trading system checklist
* 🧪 Concurrency anti-pattern catalog
* 📊 Interview-level deep concurrency notes
