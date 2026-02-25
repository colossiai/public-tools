# which timeout ctx usage is correct

```go

// snippet1
	for {
		time.Sleep(10 * time.Second)

		ctxTimeout, cancel := context.WithTimeout(context.Background(), time.Second*5)
		if err := c.refresh(ctxTimeout, false); err != nil {
			ulog.Errorf("cache refresh failed: %v\n", err)
		}
		cancel()
	}


// snippet2
    ctxTimeout, cancel := context.WithTimeout(context.Background(), time.Second*5)
    defer cancel()

	for {
		time.Sleep(10 * time.Second)

		if err := c.refresh(ctxTimeout, false); err != nil {
			ulog.Errorf("cache refresh failed: %v\n", err)
		}
	}    
```


-- SOLUTION:


**Snippet 1 is correct. Snippet 2 is wrong**, just in a quieter, sneakier way.

---

## Snippet 1 (👍 correct)

```go
for {
    time.Sleep(10 * time.Second)

    ctxTimeout, cancel := context.WithTimeout(context.Background(), time.Second*5)
    if err := c.refresh(ctxTimeout, false); err != nil {
        ulog.Errorf("cache refresh failed: %v\n", err)
    }
    cancel()
}
```

Why this is good:

* New context **per iteration**
* Fresh 5-second deadline **every time**
* `cancel()` is called promptly → no timer/goroutine leaks
* Each `refresh` gets a valid context

This is idiomatic Go.

---

## Snippet 2 (👎 still wrong)

```go
ctxTimeout, cancel := context.WithTimeout(context.Background(), time.Second*5)
defer cancel()

for {
    time.Sleep(10 * time.Second)

    if err := c.refresh(ctxTimeout, false); err != nil {
        ulog.Errorf("cache refresh failed: %v\n", err)
    }
}
```

Why this fails:

### 1. The timeout only applies once

`context.WithTimeout(..., 5*time.Second)` starts the clock **immediately**.

After 5 seconds:

* `ctxTimeout` is **done**
* `ctxTimeout.Err()` becomes `context.DeadlineExceeded`
* It **never recovers**

But your loop keeps running every 10 seconds, reusing that same dead context.

### 2. `defer cancel()` doesn’t save you here

`defer cancel()` only runs when the surrounding function returns — not per loop iteration.

So effectively:

* First iteration *might* work (if it runs within the first 5 seconds)
* Every iteration after that gets an already-expired context

---

## Mental model that helps

Think of a context like a **single-use coupon** 🧾

* Once it expires or is canceled, it’s trash
* You cannot “reset” or “reuse” it
* `defer cancel()` is about **cleanup**, not reuse

---

## If you want `defer cancel()`, do this instead

```go
for {
    time.Sleep(10 * time.Second)

    func() {
        ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
        defer cancel()

        if err := c.refresh(ctx, false); err != nil {
            ulog.Errorf("cache refresh failed: %v\n", err)
        }
    }()
}
```

This way:

* New context per iteration
* `defer cancel()` runs at the end of *each* loop pass
* Safe, clean, idiomatic

---

### Bottom line

* ✅ Context creation **inside the loop**
* ❌ Context reuse **across loop iterations**
* ❌ Expecting `defer cancel()` to reset timeouts

If you want, I can also show:

* the `time.Ticker` version
* how this behaves under slow `refresh`
* how to wire this to a parent shutdown context

Just poke me 👋
