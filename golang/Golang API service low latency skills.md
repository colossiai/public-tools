# Golang API service low latency skills

For a **Golang API service with low-latency goals**, think in layers: **design → runtime → IO → memory → observability**. Below is a **practical, production-oriented skill checklist**, tailored to backend API work like you’ve been doing with **Gin, GORM, typed config, and clean architecture**.

---

## 1. API & Architecture Design (Biggest Wins)

### 🔹 Keep the hot path small

* Minimize work per request
* Avoid unnecessary abstraction in handlers
* Push non-critical work async (events, logging, metrics)

### 🔹 Clean separation (but not over-abstracted)

* Handler → Service → Repo
* **No reflection or interface indirection in hot paths unless justified**

### 🔹 Error design

* Treat **business errors vs system errors** differently
  (you already noticed this with `gorm.ErrRecordNotFound`)
* Avoid wrapping errors excessively in request path

---

## 2. HTTP & Gin Optimization

### 🔹 Gin-specific skills

* Use `gin.ReleaseMode`
* Avoid `c.ShouldBindJSON()` in ultra-hot paths → use:

  ```go
  json.NewDecoder(c.Request.Body).Decode(&req)
  ```
* Avoid per-request allocations in middleware

### 🔹 Middleware discipline

* Order matters:

  ```
  Recovery → Metrics → Auth → Business
  ```
* Skip middleware when not needed:

  ```go
  r.GET("/health", healthHandler) // no auth, no DB
  ```

---

## 3. Concurrency & Goroutines

### 🔹 Master goroutine cost

* Goroutines are cheap, **not free**
* Avoid spawning goroutines per request unless IO-bound

### 🔹 Correct use of pools

* `sync.Pool` for:

  * request buffers
  * JSON temp structs
* **Never store request-scoped state permanently**

```go
var bufPool = sync.Pool{
    New: func() any { return make([]byte, 0, 4096) },
}
```

---

## 4. Memory & Allocation Control (Critical for Latency)

### 🔹 Reduce allocations

* Prefer:

  * `[]T` over `[]*T` (you asked this for GORM)
  * stack structs over heap pointers
* Pre-allocate slices:

  ```go
  items := make([]Item, 0, 32)
  ```

### 🔹 Escape analysis awareness

* Avoid returning pointers to local variables
* Use:

  ```bash
  go build -gcflags="-m"
  ```

---

## 5. JSON & Serialization

### 🔹 Choose fast JSON when needed

* `encoding/json` → safe default
* Consider:

  * `jsoniter`
  * `sonic` (very fast, but stricter)

### 🔹 Avoid map[string]interface{}

* Use **typed structs**
* Pre-define response structs

---

## 6. Database & IO Latency (Often the Real Bottleneck)

### 🔹 SQL / GORM best practices

* Always:

  * limit columns (`Select`)
  * use indexes
* Avoid:

  * `Preload` in hot paths
  * N+1 queries

### 🔹 Connection pool tuning

```go
db.SetMaxOpenConns(50)
db.SetMaxIdleConns(50)
db.SetConnMaxLifetime(5 * time.Minute)
```

### 🔹 Cache aggressively

* Read-through cache (Redis / in-memory)
* Cache **negative results** (e.g. not found)

---

## 7. Configuration & Atomic Updates

You’re already on the right path with:

* `atomic.Pointer[T]`
* typed config keys
* partial reload

**Low-latency rule**:

> Reads must be lock-free

```go
val := cfgPtr.Load() // O(1), no mutex
```

---

## 8. Profiling & Measurement (Non-Negotiable Skill)

### 🔹 pprof mastery

* CPU:

  ```bash
  go tool pprof cpu.out
  ```
* Heap:

  ```bash
  go tool pprof heap.out
  ```

### 🔹 Know what “slow” means

* p50, p90, p99 latency
* GC pause time
* Allocations / request

---

## 9. GC & Runtime Tuning

### 🔹 Reduce GC pressure

* Fewer allocations > GC tuning
* Use pooling before touching `GOGC`

### 🔹 Runtime flags

```bash
GOMAXPROCS=$(nproc)
```

---

## 10. Production-Grade Low-Latency Mindset

### 🔹 Design principles

* “Fast is better than clever”
* Prefer explicit code over generic frameworks
* Measure first, optimize second

### 🔹 Typical latency killers

❌ Excessive middleware
❌ JSON reflection
❌ DB round trips
❌ Unbounded goroutines
❌ Logging in hot path

---

## Skill Progression Roadmap

**Beginner → Advanced**

1. Write correct Gin APIs
2. Understand allocations & GC
3. Master pprof
4. Lock-free reads (`atomic`, `sync.Pool`)
5. IO-aware architecture
6. Tail-latency optimization (p99)

---

If you want, I can:

* Review **one of your Gin handlers** for latency issues
* Give a **low-latency Gin project template**
* Show a **before/after pprof optimization case**

Just tell me which direction 👍
