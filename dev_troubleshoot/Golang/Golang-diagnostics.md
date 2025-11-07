# Introduce golang diagnostic tools to troubleshoot CPU high load/Memory leak


Great topic — Go provides **excellent built-in and external tools** for diagnosing CPU high load, memory leaks, goroutine leaks, and other performance issues. Let’s go through them systematically 👇

---

## 🧠 1. **Built-in Diagnostic Tools**

### (a) **pprof** — CPU, Memory, Goroutine, Block Profiling

**pprof** is the main Go performance profiling tool, built right into the standard library.

#### How to enable:

```go
import (
    _ "net/http/pprof"
    "net/http"
)

func main() {
    go func() {
        http.ListenAndServe("localhost:6060", nil)
    }()
    // your main logic
}
```

Then open:

* 🔗 `http://localhost:6060/debug/pprof/`

Available profiles:

| Profile                  | Description                              |
| ------------------------ | ---------------------------------------- |
| `/debug/pprof/profile`   | 30-second CPU profile                    |
| `/debug/pprof/heap`      | Heap (memory allocation) profile         |
| `/debug/pprof/goroutine` | Stack traces of all goroutines           |
| `/debug/pprof/block`     | Blocking events (mutex contention, etc.) |
| `/debug/pprof/mutex`     | Mutex contention profile                 |

#### Analyze profile:

```bash
go tool pprof http://localhost:6060/debug/pprof/profile
(pprof) top
(pprof) web
```

`web` opens a graph view (requires `dot` from Graphviz).

---

### (b) **runtime/trace**

For more fine-grained event tracing (scheduler events, GC, syscalls, etc.)

```bash
go test -trace trace.out
go tool trace trace.out
```

This opens an interactive web UI to visualize goroutines, CPU usage, GC pauses, etc.

---

### (c) **expvar**

Exports runtime metrics as JSON for monitoring:

```go
import _ "expvar"
import "net/http"

func main() {
    go http.ListenAndServe(":8080", nil)
}
```

Now visit `/debug/vars` — you’ll see metrics like memory stats, goroutines count, GC info, etc.

---

## 🧩 2. **Command-Line Tools**

### (a) **go tool pprof**

Can be used directly with binaries:

```bash
go build -o myapp
./myapp &
go tool pprof http://localhost:6060/debug/pprof/heap
```

Or from saved profiles:

```bash
go tool pprof -http=:8081 cpu.prof
```

### (b) **go test -bench / -cpuprofile / -memprofile**

For profiling benchmarks:

```bash
go test -bench=. -cpuprofile=cpu.out -memprofile=mem.out
go tool pprof cpu.out
```

---

## 🔬 3. **External Tools**

### (a) **Go toolchain GUI**

* **[pprof.me](https://pprof.me)** — upload `.pprof` files for quick visualization.
* **[speedscope.app](https://speedscope.app)** — visualize flame graphs from pprof JSON.

### (b) **GoLand / VSCode**

Both IDEs integrate with `pprof` to visualize CPU & memory usage.

### (c) **Prometheus + Grafana**

With the [prometheus/client_golang](https://github.com/prometheus/client_golang) library, you can export:

* GC pause duration
* Goroutine count
* Memory usage
* Custom app metrics

and visualize over time to detect leaks or abnormal CPU growth.

### (d) **parca / pyroscope**

Continuous profiling tools for Go — lightweight and production-safe.

* Collects CPU/mem profiles continuously
* Visualizes trends over time
* Useful in microservices or Kubernetes

---

## 💡 4. **Common Investigation Patterns**

| Symptom             | Tools                     | Typical Cause                                           |
| ------------------- | ------------------------- | ------------------------------------------------------- |
| High CPU load       | `pprof` (CPU profile)     | Busy loop, goroutine spin, high lock contention         |
| Memory leak         | `pprof` (heap)            | Unreleased slices, maps growing, channels never drained |
| Too many goroutines | `/debug/pprof/goroutine`  | Goroutines blocked on channel or mutex                  |
| Slow response       | `trace`, `block`, `mutex` | Lock contention, GC pauses                              |
| Periodic spikes     | Prometheus metrics        | GC, background jobs, DB retries                         |

---

## ⚙️ Example workflow (CPU high usage)

1. Enable pprof endpoint
2. Run:

   ```bash
   go tool pprof http://localhost:6060/debug/pprof/profile?seconds=30
   ```
3. In pprof shell:

   ```
   (pprof) top10
   (pprof) web
   ```

   Check which function consumes CPU.

---

## ⚙️ Example workflow (Memory leak)

1. Enable heap profiling:

   ```bash
   go tool pprof http://localhost:6060/debug/pprof/heap
   ```
2. Compare snapshots over time:

   ```
   go tool pprof -base heap1.out heap2.out
   ```
3. Use `top` or `list` in pprof to locate leaks.

---

Would you like me to show a **minimal example Go program** that demonstrates how to collect and analyze a CPU & memory profile in practice?
