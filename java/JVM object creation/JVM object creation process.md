# The Java JVM GC memory allocation process when creating a new object.


Here’s what actually happens inside the JVM when you do `new SomeObject()`—from bytecode to GC, step by step.

---

## 1. Bytecode → Allocation Request

When the JVM executes a `new` bytecode instruction, it:

1. Checks the class metadata is loaded and initialized.
2. Figures out **how many bytes** the object needs (object header + fields, padded for alignment).
3. Requests memory from the heap.

At this point, *no GC has happened yet*. The JVM tries a **fast-path allocation first**.

---

## 2. Fast Path: TLAB Allocation (Most Common Case)

### Thread-Local Allocation Buffer (TLAB)

* Each Java thread usually owns a **TLAB**, a small chunk of **Eden space**.
* Allocation is just:

  ```text
  object_address = tlab_top
  tlab_top += object_size
  ```
* This is called **bump-the-pointer allocation**.
* No locks, no synchronization, extremely fast (basically pointer arithmetic).

If the object fits in the current TLAB → **allocation succeeds immediately**.

---

## 3. Slow Path: Eden Allocation

If:

* The TLAB doesn’t have enough space **or**
* TLABs are disabled

Then the JVM:

* Tries to allocate directly from **Eden space**
* Uses atomic operations (CAS) to bump a shared pointer

Still no GC yet—this is slower than TLAB but still cheap.

---

## 4. Allocation Failure → Minor GC Trigger

If Eden does not have enough free space:

1. The JVM triggers a **Minor GC (Young GC)**.
2. Live objects in Eden:

   * Are copied to a **Survivor space** (S0/S1), or
   * Promoted to the **Old Generation** if they’re old enough or Survivor space is full.
3. Eden is cleared completely.

After Minor GC:

* The JVM retries the allocation.
* If it now fits → success.

---

## 5. Promotion & Old Generation Allocation

Objects may be allocated or promoted directly into **Old Gen** when:

* The object is **very large** (bypasses Eden).
* Survivor space is full.
* Object age exceeds the promotion threshold.

Old Gen allocation strategies depend on the GC:

* **CMS / G1**: free lists, region-based allocation
* **Parallel / Serial**: contiguous block allocation

---

## 6. Full GC (Worst Case)

If Old Gen cannot satisfy the allocation:

1. **Full GC** is triggered.
2. Entire heap is compacted or swept.
3. Allocation is retried.

If it *still* fails:

* `OutOfMemoryError: Java heap space` is thrown.

---

## 7. Object Initialization (After Memory Is Reserved)

Once memory is allocated:

1. Object memory is zeroed (JVM guarantee).
2. Object header is written:

   * Mark word (hash, lock, GC info)
   * Class pointer
3. Constructor (`<init>`) is executed.

Only **after this** does your Java code see the object.

---

## 8. Summary Flow (Happy Path)

```text
new Object()
  ↓
TLAB allocation (bump pointer)
  ↓
Eden allocation
  ↓
Minor GC (if needed)
  ↓
Old Gen allocation (if needed)
  ↓
Full GC (last resort)
```

---

## Key Takeaways

* **Most allocations never touch the GC** (TLAB fast path).
* Young Gen is optimized for **cheap allocation and cheap death**.
* GC cost comes from **object survival**, not object creation.
* Allocation is *far* cheaper than synchronization or I/O.

If you want, I can:

* Walk through this for **G1 vs ZGC vs Shenandoah**
* Explain **escape analysis & stack allocation**
* Show how allocation shows up in **JFR or GC logs**



# Walk through this object creation process for G1 vs ZGC vs Shenandoah


Alright, let’s do a **side-by-side walk-through** of what happens when you allocate a new object under **G1 vs ZGC vs Shenandoah**. Same Java code, very different machinery under the hood.

I’ll follow the *exact same allocation timeline* for each so you can see where they diverge.

---

# 1. Common Starting Point (All GCs)

No matter which GC you use:

```java
new Foo()
```

The JVM:

1. Executes the `new` bytecode
2. Computes object size
3. Tries a **fast allocation path first**
4. Falls back to GC only if allocation fails

What changes is **where the memory comes from**, **how failures are handled**, and **whether GC pauses your thread**.

---

# 2. G1 GC Allocation Flow

### Heap model

* Heap split into **equal-sized regions** (1–32 MB)
* Regions can be:

  * Eden
  * Survivor
  * Old
  * Humongous

---

### Step-by-step (G1)

#### 1️⃣ Fast path: TLAB (same as classic JVM)

* Allocation happens in an Eden region
* Bump-the-pointer
* No locks, no GC interaction

✅ **Most allocations end here**

---

#### 2️⃣ Slow path: Eden region allocation

If TLAB is full:

* JVM tries to allocate from another Eden region
* Uses CAS to reserve space

---

#### 3️⃣ Eden full → Young GC

When Eden regions are exhausted:

* **Stop-the-world Young GC**
* Live objects copied:

  * Eden → Survivor
  * Survivor → Survivor / Old
* Dead objects discarded
* Eden regions reclaimed *entirely*

⏸ Pause exists, but:

* Region-based
* Predictable
* Tuned toward short pauses

---

#### 4️⃣ Large objects (Humongous)

If object size > 50% of region:

* Allocated as **Humongous object**
* Occupies multiple contiguous regions
* Reclaimed only during marking cycles

⚠️ Too many humongous objects = G1 pain

---

#### 5️⃣ Old Gen pressure → Mixed GC

* G1 selects a **subset of Old regions**
* Cleans them together with Young regions
* Still stop-the-world, but selective

---

### G1 mental model

> “Pause the world briefly, copy live objects, keep regions tidy.”

---

# 3. ZGC Allocation Flow

### Heap model

* Heap split into **ZPages** (small / medium / large)
* Everything is **colored pointers**
* GC runs **almost entirely concurrently**

---

### Step-by-step (ZGC)

#### 1️⃣ Fast path: TLAB (still exists!)

* Allocation is bump-the-pointer
* Happens in a ZPage
* Object pointer includes **metadata bits** (coloring)

---

#### 2️⃣ Page allocation

If TLAB is empty:

* JVM grabs a new ZPage
* Still concurrent, still fast

No Eden/Survivor distinction.

---

#### 3️⃣ Allocation pressure → Concurrent GC

Instead of failing:

* ZGC starts **concurrent marking**
* Objects are **relocated while application runs**
* Pointers are updated *lazily* via load barriers

🟢 **Your thread does NOT stop**

---

#### 4️⃣ Relocation (no pauses)

* Objects are moved concurrently
* When your code touches a reference:

  * Load barrier checks pointer color
  * Fixes it transparently if needed

This is the magic.

---

#### 5️⃣ Allocation never waits for GC

* Allocation continues while GC works
* If memory is truly exhausted:

  * Allocation stalls briefly (not a Full GC)
  * Worst-case: OOME

---

### ZGC mental model

> “Allocate freely. GC cleans up in the background. Fix pointers on demand.”

---

# 4. Shenandoah Allocation Flow

### Heap model

* Heap split into regions (like G1)
* No fixed young/old separation
* Uses **Brooks forwarding pointers**

---

### Step-by-step (Shenandoah)

#### 1️⃣ Fast path: TLAB

* Same bump-the-pointer allocation
* Region-based

---

#### 2️⃣ Region allocation

* New region assigned if TLAB runs out
* No generational assumptions (by default)

---

#### 3️⃣ Allocation pressure → Concurrent GC

When space is tight:

* Shenandoah starts **concurrent marking**
* Live objects identified
* Objects are **moved concurrently**

🟢 Application threads keep running

---

#### 4️⃣ Forwarding pointer magic

Each object has:

* A forwarding pointer slot

When an object moves:

* Old copy points to new location
* Access barrier checks and follows pointer

No long pauses, no global compaction.

---

#### 5️⃣ Brief pauses (very short)

Shenandoah still has pauses, but they’re:

* Milliseconds
* Independent of heap size

---

### Shenandoah mental model

> “Move objects live, leave breadcrumbs, follow them when needed.”

---

# 5. Side-by-Side Comparison

| Aspect                | G1                  | ZGC           | Shenandoah    |
| --------------------- | ------------------- | ------------- | ------------- |
| Heap layout           | Regions (young/old) | ZPages        | Regions       |
| Allocation fast path  | TLAB                | TLAB          | TLAB          |
| Young GC pauses       | Yes                 | No            | No            |
| Concurrent relocation | Partial             | Yes           | Yes           |
| Pointer barriers      | Minimal             | Load barriers | Read barriers |
| Pause time goal       | ~10–50 ms           | <1 ms         | <5 ms         |
| Large heap scaling    | Good                | Excellent     | Excellent     |
| Humongous objects     | Special case        | Natural       | Natural       |

---

# 6. What This Means Practically

### Choose **G1** if:

* You want predictable pauses
* Heap ≤ ~32–64 GB
* Simpler mental model

### Choose **ZGC** if:

* Latency matters more than throughput
* Heap is huge (100s of GB+)
* You want GC to feel “invisible”

### Choose **Shenandoah** if:

* You want low latency *and* region-based design
* You’re on Red Hat–focused JVMs
* You want fewer pointer tricks than ZGC

---

If you want next:

* A **timeline diagram** for one allocation
* How **escape analysis** interacts with each GC
* What GC logs look like for the *same workload* under all three


# Show timeline diagram for one allocation


Nice, this is where it really clicks. Let’s do a **single object allocation timeline**, same code, three collectors.
Assume:

```java
Foo f = new Foo();
```

Heap is under pressure, but not totally out of memory.

---

## 1️⃣ G1 GC — Allocation Timeline

```
Time →
│
│ Thread executes `new Foo()`
│
├─▶ TLAB allocation attempt
│      └─❌ TLAB full
│
├─▶ Eden region allocation
│      └─❌ No Eden space
│
├─⏸ Stop-the-World (Young GC)
│      ├─ Mark live objects in Eden
│      ├─ Copy survivors → Survivor / Old
│      ├─ Reclaim all Eden regions
│      └─ Pause ends
│
├─▶ Retry allocation
│      └─✅ New Eden region, bump pointer
│
├─▶ Zero memory + write object header
│
└─▶ Constructor `<init>` runs
```

**What your thread experiences**

* One noticeable pause
* Allocation resumes *after* GC finishes

---

## 2️⃣ ZGC — Allocation Timeline

```
Time →
│
│ Thread executes `new Foo()`
│
├─▶ TLAB allocation attempt
│      └─❌ TLAB full
│
├─▶ Get new ZPage
│      └─❌ Heap pressure detected
│
├─▶ ▶▶ Concurrent GC starts (background)
│      ├─ Concurrent marking
│      ├─ Concurrent relocation
│      └─ Pointer colors updated lazily
│
├─▶ Allocation continues concurrently
│      └─✅ Space freed by relocation
│
├─▶ Zero memory + colored pointer install
│
└─▶ Constructor `<init>` runs
```

**What your thread experiences**

* No stop-the-world pause
* Possible *tiny* allocation stall (microseconds)
* GC runs invisibly in parallel

---

## 3️⃣ Shenandoah — Allocation Timeline

```
Time →
│
│ Thread executes `new Foo()`
│
├─▶ TLAB allocation attempt
│      └─❌ TLAB full
│
├─▶ Region allocation attempt
│      └─❌ Regions scarce
│
├─▶ ▶▶ Concurrent GC starts
│      ├─ Concurrent marking
│      ├─ Concurrent evacuation
│      └─ Forwarding pointers installed
│
├─▶ Allocation retries
│      └─✅ Freed region available
│
├─▶ Zero memory + forwarding pointer slot
│
└─▶ Constructor `<init>` runs
```

**What your thread experiences**

* No long pause
* Short, frequent barriers during pointer access
* Allocation proceeds while GC moves objects

---

## 4️⃣ Key Visual Difference (Side-by-Side)

```
G1:          |---- STW GC ----| alloc
ZGC:         | alloc | GC running | alloc |
Shenandoah:  | alloc | GC running | alloc |
```

---

## 5️⃣ What Actually “Costs” Time

| Phase             | G1           | ZGC                    | Shenandoah             |
| ----------------- | ------------ | ---------------------- | ---------------------- |
| Allocation itself | ~nanoseconds | ~nanoseconds           | ~nanoseconds           |
| GC impact         | One pause    | Barriers + concurrency | Barriers + concurrency |
| Latency spikes    | Yes          | Almost none            | Almost none            |

---

## 6️⃣ Intuition to Remember

* **G1**: “I’ll stop everything, clean up, then let you allocate.”
* **ZGC**: “Go ahead, I’ll clean while you work.”
* **Shenandoah**: “Keep going—just follow the forwarding pointers.”

If you want, next I can:

* Draw the **pointer/barrier flow** when the object is later accessed
* Show **humongous object timelines**
* Compare **allocation under extreme memory pressure**
