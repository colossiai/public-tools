# Explain x86 SFENCE

### x86 `SFENCE` Instruction

`SFENCE` = **Store Fence**

It is a **memory ordering instruction** that ensures **store (write) operations before the fence become globally visible before any store after the fence**.

In other words:

```
Store A
Store B
```

Without a fence, the CPU may reorder them internally or delay visibility to other cores.

With `SFENCE`:

```
Store A
SFENCE
Store B
```

The CPU guarantees:

```
A becomes globally visible
    BEFORE
B becomes globally visible
```

---

# 1. Why `SFENCE` Exists

Modern CPUs (especially x86 with **store buffers**) allow **out-of-order memory operations** for performance.

A typical store pipeline:

```
CPU Core
   ↓
Store Buffer
   ↓
L1 Cache
   ↓
L2/L3
   ↓
Memory
```

Stores are **queued in the store buffer**, so:

```
store A
store B
```

may become visible to other cores as:

```
B visible first
A visible later
```

`SFENCE` forces the CPU to:

```
drain the store buffer before continuing
```

---

# 2. What `SFENCE` Orders

`SFENCE` only orders **stores vs stores**.

| Instruction | Orders         |
| ----------- | -------------- |
| `LFENCE`    | Loads          |
| `SFENCE`    | Stores         |
| `MFENCE`    | Loads + Stores |

So:

```
Store → Store  ✔ ordered
Store → Load   ✖ not guaranteed
Load → Store   ✖ not guaranteed
Load → Load    ✖ not guaranteed
```

---

# 3. Typical Use Case

`SFENCE` is commonly used with:

### Streaming stores (non-temporal writes)

Example instruction:

```
MOVNTDQ
MOVNTPS
MOVNTI
```

These **bypass cache** and write directly to memory.

Example:

```asm
movnti [rdi], rax
movnti [rdi+8], rbx
sfence
```

Why?

Because **non-temporal stores are weakly ordered**.

Without `SFENCE`, the writes might still be in buffers when the program proceeds.

---

# 4. Example Scenario

Imagine a producer thread writing data then a flag.

```
data = 42
flag = 1
```

Assembly version:

```asm
mov [data], 42
sfence
mov [flag], 1
```

Guarantee:

```
Other cores cannot see flag=1
before data=42 is visible
```

Without `SFENCE`:

```
flag visible first
data visible later
```

This breaks synchronization.

---

# 5. Hardware Effect

`SFENCE` does roughly:

```
wait until all previous stores
leave the store buffer
```

Conceptually:

```
Store buffer
--------------
A
B
SFENCE   ← waits here until A,B commit
C
```

---

# 6. Performance Cost

`SFENCE` is **much cheaper than `MFENCE`**.

Approximate cost:

| Instruction | Cost          |
| ----------- | ------------- |
| `LFENCE`    | ~5–10 cycles  |
| `SFENCE`    | ~10–20 cycles |
| `MFENCE`    | ~40–80 cycles |

(Varies by microarchitecture.)

That's why **HFT / low-latency code prefers `SFENCE` when possible.**

---

# 7. Example in C/C++

In C++ atomics:

```cpp
std::atomic_thread_fence(std::memory_order_release);
```

often compiles to:

```
SFENCE
```

(on architectures that need it).

---

# 8. Real Low-Latency Example

High-performance systems (trading, networking, storage) use:

```
Write packet buffer
SFENCE
Ring doorbell register
```

Example:

```
write DMA buffer
SFENCE
notify NIC
```

Because the NIC must **not read the buffer before writes complete**.

---

# 9. Relationship with x86 Memory Model

x86 uses **TSO (Total Store Order)**:

* Loads are not reordered with loads
* Stores are not reordered with stores

However **visibility via store buffers still matters**, especially for:

* **non-temporal stores**
* **MMIO**
* **persistent memory**

So `SFENCE` is still needed.

---

# 10. Quick Summary

| Instruction          | Meaning                                                  |
| -------------------- | -------------------------------------------------------- |
| `SFENCE`             | Ensures **stores before** happen before **stores after** |
| Primary job          | **Drain store buffer**                                   |
| Typical usage        | Streaming stores, device memory                          |
| Cost                 | Moderate                                                 |
| Compared to `MFENCE` | Much cheaper                                             |

---

✅ **One-line mental model**

```
SFENCE = "flush my previous writes before doing new writes"
```

---

If you're studying **low-latency/HFT assembly**, I can also show you the **7 memory ordering instructions every performance engineer should know** (including `LOCK`, `XCHG`, `CLFLUSH`, `PAUSE`, etc.).
