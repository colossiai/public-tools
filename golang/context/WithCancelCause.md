# Show how to use context.WithCancelCause


`context.WithCancelCause` (Go 1.20+) lets you **cancel a context with a specific error cause**, so downstream code can distinguish *why* it was canceled (timeout vs manual vs business error).

Below are **practical, idiomatic patterns** you’ll actually use in Go services.

---

## 1. Basic usage

```go
ctx, cancel := context.WithCancelCause(context.Background())
defer cancel(nil) // safe: nil means "no specific cause"
```

Cancel with a cause:

```go
cancel(errors.New("upstream service returned 503"))
```

Retrieve the cause:

```go
err := context.Cause(ctx)
```

---

## 2. Difference vs `context.WithCancel`

| Feature               | WithCancel                 | WithCancelCause                  |
| --------------------- | -------------------------- | -------------------------------- |
| Cancel signal         | yes                        | yes                              |
| Reason / error        | ❌ no                       | ✅ yes                            |
| Works with ctx.Done() | ✅                          | ✅                                |
| Works with ctx.Err()  | returns `context.Canceled` | still returns `context.Canceled` |

👉 **Important:**

* `ctx.Err()` **does NOT return the cause**
* You must call `context.Cause(ctx)`

---

## 3. Worker goroutine propagating a real failure

This is the **most common correct use case**.

```go
func worker(ctx context.Context) error {
	select {
	case <-time.After(200 * time.Millisecond):
		return errors.New("database connection lost")
	case <-ctx.Done():
		return context.Cause(ctx)
	}
}

func main() {
	ctx, cancel := context.WithCancelCause(context.Background())
	defer cancel(nil)

	go func() {
		if err := worker(ctx); err != nil {
			cancel(err) // propagate real failure
		}
	}()

	<-ctx.Done()

	fmt.Println("ctx.Err():", ctx.Err())
	fmt.Println("cause:", context.Cause(ctx))
}
```

**Output**

```
ctx.Err(): context canceled
cause: database connection lost
```

---

## 4. Coordinating multiple goroutines (first error wins)

Classic fan-out / fan-in pattern.

```go
func runTask(ctx context.Context, id int) error {
	if id == 2 {
		return errors.New("task 2 failed")
	}
	time.Sleep(500 * time.Millisecond)
	return nil
}

func main() {
	ctx, cancel := context.WithCancelCause(context.Background())
	defer cancel(nil)

	for i := 1; i <= 3; i++ {
		go func(id int) {
			if err := runTask(ctx, id); err != nil {
				cancel(err) // first call wins
			}
		}(i)
	}

	<-ctx.Done()
	fmt.Println("cause:", context.Cause(ctx))
}
```

✔ Only the **first cancel cause is kept**
✔ Subsequent `cancel(err)` calls are ignored

---

## 5. Combining with timeout / deadline

Timeout still works, but now you can tell *why* it ended.

```go
parent := context.Background()

ctx, cancel := context.WithTimeoutCause(
	parent,
	100*time.Millisecond,
	errors.New("operation timed out"),
)
defer cancel(nil)

<-ctx.Done()

fmt.Println("Err():", ctx.Err())              // context deadline exceeded
fmt.Println("Cause():", context.Cause(ctx))  // operation timed out
```

---

## 6. HTTP handler example (very useful in servers)

```go
func handler(w http.ResponseWriter, r *http.Request) {
	ctx, cancel := context.WithCancelCause(r.Context())
	defer cancel(nil)

	go func() {
		err := doBusinessLogic(ctx)
		if err != nil {
			cancel(err)
		}
	}()

	<-ctx.Done()

	if cause := context.Cause(ctx); cause != nil {
		http.Error(w, cause.Error(), http.StatusInternalServerError)
		return
	}

	w.WriteHeader(http.StatusOK)
}
```

---

## 7. Rules & gotchas (important)

### ✅ DO

* Use **one cancel owner**
* Pass ctx downstream normally
* Call `context.Cause(ctx)` to inspect reason

### ❌ DON’T

* Expect `ctx.Err()` to contain your error
* Wrap causes repeatedly
* Use for normal success paths

---

## 8. When should *you* use it?

Given you work on **Go backend systems / APIs**, use `WithCancelCause` when:

✔ You need **error propagation across goroutines**
✔ You want **structured cancellation reasons**
✔ You’re coordinating parallel tasks (fan-out)
✔ You want better observability/logging

If you want, I can also show:

* `errgroup` + `WithCancelCause`
* How to log causes cleanly
* How to map causes to API error codes
* Migration from `WithCancel` → `WithCancelCause`

Just tell me.
