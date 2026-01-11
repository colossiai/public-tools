# Golang correct usage of context.Background().

In Go, **`context.Background()` is the root, empty context**. The “correct usage” is mostly about **when it is appropriate** to use it—and when it is not.

Below is a practical, production-oriented guide.

---

## What `context.Background()` is

```go
ctx := context.Background()
```

* Never canceled
* Has no deadline
* Has no values
* Safe to use globally
* Usually the **top-level parent context**

Think of it as **`context.TODO()` but intentional**.

---

## Correct places to use `context.Background()`

### 1. **At program entry points**

`main`, initialization code, or bootstrapping logic.

```go
func main() {
    ctx := context.Background()
    app.Run(ctx)
}
```

Why:

* No request lifecycle yet
* Nothing to cancel *from above*

---

### 2. **When creating long-lived services**

Workers, schedulers, background goroutines started at boot.

```go
func StartMetricsCollector() {
    go collect(context.Background())
}
```

Better pattern (preferred):

```go
func StartMetricsCollector(ctx context.Context) {
    go collect(ctx)
}
```

…and pass `Background()` only at the top level.

---

### 3. **In tests (sometimes)**

When cancellation is irrelevant.

```go
func TestParseConfig(t *testing.T) {
    err := LoadConfig(context.Background())
    if err != nil {
        t.Fatal(err)
    }
}
```

---

### 4. **As the root for derived contexts**

This is the most common *correct* usage.

```go
ctx, cancel := context.WithTimeout(context.Background(), 2*time.Second)
defer cancel()
```

---

## Incorrect / discouraged usage

### ❌ Inside request handlers

```go
func handler(w http.ResponseWriter, r *http.Request) {
    doWork(context.Background()) // ❌ WRONG
}
```

Why bad:

* Ignores client cancellation
* Leaks goroutines
* Breaks deadlines

Correct:

```go
func handler(w http.ResponseWriter, r *http.Request) {
    doWork(r.Context()) // ✅
}
```

---

### ❌ Inside library code

```go
func QueryDB() error {
    ctx := context.Background() // ❌
    return db.QueryContext(ctx, ...)
}
```

Why bad:

* Caller cannot cancel
* Violates Go context propagation rule

Correct:

```go
func QueryDB(ctx context.Context) error {
    return db.QueryContext(ctx, ...)
}
```

---

### ❌ Replacing a passed-in context

```go
func Process(ctx context.Context) {
    ctx = context.Background() // ❌ breaks chain
}
```

You **must not discard** the caller’s context.

---

## `context.Background()` vs `context.TODO()`

| Use case                            | Which          |
| ----------------------------------- | -------------- |
| Production, intentional root        | `Background()` |
| Placeholder, unsure what to use yet | `TODO()`       |

Example:

```go
ctx := context.TODO() // temporary during refactor
```

Linters often flag `TODO()` in production code.

---

## Golden rules (memorize these)

1. **Only create `Background()` at the edges**

   * `main`
   * init / bootstrap
2. **Never use it inside request handling**
3. **Never use it inside libraries**
4. **Always accept `context.Context` as the first parameter**
5. **Always propagate the context you receive**

---

## Canonical pattern (idiomatic Go)

```go
func main() {
    ctx, cancel := signal.NotifyContext(context.Background(), os.Interrupt)
    defer cancel()

    run(ctx)
}

func run(ctx context.Context) {
    go worker(ctx)
    <-ctx.Done()
}
```

---

If you want, I can:

* Review your code for context misuse
* Show **anti-patterns that cause goroutine leaks**
* Explain `context.WithValue` best practices (and when *not* to use it)

Just tell me 👍
