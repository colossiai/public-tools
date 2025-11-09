# Compare `gperftools (tcmalloc)` and `heaptrack`

Excellent question — both **gperftools (tcmalloc)** and **heaptrack** are powerful tools for diagnosing C++ memory leaks and performance issues, but they serve slightly different use cases.

Let’s break it down clearly:

---

## 🧩 1. Overview

| Tool                      | Description                                                                                                                         |
| ------------------------- | ----------------------------------------------------------------------------------------------------------------------------------- |
| **gperftools (tcmalloc)** | A high-performance malloc implementation with optional lightweight heap profiling and CPU profiling. Designed for production use.   |
| **heaptrack**             | A modern, detailed heap profiler built on top of `LD_PRELOAD` interception. Provides full stack traces and visual timeline via GUI. |

---

## ⚙️ 2. Installation & Usage

| Aspect                    | **gperftools (tcmalloc)**                                       | **heaptrack**                       |
| ------------------------- | --------------------------------------------------------------- | ----------------------------------- |
| Install                   | `sudo apt install google-perftools`                             | `sudo apt install heaptrack`        |
| Run new process           | `LD_PRELOAD=/usr/lib/libtcmalloc.so HEAPPROFILE=./heap ./myapp` | `heaptrack ./myapp`                 |
| Attach to running process | ❌ Not supported easily                                          | ✅ `heaptrack -p <pid>`              |
| Analyze                   | `pprof ./myapp heapfile`                                        | `heaptrack_gui heaptrack.<pid>.zst` |

---

## 🧠 3. Profiling Depth

| Feature                    | **gperftools (tcmalloc)** | **heaptrack**                  |
| -------------------------- | ------------------------- | ------------------------------ |
| Sampling-based             | ✅ Yes (low overhead)      | ❌ No, records every allocation |
| Full allocation trace      | ❌ Partial (samples)       | ✅ Full (every alloc/free)      |
| Timeline visualization     | ❌ No                      | ✅ Yes (GUI: memory over time)  |
| Function-level attribution | ✅ Yes (top allocators)    | ✅ Yes (stack traces)           |
| Detect unfreed memory      | ✅ Yes                     | ✅ Yes                          |
| Detect temporary spikes    | ❌ No                      | ✅ Yes (time-based view)        |

---

## ⚡ 4. Overhead & Performance

| Metric                  | **gperftools** | **heaptrack**                |
| ----------------------- | -------------- | ---------------------------- |
| Runtime overhead        | 🟢 Low (few %) | 🔴 High (3–20× slower)       |
| Suitable for production | ✅ Yes          | ⚠️ No (debug/profiling only) |
| Memory overhead         | Low            | Medium–High (stores traces)  |

**Summary:**

* gperftools = lightweight, safe for production, continuous profiling.
* heaptrack = heavy but detailed, best for offline diagnosis or reproducing leak locally.

---

## 📊 5. Output & Analysis

| Tool       | Output                               | Viewer                               |
| ---------- | ------------------------------------ | ------------------------------------ |
| gperftools | `.heap` files → analyze with `pprof` | CLI or Web (`pprof --web`)           |
| heaptrack  | `.zst` file with full trace          | `heaptrack_gui` (interactive charts) |

Example with gperftools:

```bash
pprof --text ./myapp ./heap.0003.heap | head
```

Example with heaptrack:

```bash
heaptrack_gui heaptrack.myapp.1234.zst
```

You’ll see a timeline + callgraph of allocations.

---

## 💡 6. Ideal Use Cases

| Use Case                            | Recommended Tool          |
| ----------------------------------- | ------------------------- |
| Production system (low overhead)    | **gperftools / tcmalloc** |
| Postmortem analysis (attach to PID) | **heaptrack**             |
| GUI visualization, timeline         | **heaptrack**             |
| Quick top allocators overview       | **gperftools**            |
| Long-running service profiling      | **gperftools**            |
| Debug builds, reproduction in dev   | **heaptrack**             |

---

## 🧩 7. Typical Workflow (Best of Both)

**1️⃣ Detect growth in production:**

* Use gperftools (tcmalloc) profiling mode periodically.
* Dump heap snapshots every few hours with `HEAPPROFILE`.

**2️⃣ Reproduce locally with same load:**

* Run app under heaptrack for full allocation trace.
* Open `heaptrack_gui` to find exact leak functions.

---

## ✅ Summary Table

| Feature                | **gperftools (tcmalloc)** | **heaptrack**      |
| ---------------------- | ------------------------- | ------------------ |
| Overhead               | 🔹 Low                    | 🔸 High            |
| Detail                 | 🔸 Moderate               | 🔹 Very detailed   |
| Attach live            | ❌ No                      | ✅ Yes              |
| Visualization          | 🔸 Basic (pprof)          | 🔹 Excellent (GUI) |
| Production use         | ✅ Yes                     | ❌ No               |
| Leak pinpoint accuracy | 🔸 Approximate            | 🔹 Exact           |
| Time-based view        | ❌ No                      | ✅ Yes              |

---

### 🔧 Recommendation

* **Use gperftools (tcmalloc)** in production for low-overhead continuous monitoring.
* **Use heaptrack** in development or staging to dig deep into specific leaks.

---

Would you like me to show a **combined workflow** example — using gperftools for production sampling and heaptrack to deep-dive into the specific leaking code paths found?

