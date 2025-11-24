# FastUtil and alternatives

If you're looking for **FastUtil alternatives** (especially for **primitive collections**, **low-latency**, ** memory-efficient** data structures), here are the real options that people in high-performance Java projects actually use.

Below is the list **from best → worst**, with notes.

---

# 🏆 **1. HPPC (High-Performance Primitive Collections)**

**URL**: CarrotSearch/HPPC
**Status**: Active-ish
**Focus**: Very fast primitive collections
**Style**: Similar to Trove, with open-addressing maps and sets

### Pros

* Very fast, comparable to FastUtil
* Lightweight, minimal GC
* Clean API

### Cons

* Development slower than FastUtil
* API less extensive

### When to use:

If you want **very fast maps/sets**, but prefer a cleaner API than FastUtil.

---

# 🏆 **2. Agrona (RealLogic)** (NOT a full replacement, but amazing for some cases)

**URL**: RealLogic/Agrona (same team as Aeron)
**Status**: Extremely active
**Focus**: Off-heap / on-heap data buffers + ring buffers + specialized maps

### Important:

Agrona offers **Long2LongHashMap**, **Int2IntHashMap**, etc.

### Pros

* Designed for **low-latency trading systems**
* Used in Aeron, Chronicle-like systems
* Very fast open-addressing maps
* Tight GC footprint

### Cons

* Limited to **primitive–primitive** maps
* Little variety (no lists, sets, only basic maps)

### When to use:

If you need **ultra low latency**, and your map types fit Agrona's limited set.

---

# 🥈 **3. Eclipse Collections (primitive collections)**

Even though it's not purely minimalistic like FastUtil, its **primitive collections** are strong.

### Pros

* Very mature
* Rich API
* Good performance

### Cons

* More abstraction → slightly more overhead
* Not as low-level / raw as FastUtil

### When to use:

If you need **functional transformations + primitive collections**.

---

# 🥉 **4. Trove4j (older)**

**URL**: trove4j
**Status**: Mostly dead
**Focus**: Primitive collections

### Pros

* Once the standard primitive collection lib
* Still works and is stable

### Cons

* No longer maintained
* Slower than FastUtil now

### When to use:

Usually **not recommended** unless stuck with legacy.

---

# 🥉 **5. Koloboke**

**URL**: Koloboke
**Status**: Almost dead; moved to commercial version
**Focus**: Extremely fast primitive maps

### Pros

* Very fast in benchmarks
* Excellent design

### Cons

* Open-source version is old (Java 8 era)
* Author switched to commercial license → updates only in paid version

### When to use:

If you're ok using an old version or paying for the commercial one.

---

# 🥉 **6. Goldman Sachs GS Collections (old name of Eclipse Collections)**

(Actually Eclipse Collections; keep for legacy references.)

---

# ❗ Not alternatives but sometimes used:

### **7. Java's own `PrimitiveIterator` + arrays**

People sometimes ditch collections entirely for:

* `int[]` + custom binary search
* linear probing map implementations
* or direct buffer algorithms

For absolute lowest latency (HFT), custom structures **can beat FastUtil**.

---

# ❗ **8. JCTools**

Not a replacement, but essential for low-latency queues:

* MPSC/MPSC queues
* SPSC ring buffers

Common for messaging pipelines, trading engines.

---

# 🧩 Summary Table

| Library                 | Primitive Collections | Performance | Maintenance | Notes                   |
| ----------------------- | --------------------- | ----------- | ----------- | ----------------------- |
| **FastUtil**            | ★★★★★                 | ★★★★★       | ★★★★        | Best all-around         |
| **HPPC**                | ★★★★                  | ★★★★★       | ★★☆         | Clean, fast             |
| **Agrona**              | ★★☆                   | ★★★★★       | ★★★★★       | Best latency; few types |
| **Eclipse Collections** | ★★★★★                 | ★★★★        | ★★★★★       | Rich API                |
| **Trove4j**             | ★★★                   | ★★★★        | ☆☆☆         | Legacy                  |
| **Koloboke**            | ★★★★                  | ★★★★★       | ☆☆☆         | Old or paid             |

---

# ⭐ Best Choice by Scenario

### **Ultra low latency trading (orderbook, matching engine)**

→ **Agrona** or **FastUtil**

### **General high-performance primitive maps**

→ **FastUtil**
→ HPPC

### **Rich functional operations**

→ **Eclipse Collections**

### **Legacy systems**

→ Trove4j or old Koloboke

---

# If you want, I can provide:

* JMH benchmark comparing **FastUtil vs HPPC vs Agrona**
* Recommendations for specific map types (Long2Long, Long2Object, Int2Long…)
* Example code for low-GC open-addressing maps

Just tell me.
