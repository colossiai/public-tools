# can golang context be reused in multi function calls?, like

```go
ctx, cancel := context.WithTimeout(context.Background(), time.Second*10)
defer cancel()

call_a(ctx)
call_b(ctx)
```


## SOLUTION:

Yep — that’s not just allowed, it’s *exactly* how `context.Context` is meant to be used 👍

Your example is idiomatic Go:

```go
ctx, cancel := context.WithTimeout(context.Background(), 10*time.Second)
defer cancel()

callA(ctx)
callB(ctx)
```

### How this works (and why it’s safe)

* A `context.Context` is **immutable** and **thread-safe**
* You can pass the *same* context to **multiple functions**
* All functions share:

  * the same deadline / timeout
  * the same cancellation signal
  * the same values stored in the context

So when:

* the 10 seconds expire **or**
* `cancel()` is called

👉 **both `callA` and `callB` will see `ctx.Done()` close**

---

### Very common real-world pattern

This is *the* standard pattern for request-scoped work:

```go
func handler(w http.ResponseWriter, r *http.Request) {
    ctx, cancel := context.WithTimeout(r.Context(), 10*time.Second)
    defer cancel()

    if err := callA(ctx); err != nil {
        return
    }
    if err := callB(ctx); err != nil {
        return
    }
}
```

Or concurrently:

```go
go callA(ctx)
go callB(ctx)
```

Still totally fine.

---

### One important rule to remember

> **Only the owner of the context should cancel it**

Meaning:

* The function that *creates* the context calls `cancel()`
* `callA` and `callB` should **never** call `cancel()`
* They should only *observe* it:

```go
select {
case <-ctx.Done():
    return ctx.Err()
default:
    // do work
}
```

---

### When you *shouldn’t* reuse a context

Don’t reuse a context if:

* the operations have **different lifetimes**
* one should be cancellable without killing the other

In that case, derive child contexts:

```go
ctxA, cancelA := context.WithTimeout(ctx, 2*time.Second)
defer cancelA()

ctxB, cancelB := context.WithTimeout(ctx, 5*time.Second)
defer cancelB()
```

---

### TL;DR

* ✅ Reusing a context across multiple function calls is correct
* ✅ Reusing it across goroutines is correct
* ❌ Don’t cancel a context you didn’t create
* ❌ Don’t use context as a bag of optional parameters

If you want, I can also show:

* common context anti-patterns
* how `WithCancelCause` fits in
* or how this behaves with HTTP / database calls

Just say the word 😄

# in the above example, if callA() cost time 8 seconds, callB cost time 7 seconds (which is total 15 seconds), and ctx is only with timeout = 10 seconds, will callB() be time-outed?


Yes — **`callB()` will time out** in that scenario.

Let’s walk it through step by step, because the timing detail matters ⏱️

---

### Timeline with your example

```go
ctx, cancel := context.WithTimeout(context.Background(), 10*time.Second)
defer cancel()

callA(ctx) // takes ~8s
callB(ctx) // takes ~7s
```

**What happens:**

* `t = 0s` → context created, 10s deadline starts
* `t = 8s` → `callA` finishes
* `t = 8s` → `callB` starts
* `t = 10s` → context deadline exceeded
* `t = 10–15s` → `callB` is running *with a canceled context*

So yes: **`callB` will see `ctx.Done()` close about 2 seconds after it starts**.

---

### What `callB` actually experiences

That depends on whether `callB` *respects* the context.

#### If `callB` checks the context (good citizen):

```go
func callB(ctx context.Context) error {
    select {
    case <-time.After(7 * time.Second):
        return nil
    case <-ctx.Done():
        return ctx.Err() // context deadline exceeded
    }
}
```

➡️ `callB` exits early at ~2 seconds with
`context deadline exceeded`

---

#### If `callB` ignores the context (bad citizen 😅):

```go
func callB(ctx context.Context) {
    time.Sleep(7 * time.Second)
}
```

➡️ **Nothing stops it**

* The context times out
* But `callB` keeps running anyway
* You only *know* it timed out if you check `ctx.Err()`

Contexts are **cooperative**, not forceful.

---

### Key takeaway

> A context timeout is **absolute**, not “per function call”

It starts counting down the moment it’s created — not when each function begins.

---

### If you want 10 seconds *per call*

You need **separate child contexts**:

```go
callA := func(parent context.Context) error {
    ctx, cancel := context.WithTimeout(parent, 10*time.Second)
    defer cancel()
    return doA(ctx)
}

callB := func(parent context.Context) error {
    ctx, cancel := context.WithTimeout(parent, 10*time.Second)
    defer cancel()
    return doB(ctx)
}
```

Or inline:

```go
ctxA, cancelA := context.WithTimeout(ctx, 10*time.Second)
defer cancelA()
callA(ctxA)

ctxB, cancelB := context.WithTimeout(ctx, 10*time.Second)
defer cancelB()
callB(ctxB)
```

---

### One-liner mental model

* **One context = one shared deadline**
* Sequential work eats into the same clock
* Concurrency shares the same cancel signal

If you want, I can also show:

* how this behaves when `callA`/`callB` run in goroutines
* how to log *how much time is left* using `ctx.Deadline()`
* or a quick rule-of-thumb for structuring timeouts cleanly

Just tell me 👍
