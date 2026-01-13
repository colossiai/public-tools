# How to properly use context.WithCancel

In Go, `context.WithCancel` is used to **signal cancellation** to one or more goroutines that are doing work derived from a parent context. The key idea is: **the caller who creates the context owns its cancellation**.

Below is the *proper* way to use it, including common patterns and pitfalls.

---

## 1. Basic pattern (canonical)

```go
ctx, cancel := context.WithCancel(context.Background())
defer cancel() // always call cancel to release resources

go worker(ctx)

// later…
cancel()
```

What happens:

* `ctx.Done()` is closed when `cancel()` is called
* All goroutines using `ctx` should stop promptly

---

## 2. How a goroutine should respect cancellation

Every goroutine **must actively listen** to `ctx.Done()`.

```go
func worker(ctx context.Context) {
	for {
		select {
		case <-ctx.Done():
			// Cleanup if needed
			return
		default:
			// Do work
			time.Sleep(100 * time.Millisecond)
		}
	}
}
```

For blocking calls, always prefer context-aware APIs:

* `http.NewRequestWithContext`
* `db.QueryContext`
* `select { case <-ctx.Done(): ... }`

---

## 3. Correct ownership rule (very important)

> **The function that calls `WithCancel` must call `cancel()`**

❌ **Wrong** (callee cancels caller’s context):

```go
func bad(ctx context.Context) {
	ctx, cancel := context.WithCancel(ctx)
	cancel() // ❌ cancels parent's work unexpectedly
}
```

✅ **Correct**:

```go
func good(parent context.Context) (context.Context, context.CancelFunc) {
	return context.WithCancel(parent)
}
```

Caller decides *when* to cancel.

---

## 4. Using `WithCancel` to stop multiple goroutines

```go
ctx, cancel := context.WithCancel(context.Background())

for i := 0; i < 3; i++ {
	go func(id int) {
		for {
			select {
			case <-ctx.Done():
				fmt.Println("worker", id, "stopped")
				return
			default:
				time.Sleep(time.Second)
			}
		}
	}(i)
}

time.Sleep(3 * time.Second)
cancel()
```

All workers stop simultaneously.

---

## 5. `WithCancel` vs `WithTimeout` vs `WithDeadline`

| Function       | Use when                              |
| -------------- | ------------------------------------- |
| `WithCancel`   | Manual cancellation (lifecycle-based) |
| `WithTimeout`  | Max execution time                    |
| `WithDeadline` | Stop at fixed time                    |

Internally, `WithTimeout` and `WithDeadline` **use `WithCancel`**.

```go
ctx, cancel := context.WithTimeout(ctx, 2*time.Second)
defer cancel()
```

---

## 6. HTTP server example (real-world correct usage)

```go
func handler(w http.ResponseWriter, r *http.Request) {
	ctx := r.Context() // already cancellable

	result, err := doWork(ctx)
	if err != nil {
		http.Error(w, err.Error(), 499)
		return
	}
	w.Write([]byte(result))
}
```

Client disconnect → `ctx.Done()` fires automatically.

---

## 7. Avoid common mistakes

### ❌ Forgetting to call `cancel()`

Leads to **context leaks** (timers, goroutines).

```go
ctx, _ := context.WithCancel(context.Background()) // ❌
```

Always:

```go
ctx, cancel := context.WithCancel(...)
defer cancel()
```

---

### ❌ Storing context in structs

```go
type Service struct {
	ctx context.Context // ❌
}
```

Context should be **request-scoped**, passed explicitly.

---

### ❌ Using context for optional data

Context is **not** for:

* config
* auth models
* business objects

Only:

* cancellation
* deadlines
* request-scoped metadata

---

## 8. When you should use `WithCancel`

Use it when:

* You spawn goroutines that must stop together
* You need early-exit on error
* You manage lifecycle (stream, watcher, worker pool)
* You want cooperative cancellation

Example: stop workers on first error

```go
ctx, cancel := context.WithCancel(context.Background())
defer cancel()

if err := runA(ctx); err != nil {
	cancel()
}
```

---

## Mental model (remember this)

* `context.Context` is **read-only**
* `CancelFunc` is **write-only**
* Parent controls child
* Cancellation is **broadcast**, not forced

---

If you want, I can also show:

* `errgroup.WithContext` (preferred in many cases)
* cancellation-safe worker pools
* context usage patterns for gRPC / HTTP / DB
* how Go’s context tree actually works internally

Just tell me 👍
