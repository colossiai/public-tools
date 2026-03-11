# Inspect risk check loop assembly

Let’s walk through a **realistic low-latency example** similar to what appears inside an exchange **order matching engine** or **risk check loop**. We’ll start from C++ and inspect the generated **x86 assembly** and explain what a low-latency engineer looks for.

---

# 1. Example: Simple Risk Check Loop

Suppose we have a **very common hot-path operation**: checking if an order exceeds a position limit.

### C++ code

```cpp
inline bool risk_check(int position, int order_qty, int limit) {
    return position + order_qty <= limit;
}

int process_orders(int* pos, int* qty, int limit, int n) {
    int approved = 0;

    for (int i = 0; i < n; i++) {
        if (risk_check(pos[i], qty[i], limit))
            approved++;
    }

    return approved;
}
```

Compile:

```bash
g++ -O3 -march=native test.cpp
objdump -d -M intel a.out
```

---

# 2. Typical Optimized Assembly

A good compiler will produce something similar to this:

```asm
process_orders:
    xor     eax,eax        ; approved = 0
    xor     r8d,r8d        ; i = 0

L1:
    mov     ecx,[rdi+r8*4] ; load pos[i]
    mov     edx,[rsi+r8*4] ; load qty[i]
    add     ecx,edx        ; position + order_qty
    cmp     ecx,edx        ; compare with limit
    setle   dl             ; dl = result (0 or 1)
    add     eax,edx        ; approved += result

    inc     r8
    cmp     r8,rcx
    jne     L1

    ret
```

---

# 3. Instruction-by-Instruction Analysis

### 1️⃣ Initialize registers

```asm
xor eax,eax
```

Sets `approved = 0`.

Why `xor`?

* fastest way to zero register
* avoids dependency chain

Latency: **0 cycles (dependency breaking)**

---

### 2️⃣ Loop index

```asm
xor r8d,r8d
```

`i = 0`

Compiler uses **r8** as loop index.

Good sign:

* loop variables kept in **registers**

---

### 3️⃣ Load position

```asm
mov ecx,[rdi+r8*4]
```

Memory access:

```
pos[i]
```

Address calculation:

```
base (rdi) + index (r8) * sizeof(int)
```

Possible latency:

| location | latency    |
| -------- | ---------- |
| L1 cache | ~4 cycles  |
| L2 cache | ~12 cycles |
| L3 cache | ~40 cycles |

Low-latency code tries to **keep arrays hot in L1**.

---

### 4️⃣ Load order quantity

```asm
mov edx,[rsi+r8*4]
```

Load:

```
qty[i]
```

Again memory access.

Two loads per loop iteration.

---

### 5️⃣ Add values

```asm
add ecx,edx
```

Compute:

```
position + order_qty
```

Latency: **1 cycle**

This is very fast because:

* register → register

---

### 6️⃣ Compare with limit

```asm
cmp ecx,edx
```

Sets CPU **flags register**.

Used by next instruction.

Latency: **1 cycle**

---

### 7️⃣ Branchless result

```asm
setle dl
```

This is **important**.

Instead of branching:

```
if (x <= limit)
```

The compiler emits:

```
setle dl
```

Meaning:

```
dl = 1 if condition true
dl = 0 otherwise
```

This avoids **branch misprediction**.

---

### 8️⃣ Increment approved

```asm
add eax,edx
```

Equivalent to:

```
approved += result
```

Because result is **0 or 1**.

This is **branchless counting**.

Very good optimization.

---

### 9️⃣ Increment loop index

```asm
inc r8
```

```
i++
```

Latency: **1 cycle**

---

### 🔟 Loop condition

```asm
cmp r8,rcx
jne L1
```

Loop branch.

Branch predictor will predict correctly because:

```
loop branch = highly predictable
```

---

# 4. Why This Code Is Low Latency

Good signs:

### ✅ No function call

`risk_check` was **inlined**.

No `call`.

---

### ✅ Branchless decision

Instead of:

```
if (...)
    approved++
```

we got:

```
setle
add
```

This avoids:

| problem              | cost         |
| -------------------- | ------------ |
| branch misprediction | 15–20 cycles |

---

### ✅ Everything in registers

Operations use:

```
eax ecx edx r8
```

Registers are fastest CPU storage.

---

### ✅ Tight loop

Only about **9 instructions** per iteration.

Very efficient.

---

# 5. What BAD Assembly Would Look Like

If code was poorly optimized:

```asm
cmp ecx,edx
jg skip
inc eax
skip:
```

Branch version.

Problem:

```
branch misprediction
```

Pipeline flush:

```
~20 cycles lost
```

In HFT this is **unacceptable**.

---

# 6. Even Better: Vectorized Version

Best compilers may generate **AVX vector instructions**:

```asm
vmovdqu ymm0,[rdi]
vmovdqu ymm1,[rsi]
vpaddd ymm0,ymm0,ymm1
vpcmpgtd ymm2,ymm0,ymm3
```

Meaning:

```
process 8 orders at once
```

Huge speed improvement.

---

# 7. Professional Workflow

Low-latency engineers often do:

```
write C++
↓
compile -O3 -march=native
↓
inspect assembly
↓
measure with perf
↓
remove branches / memory loads
↓
repeat
```

---

# 8. One Powerful Tool You Should Use

Instead of manually reading assembly, use:

```bash
perf annotate
```

This shows:

```
C++ source
↓
assembly
↓
CPU cycle cost
```

Extremely useful.

---

✅ If you want, I can also show something **extremely useful for low-latency engineers**:

**10 assembly patterns every HFT engineer looks for when reviewing compiled C++**

Examples like:

```
cmov vs branch
lea optimization
xor zeroing
loop unrolling
prefetch usage
```

These patterns allow you to **judge assembly quality in seconds.**


