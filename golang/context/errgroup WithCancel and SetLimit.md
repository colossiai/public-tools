# Explain errgroup.SetLimit

`errgroup.SetLimit` is about **putting a hard cap on how many goroutines run at the same time** in an `errgroup.Group`.

Think of it as a built-in **concurrency throttle**.

---

## What `errgroup` does (quick recap)

`golang.org/x/sync/errgroup` helps you:

* run multiple goroutines
* wait for all of them
* return the **first error** (and cancel the rest if you use `WithContext`)

Without a limit, this can easily spin up **hundreds or thousands** of goroutines.

---

## What `SetLimit(n)` means

```go
g.SetLimit(n)
```

👉 **At most `n` goroutines created via `g.Go()` may be running concurrently.**

* If `n > 0` → limit concurrency to `n`
* If `n == 0` → **no goroutines allowed** (every `Go` blocks forever → usually a bug)
* If `n < 0` → **no limit** (default behavior)

---

## Simple example

```go
g := new(errgroup.Group)
g.SetLimit(3)

for i := 0; i < 10; i++ {
    i := i
    g.Go(func() error {
        fmt.Println("start", i)
        time.Sleep(time.Second)
        fmt.Println("end", i)
        return nil
    })
}

_ = g.Wait()
```

### What happens

* Only **3 goroutines run at a time**
* The loop calling `g.Go()` **blocks** once 3 are running
* As soon as one finishes, the next starts

This behaves like a **worker pool**, but without explicit channels.

---

## Important behavior detail (easy to miss ⚠️)

### `SetLimit` blocks at `g.Go`, not inside the goroutine

That means:

```go
for _, item := range items {
    g.Go(func() error {
        // work
        return nil
    })
}
```

If the limit is hit, the **loop itself pauses** until a slot frees up.

This is usually what you want — but it surprises people expecting all goroutines to be “queued”.

---

## With `WithContext` (very common)

```go
ctx, cancel := context.WithCancel(context.Background())
defer cancel()

g, ctx := errgroup.WithContext(ctx)
g.SetLimit(5)

for _, url := range urls {
    url := url
    g.Go(func() error {
        req, _ := http.NewRequestWithContext(ctx, "GET", url, nil)
        resp, err := http.DefaultClient.Do(req)
        if err != nil {
            return err
        }
        resp.Body.Close()
        return nil
    })
}

if err := g.Wait(); err != nil {
    log.Fatal(err)
}
```

### What you get

* Max **5 concurrent HTTP requests**
* First error:

  * cancels the context
  * remaining goroutines stop early (if they respect `ctx`)

---

## How it’s implemented (mental model)

Internally, `SetLimit(n)` uses a **semaphore**:

* `g.Go()` → acquire token
* goroutine exits → release token

No token → `Go()` waits.

---

## When you should use `SetLimit`

✅ Great for:

* HTTP / RPC fan-out
* DB queries
* File IO
* Calling third-party APIs
* Any “loop + goroutine” pattern

❌ Not ideal when:

* You need priority scheduling
* You need dynamic resizing (use a worker pool instead)

---

## Common pitfalls

### 1. `SetLimit(0)`

```go
g.SetLimit(0) // ❌ deadlock
```

This blocks forever.

---

### 2. Calling `SetLimit` after `Go`

```go
g.Go(fn)
g.SetLimit(5) // ❌ panic
```

`SetLimit` **must be called before** any `Go`.

---

### 3. Forgetting that `Go` can block

If you do expensive work **before** calling `g.Go`, concurrency control won’t help you.

---

## TL;DR

* `SetLimit(n)` = **max N concurrent goroutines**
* Blocks at `g.Go()`, not in the goroutine
* Works like a semaphore
* Perfect for safe fan-out without writing a worker pool

If you want, I can compare `errgroup.SetLimit` vs a **channel-based worker pool** or vs **semaphore.Weighted** and show when each one wins.


# In the WithContext() example, why first error will cancels the context?

Great question — this is **by design**, not magic.

Short answer first, then the mechanics.

---

## Short answer

`errgroup.WithContext()` is explicitly designed so that:

> **The first goroutine that returns a non-nil error cancels the shared context**, signaling all other goroutines to stop early.

This makes *fan-out + fail-fast* easy and safe.

---

## Where the cancellation comes from

When you call:

```go
g, ctx := errgroup.WithContext(parentCtx)
```

internally, errgroup does roughly this (simplified):

```go
ctx, cancel := context.WithCancel(parentCtx)

g := &Group{
    cancel: cancel,
}
```

Then, every time a goroutine finishes:

```go
if err != nil {
    g.errOnce.Do(func() {
        g.err = err
        cancel()   // 👈 THIS is the key
    })
}
```

So:

* the **first** non-nil error:

  * is recorded
  * triggers `cancel()`
* subsequent errors are ignored
* `g.Wait()` returns that first error

---

## Why cancel the context?

Because in most concurrent fan-out scenarios:

* Once **one task fails**, the rest of the work is often:

  * useless
  * expensive
  * or even dangerous (duplicate writes, partial state, etc.)

Canceling the context gives you a **clean, cooperative shutdown signal**.

---

## What “canceling the context” actually does

Context cancellation does **not** kill goroutines.

It only:

* closes `ctx.Done()`
* makes `ctx.Err()` return `context.Canceled`

Each goroutine must **opt in** by checking or passing the context along.

Example:

```go
g.Go(func() error {
    select {
    case <-ctx.Done():
        return ctx.Err() // exit early
    default:
        // do work
    }
})
```

Or more commonly, pass `ctx` into APIs that respect it:

```go
http.NewRequestWithContext(ctx, ...)
db.QueryContext(ctx, ...)
```

---

## What if errgroup didn’t cancel?

Imagine 100 HTTP calls:

* call #3 fails immediately
* calls #4–#100 keep running
* you:

  * waste bandwidth
  * waste CPU
  * maybe overload a dependency

You’d then need **extra coordination code** to stop the rest.

`WithContext()` bakes this pattern in.

---

## Why not always cancel in `Group` (without context)?

Because cancellation only makes sense if:

* you *have* a context
* your work knows how to stop cooperatively

That’s why errgroup has **two variants**:

| API                      | Behavior                        |
| ------------------------ | ------------------------------- |
| `new(errgroup.Group)`    | Collect errors, no cancellation |
| `errgroup.WithContext()` | Fail-fast + cancel signal       |

You choose.

---

## Common misunderstanding ⚠️

> “errgroup kills my goroutines”

❌ False
✔️ errgroup **signals** cancellation; goroutines must listen.

If a goroutine ignores `ctx`, it will keep running.

---

## Mental model

Think of `errgroup.WithContext()` as:

> “Run these tasks in parallel.
> If *any one* fails, tell the rest to stop ASAP.”

---

## When you *shouldn’t* rely on this

* Cleanup tasks that must always finish
* Fire-and-forget background jobs
* Tasks that are not cancel-safe

In those cases:

* use `errgroup.Group` without context
* or create separate contexts per task

---

### TL;DR

* `WithContext()` wraps a `context.WithCancel`
* First non-nil error calls `cancel()`
* Cancellation is a **signal**, not a kill switch
* This enables **fail-fast fan-out** with minimal code

If you want, I can show:

* a minimal reproduction using `ctx.Done()`
* or compare this with `WaitGroup + context` side-by-side 👀
