# Difference between pprof --diff_base and pprof --base


Good question — this is a subtle but important distinction when comparing profiles in **Go’s `pprof`** tool.

Let’s break it down clearly:

---

### 🧩 `--base`

**Purpose:** Compare *two profile snapshots* (base vs current) — often used to find **what changed (e.g., leaked or grew)**.

**Usage example:**

```bash
go tool pprof --base base.pb.gz current.pb.gz
```

**Meaning:**

* `base.pb.gz`: a **baseline** profile (earlier in time).
* `current.pb.gz`: a **later** profile (current state).

`pprof` subtracts the metrics in `base` from `current`.
For example, in a heap profile:

* Positive values ⇒ **new allocations** (memory growth)
* Negative values ⇒ **freed memory**

✅ **Typical use case:**
Detect **memory leaks** or **growth over time**:

```bash
# Capture two profiles 60s apart
go tool pprof -proto http://localhost:6060/debug/pprof/heap > base.pb.gz
sleep 60
go tool pprof -proto http://localhost:6060/debug/pprof/heap > current.pb.gz

# Compare them
go tool pprof --base base.pb.gz current.pb.gz
```

---

### ⚖️ `--diff_base`

**Purpose:** Compare *two profiles* by highlighting **relative differences** in the output visualization (e.g., web or text graph).

**Usage example:**

```bash
go tool pprof --diff_base old.pb.gz new.pb.gz
```

**Meaning:**

* `--diff_base` colors or annotates the graph/text view:

  * Functions **added** or increased (red / positive)
  * Functions **removed** or decreased (green / negative)
* The *scale* and *percentages* are based on the difference rather than simple subtraction.

It’s mainly for **visual or proportional comparisons**, rather than absolute metric subtraction.

✅ **Typical use case:**
Visual diff to see **what parts of the code changed most** between two CPU or memory profiles.

---

### 🔍 Summary Table

| Option        | Input Form                                      | Output Type                               | Common Use                             | Notes                           |
| ------------- | ----------------------------------------------- | ----------------------------------------- | -------------------------------------- | ------------------------------- |
| `--base`      | `go tool pprof --base base.pb.gz current.pb.gz` | Subtracted profile (numerical difference) | Memory leak detection, growth analysis | Subtracts metrics directly      |
| `--diff_base` | `go tool pprof --diff_base old.pb.gz new.pb.gz` | Color-coded diff in visualization         | Comparing CPU/memory hotspots          | Relative diff for visualization |

---

### 🧠 Rule of Thumb

* Use **`--base`** when you want **numerical subtraction** — e.g., to detect **leaked bytes**.
* Use **`--diff_base`** when you want **visual comparison** — e.g., to **see performance regressions** in a flame graph or web UI.

---

Would you like me to show a concrete demo with sample CPU or heap data illustrating how `--base` and `--diff_base` differ in output?
