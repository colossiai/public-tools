# Analysis the ZGC gc log

* The log is generated from app app with small heap intentionally

```bash
# Configure undersized heap: 1GB max, but live set will grow to ~800MB
export JVM_OPTS="-Xms512m \
-Xmx1g \
-XX:+UseZGC \
-Xlog:gc*:file=${GC_LOG}:time,uptime,level,tags \
-Xlog:gc+phases=debug \
-Xlog:gc+heap=debug \
-XX:+UnlockDiagnosticVMOptions \
-XX:+PrintFlagsFinal \
-XX:ZAllocationSpikeTolerance=1"
```

```
[2026-02-18T19:13:11.144+0800][45.206s][info][gc,ref      ] GC(2485) O:                       Encountered   Discovered     Enqueued 
[2026-02-18T19:13:11.144+0800][45.206s][info][gc,ref      ] GC(2485) O: Soft References:               65           44            0 
[2026-02-18T19:13:11.144+0800][45.206s][info][gc,ref      ] GC(2485) O: Weak References:              203          153            0 
[2026-02-18T19:13:11.144+0800][45.206s][info][gc,ref      ] GC(2485) O: Final References:               0            0            0 
[2026-02-18T19:13:11.144+0800][45.206s][info][gc,ref      ] GC(2485) O: Phantom References:             5            3            0 
[2026-02-18T19:13:11.144+0800][45.206s][info][gc,reloc    ] GC(2485) O:                        Candidates     Selected     In-Place         Size        Empty    Relocated 
[2026-02-18T19:13:11.144+0800][45.206s][info][gc,reloc    ] GC(2485) O: Small Pages:                   56            8            0         112M           0M           3M 
[2026-02-18T19:13:11.144+0800][45.206s][info][gc,reloc    ] GC(2485) O: Medium Pages:                  17            2            2         388M           0M          21M 
[2026-02-18T19:13:11.144+0800][45.206s][info][gc,reloc    ] GC(2485) O: Large Pages:                   55            0            0         446M           0M           0M 
[2026-02-18T19:13:11.144+0800][45.206s][info][gc,reloc    ] GC(2485) O: Forwarding Usage: 0M
[2026-02-18T19:13:11.144+0800][45.206s][info][gc,heap     ] GC(2485) O: Min Capacity: 512M(50%)
[2026-02-18T19:13:11.144+0800][45.206s][info][gc,heap     ] GC(2485) O: Max Capacity: 1024M(100%)
[2026-02-18T19:13:11.144+0800][45.206s][info][gc,heap     ] GC(2485) O: Soft Max Capacity: 1024M(100%)
[2026-02-18T19:13:11.144+0800][45.206s][info][gc,heap     ] GC(2485) O: Heap Statistics:
[2026-02-18T19:13:11.144+0800][45.206s][info][gc,heap     ] GC(2485) O:                Mark Start          Mark End        Relocate Start      Relocate End           High               Low         
[2026-02-18T19:13:11.144+0800][45.206s][info][gc,heap     ] GC(2485) O:  Capacity:     1024M (100%)       1024M (100%)       1024M (100%)       1024M (100%)       1024M (100%)       1024M (100%)   
[2026-02-18T19:13:11.144+0800][45.206s][info][gc,heap     ] GC(2485) O:      Free:       16M (2%)           30M (3%)           10M (1%)           20M (2%)           42M (4%)            0M (0%)     
[2026-02-18T19:13:11.144+0800][45.206s][info][gc,heap     ] GC(2485) O:      Used:     1008M (98%)         994M (97%)        1014M (99%)        1004M (98%)        1024M (100%)        982M (96%)    
[2026-02-18T19:13:11.144+0800][45.206s][info][gc,heap     ] GC(2485) O: Old Generation Statistics:
[2026-02-18T19:13:11.144+0800][45.206s][info][gc,heap     ] GC(2485) O:                Mark Start          Mark End        Relocate Start      Relocate End    
[2026-02-18T19:13:11.144+0800][45.206s][info][gc,heap     ] GC(2485) O:      Used:      946M (92%)         982M (96%)         982M (96%)         942M (92%)    
[2026-02-18T19:13:11.144+0800][45.206s][info][gc,heap     ] GC(2485) O:      Live:         -               843M (82%)         843M (82%)         843M (82%)    
[2026-02-18T19:13:11.144+0800][45.206s][info][gc,heap     ] GC(2485) O:   Garbage:         -               102M (10%)         102M (10%)          27M (3%)     
[2026-02-18T19:13:11.144+0800][45.206s][info][gc,heap     ] GC(2485) O: Allocated:         -                36M (4%)           36M (4%)           71M (7%)     
[2026-02-18T19:13:11.144+0800][45.206s][info][gc,heap     ] GC(2485) O: Reclaimed:         -                  -                 0M (0%)           75M (7%)     
[2026-02-18T19:13:11.144+0800][45.206s][info][gc,heap     ] GC(2485) O: Compacted:         -                  -                  -                26M (3%)     
[2026-02-18T19:13:11.144+0800][45.206s][info][gc,phases   ] GC(2485) O: Old Generation 994M(97%)->1004M(98%) 0.097s
[2026-02-18T19:13:11.144+0800][45.207s][info][gc          ] GC(2485) Major Collection (Allocation Rate) 1006M(98%)->1000M(98%) 0.126s
[2026-02-18T19:13:11.144+0800][45.207s][info][gc          ] GC(2487) Major Collection (Allocation Stall)
[2026-02-18T19:13:11.144+0800][45.207s][info][gc,task     ] GC(2487) Using 3 Workers for Young Generation
[2026-02-18T19:13:11.144+0800][45.207s][info][gc,task     ] GC(2487) Using 3 Workers for Old Generation
[2026-02-18T19:13:11.145+0800][45.207s][info][gc,phases   ] GC(2487) Y: Young Generation (Promote All)
[2026-02-18T19:13:11.145+0800][45.207s][info][gc,phases   ] GC(2487) Y: Pause Mark Start 0.011ms
[2026-02-18T19:13:11.148+0800][45.210s][info][gc,phases   ] GC(2487) Y: Concurrent Mark 3.084ms
[2026-02-18T19:13:11.148+0800][45.210s][info][gc,phases   ] GC(2487) Y: Pause Mark End 0.018ms
[2026-02-18T19:13:11.148+0800][45.210s][info][gc,phases   ] GC(2487) Y: Concurrent Mark Free 0.020ms
[2026-02-18T19:13:11.148+0800][45.210s][info][gc,phases   ] GC(2487) Y: Concurrent Reset Relocation Set 0.002ms
[2026-02-18T19:13:11.153+0800][45.215s][info][gc,reloc    ] GC(2487) Y: Using tenuring threshold: 0 (Promote All)
[2026-02-18T19:13:11.153+0800][45.215s][info][gc          ] Allocation Stall (Workload-1) 50.262ms
[2026-02-18T19:13:11.153+0800][45.215s][info][gc          ] Allocation Stall (Workload-3) 41.272ms
[2026-02-18T19:13:11.153+0800][45.215s][info][gc,phases   ] GC(2487) Y: Concurrent Select Relocation Set 5.271ms
[2026-02-18T19:13:11.154+0800][45.217s][info][gc,phases   ] GC(2487) Y: Pause Relocate Start 0.015ms
[2026-02-18T19:13:11.157+0800][45.219s][info][gc,phases   ] GC(2487) Y: Concurrent Relocate 2.429ms
[2026-02-18T19:13:11.157+0800][45.219s][info][gc,alloc    ] GC(2487) Y:                         Mark Start        Mark End      Relocate Start    Relocate End   
[2026-02-18T19:13:11.157+0800][45.219s][info][gc,alloc    ] GC(2487) Y: Allocation Stalls:          3                3                1                1         
[2026-02-18T19:13:11.157+0800][45.219s][info][gc,load     ] GC(2487) Y: Load: 5.04 (42%) / 3.30 (28%) / 3.27 (27%)
[2026-02-18T19:13:11.157+0800][45.220s][info][gc,mmu      ] GC(2487) Y: MMU: 2ms/93.8%, 5ms/96.8%, 10ms/98.0%, 20ms/98.8%, 50ms/99.2%, 100ms/99.4%
[2026-02-18T19:13:11.157+0800][45.220s][info][gc,marking  ] GC(2487) Y: Mark: 2 stripe(s), 1 proactive flush(es), 1 terminate flush(es), 0 completion(s), 0 continuation(s) 
[2026-02-18T19:13:11.157+0800][45.220s][info][gc,nmethod  ] GC(2487) Y: NMethods: 605 registered, 62 unregistered
[2026-02-18T19:13:11.157+0800][45.220s][info][gc,metaspace] GC(2487) Y: Metaspace: 10M used, 10M committed, 1088M reserved
```


Great, thanks for pasting the real log — this one is **very informative**, and yes: it shows **a genuine ZGC problem**, not just noisy logs.

I’ll break this down in a **forensic, line-by-line way**, then summarize **what is wrong**, **why it happens**, and **what you should do**.

---

# 🔥 Executive summary (TL;DR)

Your JVM is in **severe heap exhaustion**, causing:

* ✅ **Allocation Stall (50ms+)** → *application threads blocked*
* ✅ **Heap ~98–100% full**
* ✅ **Major GC immediately followed by another Major GC**
* ✅ **Young GC promoted everything (Promote All)** because there is no space
* ⚠️ ZGC is **fighting for survival**, not “low-latency GC” anymore

This is **not healthy ZGC behavior**.

---

# 1️⃣ The smoking gun: Allocation Stall

```
[gc] Allocation Stall (Workload-1) 50.262ms
[gc] Allocation Stall (Workload-3) 41.272ms
```

### What this *really* means

* Application threads **stopped for 40–50ms**
* Not a GC pause — this is **allocation back-pressure**
* ZGC could not provide memory fast enough

💥 **This violates ZGC’s core promise** (no long pauses)

---

# 2️⃣ Heap is basically full the entire time

```
Capacity: 1024M (100%)
Free:      16M (2%)
Used:    1008M (98%)
```

At **multiple points**:

* Free memory: **1–3%**
* Used: **97–100%**
* High watermark: **100%**

### Why this is catastrophic for ZGC

ZGC **requires free headroom** to:

* Relocate objects
* Allocate forwarding memory
* Absorb allocation spikes

Healthy ZGC:

* Post-GC usage: **< 70–75%**

Your system:

* Post-GC usage: **~98%**

That’s a **hard fail zone**.

---

# 3️⃣ Old generation is saturated with live data

```
Old Gen Live: 843M (82%)
Old Gen Used: 982M (96%)
Garbage:     102M (10%)
```

### Interpretation

* ~82% of the heap is **live objects**
* Only ~10% garbage found
* ZGC **cannot free enough memory**

This means **one (or more)** of:

* Memory leak
* Long-lived cache / retention
* Heap size far too small

---

# 4️⃣ Back-to-back Major GCs (panic mode)

```
GC(2485) Major Collection (Allocation Rate)
GC(2487) Major Collection (Allocation Stall)
```

### This sequence is extremely bad

1. GC(2485) tries to keep up with allocation rate
2. Heap still ~98% full
3. Allocation fails
4. GC(2487) triggered due to **Allocation Stall**

ZGC is no longer proactive — it’s **reactive**.

---

# 5️⃣ “Promote All” = young generation collapse

```
Y: Young Generation (Promote All)
Using tenuring threshold: 0 (Promote All)
```

### Why this happens

* There is **no space** to age objects
* Every young object is pushed directly into old gen

### Consequences

* Old gen fills even faster
* Live set explodes
* GC pressure accelerates

This is a **death spiral pattern**.

---

# 6️⃣ Allocation stalls confirmed by allocation statistics

```
Allocation Stalls:
Mark Start: 3
Mark End:   3
Relocate:   1
```

This confirms:

* Stalls happened during **multiple GC phases**
* Not a one-off hiccup

---

# 7️⃣ Pauses are short — but that’s misleading

```
Pause Mark Start 0.011ms
Pause Relocate Start 0.015ms
```

Yes, pauses are tiny — **but irrelevant** here.

Why?

> Allocation stalls block application threads **outside GC pauses**

So latency is still destroyed even with “perfect pauses”.

---

# 8️⃣ What is *not* the problem

Just to be precise:

✅ GC workers (3) — fine
✅ Concurrent phases are fast — fine
✅ Metaspace is tiny — fine
✅ JNI / refs — normal

The issue is **pure memory pressure**.

---

# 🧠 Root cause (plain English)

Your application’s **live memory footprint is larger than what ZGC can manage in a 1GB heap**.

ZGC is:

* Finding little garbage
* Unable to compact fast enough
* Forced to stall allocations

This is **not a tuning problem** — it’s a **capacity problem**.

---

# 🛠️ What you should do (in order)

## ✅ 1. Increase heap size (mandatory)

If you want ZGC to work properly:

* Minimum recommendation here: **2–3× live set**
* Your live set ≈ **850MB**
* Realistic heap: **2.5–3GB**

This alone may completely fix the issue.

---

## ✅ 2. Look for retained objects

Because 82% is live:

* Heap dump
* Look for:

  * Caches without eviction
  * Static collections
  * Long-lived maps
  * ThreadLocal leaks

---

## ✅ 3. Watch these metrics after fix

Healthy ZGC after fix should show:

* No allocation stalls
* Heap after GC < 75%
* No Promote All
* No back-to-back Major GCs

---

# 🚨 Final verdict

This log clearly indicates:

> ❌ **ZGC is starved for memory and is stalling application threads**

If you do nothing, this will:

* Cause latency spikes
* Reduce throughput
* Eventually OOM

If you want, next we can:

* Estimate **exact heap size** needed
* Walk through **what objects are likely retained**
* Compare this with **G1 or Shenandoah behavior**

Just tell me how deep you want to go 👇
