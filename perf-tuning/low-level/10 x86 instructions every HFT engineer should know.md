# 10 x86 instructions every HFT engineer should know

For **high-frequency trading (HFT) / ultra-low latency** systems on **x86**, a small set of instructions shows up repeatedly in optimized code paths. The goal is usually to:

* avoid branch misprediction
* avoid locks
* measure time precisely
* control memory ordering
* prefetch data

Below are **10 x86 instructions every low-latency engineer should recognize when reading assembly**.

---

# 1. `RDTSC` — read CPU timestamp counter

Used for **nanosecond-level timing**.

```asm
rdtsc
```

Returns:

```
EDX:EAX = CPU cycle counter
```

Example usage in C:

```c
uint64_t t;
asm volatile ("rdtsc" : "=A"(t));
```

Typical uses:

* latency measurement
* benchmarking critical paths
* market-data processing timing

Often paired with **`RDTSCP`** to prevent reordering.

---

# 2. `RDTSCP` — serialized timestamp read

```asm
rdtscp
```

Difference from `rdtsc`:

* waits until previous instructions finish
* avoids measurement noise

Very common in HFT benchmarking.

---

# 3. `CMOV` — conditional move (branchless logic)

```asm
cmp rax, rbx
cmovg rax, rbx
```

Meaning:

```
if (rbx > rax)
    rax = rbx
```

Why it matters:

Branch misprediction costs roughly:

```
15–25 CPU cycles
```

`cmov` avoids a branch entirely.

Common use:

```
max/min operations
order book comparisons
risk limits
```

---

# 4. `PREFETCH` — load data into cache early

Example:

```asm
prefetcht0 [rdi+64]
```

This tells the CPU:

```
load this memory into L1/L2 cache soon
```

Useful for:

* parsing market data streams
* order book updates
* sequential structures

Typical latency savings:

```
100ns → 4ns (cache hit)
```

---

# 5. `PAUSE` — spin-loop optimization

```asm
pause
```

Used inside **busy-wait loops**.

Example:

```asm
spin:
    mov rax, [flag]
    test rax, rax
    jnz done
    pause
    jmp spin
```

Benefits:

* reduces power
* improves hyper-threading fairness
* prevents pipeline stalls

Used in lock-free queues.

---

# 6. `LFENCE` — load memory barrier

```asm
lfence
```

Guarantees:

```
all previous loads complete before next loads
```

Important for:

* timing measurement
* memory ordering
* preventing speculative execution issues

Common pattern:

```asm
lfence
rdtsc
```

---

# 7. `SFENCE` — store barrier

```asm
sfence
```

Guarantees:

```
all stores finish before later stores
```

Important in:

* lock-free structures
* memory-mapped I/O
* networking buffers

---

# 8. `MFENCE` — full memory barrier

```asm
mfence
```

Guarantees ordering of **all loads and stores**.

Used in:

```
multi-threaded lock-free algorithms
```

But it is expensive, so often avoided.

---

# 9. `LOCK CMPXCHG` — atomic compare and swap

Core primitive for **lock-free data structures**.

```asm
lock cmpxchg [mem], rbx
```

Meaning:

```
if (mem == rax)
    mem = rbx
else
    rax = mem
```

This powers:

* lock-free queues
* ring buffers
* atomic state machines

Most `std::atomic` operations compile to this.

---

# 10. `XADD` — atomic fetch-add

```asm
lock xadd [counter], rax
```

Meaning:

```
tmp = mem
mem += rax
rax = tmp
```

Used for:

* atomic counters
* sequence numbers
* work distribution

---

# Bonus instruction every HFT engineer sees

### `BSWAP` — byte swap

```asm
bswap eax
```

Converts:

```
network byte order ↔ host order
```

Very common in:

* market data parsing
* binary protocol decoding

---

# Example: branchless max in assembly

```asm
mov rax, a
mov rbx, b
cmp rax, rbx
cmovl rax, rbx
```

Equivalent C:

```c
return a > b ? a : b;
```

But without branch misprediction.

---

# Typical optimized HFT hot loop

You might see something like:

```asm
prefetcht0 [rdi+64]

mov rax, [rdi]
cmp rax, rbx
cmovg rbx, rax

pause
```

This:

* prefetches next order book level
* compares prices branchlessly
* keeps spin loop efficient.

---

# The real skill: reading compiler output

Low-latency engineers often inspect code like this:

```
objdump -d
perf annotate
```

to verify the compiler produced:

```
cmov instead of branch
vector instructions
no unnecessary memory loads
```

---

✅ If you'd like, I can also show something **very valuable for HFT engineers**:

* **10 assembly patterns compilers generate for C++ code**
* **how a branch misprediction actually flushes the CPU pipeline**
* **a real order-book update compiled to x86 assembly** (very insightful).
