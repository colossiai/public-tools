# Explain x86 instruction: PREFETCH


The **`PREFETCH`** family of instructions in **x86 instruction set architecture** are **performance hints** that tell the CPU to **load data into cache before it is actually needed**. This helps reduce **memory latency**.

They are especially useful in **high-performance and low-latency systems** (HFT, databases, game engines, etc.).

---

# 1. What `PREFETCH` Does

Normally, when the CPU executes:

```asm
mov rax, [rdi]
```

If `[rdi]` is **not in cache**, the CPU must fetch it from memory:

```
RAM → L3 → L2 → L1 → register
```

This can cost:

| Source   | Latency         |
| -------- | --------------- |
| L1 cache | ~4 cycles       |
| L2 cache | ~12 cycles      |
| L3 cache | ~40 cycles      |
| RAM      | ~100–300 cycles |

A **`PREFETCH` instruction requests the data earlier**, so that when the real load occurs the data is **already in cache**.

Example:

```asm
prefetcht0 [rdi+64]   ; ask CPU to fetch cache line
mov rax, [rdi]        ; later load becomes fast
```

---

# 2. Important Property: It's Only a Hint

`PREFETCH`:

* **does not block**
* **does not guarantee data will be cached**
* **does not raise page faults**
* **can be ignored by CPU**

It simply says:

> "CPU, if possible, please bring this memory into cache."

---

# 3. The Main PREFETCH Instructions

The common ones:

| Instruction   | Meaning                                         |
| ------------- | ----------------------------------------------- |
| `PREFETCHT0`  | Prefetch to **L1 cache** (highest locality)     |
| `PREFETCHT1`  | Prefetch to **L2 cache**                        |
| `PREFETCHT2`  | Prefetch to **L3 cache**                        |
| `PREFETCHNTA` | Non-temporal (streaming, avoid polluting cache) |

Example:

```asm
prefetcht0 [rsi]
```

---

# 4. Why Cache Line Matters

CPUs fetch **cache lines**, not individual bytes.

Typical cache line:

```
64 bytes
```

So this instruction:

```asm
prefetcht0 [rdi]
```

Actually loads:

```
[rdi ... rdi+63]
```

---

# 5. Classic Use Case (Array Processing)

Example loop:

```c
for (int i=0; i<N; i++)
    sum += arr[i];
```

Optimized with prefetch:

```asm
loop:
    prefetcht0 [rdi + 256]   ; prefetch future data
    mov rax, [rdi]
    add rdi, 8
    add rbx, rax
    dec rcx
    jnz loop
```

Why `+256`?

```
256 bytes ≈ 4 cache lines ahead
```

This gives the CPU **enough time to fetch from RAM**.

---

# 6. Why HFT / Low-Latency Engineers Care

Memory stalls are the **#1 performance killer**.

Example cost:

```
CPU add:      1 cycle
RAM access: 200 cycles
```

Without prefetch:

```
mov rax, [mem]   ← stall
```

With prefetch earlier:

```
prefetch mem
...do other work...
mov rax, [mem]   ← cache hit
```

This converts **200 cycles → ~4 cycles**.

---

# 7. When PREFETCH Helps

Good cases:

✔ Large arrays
✔ Streaming data
✔ Predictable access patterns
✔ Graph traversal (sometimes)
✔ Order book / market data parsing

Bad cases:

✖ Random memory access
✖ Small datasets (already in cache)
✖ CPU already doing hardware prefetch well

Modern CPUs already have **hardware prefetchers**, so manual prefetch only helps in special cases.

---

# 8. Modern Compilers Also Expose It

Example in C/C++:

```c
__builtin_prefetch(ptr);
```

Example:

```c
__builtin_prefetch(&arr[i+32], 0, 3);
```

Arguments:

```
0 = read
1 = write
3 = high locality
```

---

# 9. Microarchitecture Detail

`PREFETCH`:

1. Generates a **cache request**
2. Loads the **cache line**
3. Places it into:

```
L1 / L2 / L3 depending on instruction
```

But:

* it **does not allocate registers**
* it **does not stall pipeline**

---

# 10. Real Example From High-Performance Code

Memory scanning algorithm:

```asm
prefetcht0 [rdi + 512]
prefetcht0 [rdi + 576]
prefetcht0 [rdi + 640]

mov rax, [rdi]
mov rbx, [rdi+8]
mov rcx, [rdi+16]
```

This pipelines **memory fetch with computation**.

---

# 11. Related Instructions

| Instruction   | Purpose            |
| ------------- | ------------------ |
| `PREFETCHT0`  | Prefetch to L1     |
| `PREFETCHNTA` | Streaming loads    |
| `CLFLUSH`     | Evict cache line   |
| `MOVNTDQ`     | Non-temporal store |
| `MOVNTI`      | Non-temporal write |

These are core **cache-control instructions** in the **x86 microarchitecture**.

---

✅ **One important insight used by low-latency engineers:**

> Prefetch **3–10 cache lines ahead** of where the CPU is currently reading.

This hides **~200 cycle RAM latency**.

---

If you'd like, I can also show:

1. **A real HFT-style order book parser using PREFETCH**
2. **A 20-line C benchmark showing when PREFETCH makes code slower**
3. **How Intel hardware prefetchers work (very important)** — most developers misunderstand this.
