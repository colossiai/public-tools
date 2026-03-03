# Show usage of Java CompletableFuture and its caveats


Alright, let’s demystify **`CompletableFuture`**—it’s powerful, elegant, and *very easy to misuse* if you don’t know the sharp edges 😄

---

## Basic usage

### Creating and running asynchronously

```java
CompletableFuture<String> future =
    CompletableFuture.supplyAsync(() -> {
        // runs in another thread
        return "Hello";
    });

String result = future.join(); // blocks until done
System.out.println(result);
```

* `supplyAsync` → returns a value
* `runAsync` → no return value (`CompletableFuture<Void>`)

---

## Chaining computations

### `thenApply` (transform result)

```java
CompletableFuture<Integer> lengthFuture =
    CompletableFuture.supplyAsync(() -> "Hello")
                     .thenApply(String::length);

System.out.println(lengthFuture.join()); // 5
```

Runs **after** the previous stage completes, using the previous result.

---

### `thenAccept` (consume result, no return)

```java
CompletableFuture<Void> future =
    CompletableFuture.supplyAsync(() -> "Hello")
                     .thenAccept(s -> System.out.println(s));
```

---

### `thenRun` (ignore result)

```java
CompletableFuture<Void> future =
    CompletableFuture.supplyAsync(() -> "Hello")
                     .thenRun(() -> System.out.println("Done"));
```

---

## Composing async tasks

### `thenCompose` (flatMap for futures)

Use this when the next step is **also async**.

```java
CompletableFuture<String> future =
    CompletableFuture.supplyAsync(() -> "userId-123")
                     .thenCompose(id ->
                         CompletableFuture.supplyAsync(() -> "User:" + id)
                     );

System.out.println(future.join());
```

👉 **Rule of thumb**

* `thenApply` → returns a value
* `thenCompose` → returns another `CompletableFuture`

---

## Combining multiple futures

### `thenCombine`

```java
CompletableFuture<Integer> f1 =
    CompletableFuture.supplyAsync(() -> 10);
CompletableFuture<Integer> f2 =
    CompletableFuture.supplyAsync(() -> 20);

CompletableFuture<Integer> combined =
    f1.thenCombine(f2, Integer::sum);

System.out.println(combined.join()); // 30
```

---

### `allOf` and `anyOf`

```java
CompletableFuture<Void> all =
    CompletableFuture.allOf(f1, f2);

all.join(); // wait for all to complete
```

⚠️ `allOf` **loses type information**—you must extract results manually.

---

## Exception handling

### `exceptionally`

```java
CompletableFuture<String> future =
    CompletableFuture.supplyAsync(() -> {
        throw new RuntimeException("Boom");
    }).exceptionally(ex -> "Fallback");

System.out.println(future.join()); // Fallback
```

---

### `handle` (success or failure)

```java
CompletableFuture<String> future =
    CompletableFuture.supplyAsync(() -> "OK")
                     .handle((result, ex) ->
                         ex == null ? result : "Recovered"
                     );
```

---

### `whenComplete` (side effects only)

```java
future.whenComplete((result, ex) -> {
    if (ex != null) ex.printStackTrace();
});
```

Does **not** change the result.

---

## Using a custom Executor

```java
ExecutorService executor = Executors.newFixedThreadPool(4);

CompletableFuture<String> future =
    CompletableFuture.supplyAsync(() -> "Hello", executor);
```

This matters **a lot**—see caveats below 👇

---

## Blocking (use sparingly!)

```java
future.get();   // checked exceptions
future.join();  // unchecked CompletionException
```

Prefer `join()` in async-heavy code.

---

# Common caveats (the “gotchas”)

### 1. **ForkJoinPool starvation**

By default, `supplyAsync()` uses the **common ForkJoinPool**.

🚨 Problem:

```java
CompletableFuture.supplyAsync(() -> {
    Thread.sleep(5000); // blocking call
    return "oops";
});
```

Blocking I/O here can **starve the pool** and freeze unrelated tasks.

✅ Fix: use a dedicated executor for blocking work.

---

### 2. **Async methods aren’t always async**

```java
thenApply(...)
thenAccept(...)
thenRun(...)
```

These may run **on the same thread** that completed the previous stage.

If you want guaranteed async execution:

```java
thenApplyAsync(...)
thenAcceptAsync(...)
```

(with or without a custom executor)

---

### 3. **Exception wrapping is confusing**

Exceptions are wrapped in `CompletionException`.

```java
try {
    future.join();
} catch (CompletionException e) {
    Throwable root = e.getCause();
}
```

If you don’t unwrap, debugging becomes painful.

---

### 4. **allOf() drops types**

```java
CompletableFuture.allOf(f1, f2)
```

You must do this:

```java
CompletableFuture<List<Integer>> result =
    CompletableFuture.allOf(f1, f2)
        .thenApply(v -> List.of(f1.join(), f2.join()));
```

This is awkward and easy to mess up.

---

### 5. **Hard to cancel correctly**

Calling `cancel(true)`:

* does **not** interrupt running tasks reliably
* does **not** stop dependent stages

Cancellation is cooperative, not enforced.

---

### 6. **Silent failures**

If no one calls `join()`, `get()`, or attaches an error handler, exceptions can disappear.

```java
CompletableFuture.runAsync(() -> {
    throw new RuntimeException("Lost forever");
});
```

Always attach error handling in production code.

---

### 7. **Not a replacement for reactive frameworks**

For:

* streaming data
* backpressure
* long-lived async pipelines

`CompletableFuture` becomes awkward fast. It’s best for **finite async workflows**, not streams.

---

## When `CompletableFuture` shines

✅ Parallel I/O calls
✅ Async service orchestration
✅ Fan-out / fan-in workflows
✅ Replacing nested callbacks

## When to be cautious

⚠ Blocking operations
⚠ Deeply nested chains
⚠ Complex error propagation
⚠ High-throughput reactive systems

---

If you want, I can:

* refactor a real-world blocking example into a safe `CompletableFuture` version
* compare it with **ExecutorService + Futures**
* or show **anti-patterns** I see in production code all the time 😈


# compare it with ExecutorService + Futures

Great question 👍 — this is exactly where many Java concurrency designs go wrong.

Let’s compare:

* `ExecutorService + Future`
* `CompletableFuture`

---

# 1️⃣ Mental Model Difference

| ExecutorService + Future | CompletableFuture           |
| ------------------------ | --------------------------- |
| “Submit and block later” | “Build async pipeline”      |
| Pull model (`get()`)     | Push/composition model      |
| Manual coordination      | Declarative chaining        |
| Limited composition      | Rich functional composition |

---

# 2️⃣ Basic Example Comparison

## 🧱 With `ExecutorService + Future`

```java
ExecutorService pool = Executors.newFixedThreadPool(4);

Future<String> f1 = pool.submit(() -> {
    Thread.sleep(100);
    return "Hello";
});

Future<String> f2 = pool.submit(() -> {
    Thread.sleep(100);
    return "World";
});

String result = f1.get() + " " + f2.get();
System.out.println(result);

pool.shutdown();
```

### Problems:

* `get()` blocks
* No easy composition
* Manual orchestration
* Exceptions are checked

---

## ⚡ With `CompletableFuture`

```java
ExecutorService pool = Executors.newFixedThreadPool(4);

CompletableFuture<String> f1 =
    CompletableFuture.supplyAsync(() -> "Hello", pool);

CompletableFuture<String> f2 =
    CompletableFuture.supplyAsync(() -> "World", pool);

CompletableFuture<String> combined =
    f1.thenCombine(f2, (a, b) -> a + " " + b);

System.out.println(combined.join());

pool.shutdown();
```

### Benefits:

* Non-blocking composition
* Cleaner orchestration
* Built-in combinators

---

# 3️⃣ Composition Power

## With `Future`

There is **no built-in way** to:

* run something after completion
* combine two results
* recover from error inline
* chain async calls

You must manually:

```java
Future<String> f = pool.submit(task);

String result = f.get();   // block
String transformed = result.toUpperCase();
```

Everything becomes sequential.

---

## With `CompletableFuture`

```java
CompletableFuture.supplyAsync(() -> "hello")
    .thenApply(String::toUpperCase)
    .thenAccept(System.out::println);
```

This is functional composition, similar to:

* Java Streams
* Promises in JS
* async/await pipeline

---

# 4️⃣ Exception Handling

## `Future`

```java
try {
    f.get();
} catch (ExecutionException e) {
    Throwable cause = e.getCause();
}
```

* Checked exceptions
* Must handle at blocking point
* No inline recovery

---

## `CompletableFuture`

```java
CompletableFuture.supplyAsync(() -> {
    throw new RuntimeException();
}).exceptionally(ex -> "fallback");
```

Inline recovery. Much cleaner.

---

# 5️⃣ Parallel Fan-out / Fan-in

## With `Future`

```java
List<Future<String>> futures = tasks.stream()
    .map(task -> pool.submit(task))
    .toList();

for (Future<String> f : futures) {
    System.out.println(f.get()); // sequential blocking
}
```

Sequential waiting even if tasks finish out of order.

---

## With `CompletableFuture`

```java
List<CompletableFuture<String>> futures = tasks.stream()
    .map(task -> CompletableFuture.supplyAsync(task))
    .toList();

CompletableFuture.allOf(
    futures.toArray(new CompletableFuture[0])
).join();
```

Non-blocking coordination.

---

# 6️⃣ Cancellation

Both are limited:

* `Future.cancel(true)` may interrupt thread
* `CompletableFuture.cancel(true)` does NOT reliably interrupt

Neither is ideal for structured cancellation.

(Java 21 `StructuredTaskScope` is better, but that’s another topic.)

---

# 7️⃣ Performance Characteristics

| Aspect              | Future        | CompletableFuture       |
| ------------------- | ------------- | ----------------------- |
| Allocation overhead | Lower         | Slightly higher         |
| Thread usage        | Explicit pool | Common pool by default  |
| Blocking risk       | High          | Lower if used correctly |
| Learning curve      | Low           | Moderate                |

In high-frequency trading / low-latency systems (which you seem interested in from your JMH + Aeron questions), `CompletableFuture` may introduce:

* More allocation
* More object graph
* More GC pressure

For ultra-low latency code, plain executors or even manual ring buffers are often preferred.

---

# 8️⃣ When to Use Which?

## Use `ExecutorService + Future` when:

* You just need to submit tasks
* You plan to block anyway
* You want minimal abstraction
* You are in low-level infrastructure code

---

## Use `CompletableFuture` when:

* You are orchestrating multiple async calls
* You need chaining
* You need composition
* You are writing service-layer async logic
* You want clean error pipelines

---

# 9️⃣ Common Production Anti-pattern

### ❌ Worst of both worlds

```java
CompletableFuture<String> f =
    CompletableFuture.supplyAsync(() -> blockingCall());

return f.get();  // immediately block
```

You:

* switch thread
* allocate extra objects
* then block anyway

Just call the method directly or use `ExecutorService`.

---

# 🔟 Architectural Insight (Important)

`Future` is:

> A handle to a running task.

`CompletableFuture` is:

> A programmable promise representing a future result.

That’s a fundamental abstraction upgrade.

---

If you want, I can next:

* Compare with **Project Loom virtual threads**
* Show structured concurrency vs CompletableFuture
* Or analyze which is better for a low-latency trading bot scenario (since you’ve been benchmarking concurrency recently)
