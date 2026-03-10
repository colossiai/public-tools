`what is "perf annotate"`

`perf annotate` is a command from **perf** that shows **which assembly instructions inside a function consume CPU time**.

It combines:

* **profiling data** (where CPU cycles were spent)
* **disassembly** (actual machine instructions)

So you can see **hot instructions line-by-line**.

It is extremely useful for **performance engineering, low-latency systems, and HFT optimization**.

---

# 1. What `perf annotate` does

It answers this question:

> Inside a function, **which instruction is slow?**

It shows:

```
percent   assembly instruction
```

Example output:

```
Percent | Source code & Assembly
----------------------------------------------
  45.2% | mov    (%rax),%rdx
  22.8% | add    %rdx,%rcx
  18.1% | cmp    %rcx,%r8
   9.5% | jne    0x401230
```

Meaning:

* **45% of CPU cycles** were spent on the memory load
* **22%** on addition
* **18%** on comparison
* **9%** on branch

This helps identify:

* cache misses
* branch misprediction
* slow instructions

---

# 2. Typical workflow

### Step 1 — compile with debug info

```bash
gcc -O3 -g program.c -o program
```

---

### Step 2 — record performance

```bash
perf record ./program
```

This collects **CPU samples**.

---

### Step 3 — analyze

```bash
perf annotate
```

You will see **hot functions and instructions**.

---

# 3. Example

Suppose this C code:

```c
int sum(int *a, int n) {
    int s = 0;
    for (int i = 0; i < n; i++)
        s += a[i];
    return s;
}
```

`perf annotate` might show:

```
Percent | Assembly
--------------------------------
 60.12% | mov    (%rax,%rdx,4),%ecx
 20.30% | add    %ecx,%esi
 10.50% | add    $0x1,%edx
  9.08% | cmp    %edx,%r8d
```

Interpretation:

| Instruction | Meaning                     |
| ----------- | --------------------------- |
| `mov`       | memory load (dominant cost) |
| `add`       | arithmetic                  |
| `cmp`       | loop condition              |

This tells you **memory access dominates performance**.

---

# 4. Difference from `objdump`

You asked earlier about `objdump`.

| Tool            | What it shows                   |
| --------------- | ------------------------------- |
| `objdump -d`    | full assembly                   |
| `perf annotate` | **assembly + runtime CPU cost** |

Example:

`objdump`:

```
mov (%rax), %rdx
add %rdx, %rcx
```

`perf annotate`:

```
45.2%  mov (%rax), %rdx
22.1%  add %rdx, %rcx
```

So `perf annotate` answers:

> Which instructions are actually **hot**.

---

# 5. Why low-latency engineers love it

It reveals performance killers like:

### 1️⃣ Cache misses

Example hot instruction:

```
mov (%rax),%rdx
```

High % → memory bottleneck.

---

### 2️⃣ Branch misprediction

Example:

```
jne 0x401230
```

If high %, branch predictor failing.

---

### 3️⃣ Vectorization problems

You may see scalar instructions:

```
add
mul
```

Instead of SIMD:

```
vaddps
vmulpd
```

Meaning compiler didn't vectorize.

---

# 6. Advanced usage

### Show annotation for specific function

```
perf annotate -s function_name
```

---

### With Intel syntax

```
perf annotate --stdio --asm-raw
```

---

### Navigate in TUI

```
perf annotate
```

Interactive view:

```
↑ ↓ scroll
Enter open function
q exit
```

---

# 7. Real production example

In high-frequency trading systems, engineers often discover:

```
70%  mov (%rdi,%rax,8),%rdx
```

Meaning:

> Memory latency dominates — data structure layout must be improved.

So they may:

* restructure arrays
* align cache lines
* prefetch memory
* reduce pointer chasing

---

# 8. Mental model

Think of `perf annotate` as:

```
objdump + profiler
```

or

```
assembly + heatmap
```

It shows **where CPU time is burned at instruction level**.

---

✅ **One of the most powerful performance tools in Linux.**

---

If you'd like, I can also show something extremely useful for systems engineers:

**“A real `perf annotate` investigation that finds a 5× performance bug in 3 minutes.”**

This is exactly how engineers at companies like **Meta Platforms**, **Google**, and **Jane Street** debug performance issues.
