# 10 assembly patterns every HFT engineer looks for when reviewing compiled C++


When **high-frequency trading (HFT)** engineers review compiled C++ (via `objdump`, `perf annotate`, or `Compiler Explorer`), they usually scan for a small set of **assembly patterns that directly affect latency, branch predictability, and memory ordering**.

Below are **10 common assembly patterns HFT engineers look for** when verifying the compiler generated optimal code.

---

# 10 Assembly Patterns Every HFT Engineer Looks For

## 1. Branch vs Branchless (`cmp` + `jcc` vs `cmov`)

### Bad (branch)

```asm
cmp eax, ebx
jg  label
```

### Better (branchless)

```asm
cmp eax, ebx
cmovg eax, ebx
```

**Why it matters**

Branches can cause **branch misprediction (~15–20 cycles)**.

HFT engineers prefer:

* `CMOV`
* `SETcc`
* bit tricks

for predictable latency.

---

# 2. Memory Load vs Register Reuse

### Bad

```asm
mov eax, [rdi]
add eax, [rdi]
```

### Good

```asm
mov eax, [rdi]
add eax, eax
```

**Why**

Extra memory loads:

* cause **L1 cache pressure**
* may trigger **cache misses**

Always check if the compiler reloads memory unnecessarily.

---

# 3. `LOCK` Instructions (Performance Killer)

Look for:

```asm
lock xadd
lock add
lock cmpxchg
```

Example:

```asm
lock xadd [rdi], eax
```

**Why**

`LOCK`:

* locks cache line
* expensive in multi-core

HFT engineers verify they only appear when absolutely required.

---

# 4. Hidden Memory Fences (`mfence`, `lfence`, `sfence`)

Example:

```asm
mfence
```

or

```asm
lock add [rsp], 0
```

This sometimes appears from:

* `std::atomic`
* `volatile`
* Java VarHandle (as you asked earlier)

**Cost**

~40–100 cycles depending on CPU.

---

# 5. Redundant Zeroing (`xor reg, reg`)

Compiler often emits:

```asm
xor eax, eax
```

instead of:

```asm
mov eax, 0
```

HFT engineers check:

* zero idioms used correctly
* no redundant clearing.

---

# 6. Register Spills to Stack

Bad pattern:

```asm
mov [rsp+8], rax
mov rax, [rsp+8]
```

Means:

* **register pressure**
* compiler spilled to stack

Stack access = extra latency.

---

# 7. Unnecessary Function Calls

Bad:

```asm
call memcpy
```

Good:

```asm
mov
mov
mov
```

HFT engineers prefer **inlined code** for:

* small functions
* memory copies
* arithmetic

Function calls cost:

* pipeline flush
* return stack predictor usage

---

# 8. SIMD Vectorization (`_mm_*` Intrinsics)

Look for instructions like:

```asm
vmovdqa
vaddps
vpaddq
```

or AVX:

```asm
vaddpd ymm0, ymm1, ymm2
```

This confirms the compiler used **vectorization**.

Without SIMD you might see:

```asm
add
add
add
add
```

instead.

---

# 9. Unaligned Memory Access

Bad:

```asm
movups xmm0, [rdi]
```

Better:

```asm
movaps xmm0, [rdi]
```

**Why**

* `movups` = unaligned
* `movaps` = aligned

Alignment improves L1 cache behavior.

---

# 10. Spinlock Optimization (`pause`)

Correct spinlock:

```asm
spin:
pause
cmp [lock], 0
jne spin
```

If `pause` missing:

```asm
cmp [lock], 0
jne spin
```

CPU will:

* burn power
* reduce SMT performance

`pause` improves pipeline efficiency.

---

# Bonus: What HFT Engineers **Really Scan For**

When scanning assembly, they quickly look for:

| Pattern           | Why                       |
| ----------------- | ------------------------- |
| `jmp / jcc`       | branch misprediction risk |
| `lock`            | expensive atomic          |
| `mfence`          | heavy memory barrier      |
| stack spills      | register pressure         |
| `call`            | latency                   |
| SIMD instructions | vectorization             |
| `pause`           | spinlock optimization     |
| memory loads      | cache efficiency          |

---

# Typical HFT Workflow

Example verification flow:

```
g++ -O3 -march=native code.cpp
objdump -d a.out
```

Or with perf:

```
perf record ./a.out
perf annotate
```

Or online:

```
Compiler Explorer (godbolt)
```

---

# Real HFT Tip

Top firms like:

* **Jane Street**
* **Citadel Securities**
* **Two Sigma**

often maintain **internal assembly review culture**, where engineers regularly inspect compiler output for hot paths.

---

If you'd like, I can also show:

**"A real C++ order book function → compiled assembly → what an HFT engineer critiques line-by-line."**

This is one of the **best ways to learn low-latency optimization.** 🚀
