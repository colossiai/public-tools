# Compare linux `perf` and pprof when troubleshooting CPU high load



Excellent question — both **`perf`** and **`pprof` (gperftools)** can help you troubleshoot **high CPU load**, but they differ significantly in **how** they collect data, **what they measure**, and **where** they’re best used.

Let’s do a side-by-side comparison with context, pros, and real-world usage.

---

## ⚖️ `perf` vs `pprof` (gperftools)

| Aspect             | **`perf` (Linux Perf Events)**                                        | **`pprof` (via gperftools)**                                        |
| :----------------- | :-------------------------------------------------------------------- | :------------------------------------------------------------------ |
| **Type**           | System-level profiler                                                 | Application-level (user-space) profiler                             |
| **Source**         | Kernel sampling of CPU performance counters                           | Function-level instrumentation & sampling via `libprofiler`         |
| **Scope**          | Any process, kernel or user space                                     | Only instrumented C/C++ apps                                        |
| **Need Rebuild?**  | No (can attach to running process)                                    | Yes (link with `-lprofiler` or include `ProfilerStart/Stop`)        |
| **Granularity**    | Instruction, function, kernel stack                                   | Function call stacks (user mode only)                               |
| **Overhead**       | Low to moderate (sampling-based)                                      | Moderate (requires linking, adds some overhead)                     |
| **Output Format**  | `perf.data` + text reports (`perf report`, `perf top`, `perf script`) | `.prof` + visual output (`pprof --text`, `--pdf`, `--web`)          |
| **Visualization**  | TUI, Flamegraph, or export to `perf script`                           | Built-in `pprof` visualization (web, pdf, svg)                      |
| **When useful**    | Any Linux binary, especially unknown or kernel-heavy workloads        | When you control the C++ source and want detailed function insights |
| **Works on**       | Linux only                                                            | Cross-platform (Linux, macOS, etc.)                                 |
| **Requires root?** | Often yes (to read perf events system-wide)                           | No (runs as user process)                                           |

---

## 🧠 Conceptual Difference

|         |                                                                                                                                                                                  |
| ------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `perf`  | Think of it as **a system-wide microscope** — it can attach to any process, record CPU events, cache misses, context switches, and even kernel time.                             |
| `pprof` | Think of it as **an application-level profiler** — it only knows about *your program’s functions* and call stacks, but provides clearer function attribution and easier visuals. |

---

## ⚙️ Example Usage

### 🔹 Using `perf` on a running app

```bash
sudo perf record -F 99 -p <pid> -g -- sleep 10
sudo perf report
```

* `-F 99`: sample at 99Hz
* `-g`: capture call graph
* `-- sleep 10`: record for 10 seconds
* `perf report`: interactive browser to see where CPU cycles went

👉 Great for *any* program — even closed-source binaries or Go/Python processes.

---

### 🔹 Using `pprof` with gperftools

Compile & run:

```bash
g++ -lprofiler app.cpp -o app
CPUPROFILE=cpu.prof ./app
pprof --text ./app cpu.prof
pprof --web ./app cpu.prof
```

👉 Requires app rebuild, but gives higher-level, source-linked function names.

---

## 🔍 Strength Comparison

| Scenario                               | Best Tool    | Why                                              |
| :------------------------------------- | :----------- | :----------------------------------------------- |
| Investigate unknown binary’s CPU spike | **perf**     | No rebuild; can attach to any PID                |
| Optimize known C++ source              | **pprof**    | Function-level view, simple call graph           |
| Compare pre/post optimization runs     | **pprof**    | Supports `--base` and `--diff_base` comparison   |
| Inspect kernel time or syscalls        | **perf**     | Includes kernel samples                          |
| Minimal performance overhead           | **perf**     | Runs via kernel events, not user instrumentation |
| Real-time profiling                    | **perf top** | Interactive live CPU hotspots view               |
| Visual function graph for dev analysis | **pprof**    | Built-in web/PDF visual graphs                   |

---

## 🧩 Example Combined Workflow

1. **Start with `perf top`**

   ```bash
   sudo perf top -p <pid>
   ```

   → Identify if CPU is burning in user or kernel space.

2. **If user-space C++ code → switch to `pprof`**

   * Rebuild app with `-lprofiler`
   * Capture detailed call stacks
   * Generate flamegraph or call tree

3. **If kernel or system calls dominate → stay with `perf`**

   * Use `perf record` + `perf report`
   * Explore syscall traces and hardware counters

---

## 🧭 Summary Cheat Sheet

| Goal                             | Recommended Tool   |
| -------------------------------- | ------------------ |
| Quick “who’s burning CPU?”       | `top` / `perf top` |
| Deep kernel or syscall tracing   | `perf`             |
| User-space C++ code optimization | `pprof`            |
| Visual diff of two runs          | `pprof --base`     |
| Full-system profiling            | `perf record -a`   |

---

✅ **In short:**

* Use **`perf`** to *find* the hot process or thread.
* Use **`pprof`** to *understand* what part of your code is hot.

---

Would you like me to show an **end-to-end workflow** (using both `perf` and `pprof`) to troubleshoot a real CPU hotspot step by step (with sample code and outputs)?
