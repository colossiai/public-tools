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
