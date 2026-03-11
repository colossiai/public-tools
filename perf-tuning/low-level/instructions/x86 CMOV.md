# Explain x86 CMOV* instructions


The **CMOV*** (Conditional Move) instructions in x86 Instruction Set Architecture are used to **conditionally copy data between registers without using a branch**.

They are important for **low-latency / high-performance code** because they help avoid **branch misprediction penalties** in modern CPUs.

---

# 1. What CMOV Does

Normal branch code:

```asm
cmp rax, rbx
jl  less
mov rcx, rax
jmp end
less:
mov rcx, rbx
end:
```

Branchless version using **CMOV**:

```asm
mov rcx, rax
cmp rax, rbx
cmovl rcx, rbx
```

Meaning:

```
if (rax < rbx)
    rcx = rbx
else
    rcx = rax
```

No branch instruction (`jcc`) is used.

---

# 2. Basic Syntax

```
cmovcc destination, source
```

* **destination** → register only
* **source** → register or memory
* **cc** → condition code

Example:

```asm
cmp rax, rbx
cmovg rcx, rax
```

Meaning:

```
if (rax > rbx)
    rcx = rax
```

---

# 3. Common CMOV Instructions

| Instruction       | Meaning                  | Condition      |
| ----------------- | ------------------------ | -------------- |
| `cmove` / `cmovz` | move if equal            | ZF=1           |
| `cmovne`          | move if not equal        | ZF=0           |
| `cmovg`           | move if greater (signed) | ZF=0 and SF=OF |
| `cmovge`          | move if greater or equal | SF=OF          |
| `cmovl`           | move if less (signed)    | SF≠OF          |
| `cmovle`          | move if less or equal    | ZF=1 or SF≠OF  |
| `cmova`           | move if above (unsigned) | CF=0 and ZF=0  |
| `cmovae`          | move if above/equal      | CF=0           |
| `cmovb`           | move if below            | CF=1           |
| `cmovbe`          | move if below/equal      | CF=1 or ZF=1   |

These conditions depend on flags set by instructions like:

```
cmp
test
sub
add
```

---

# 4. Why CMOV Is Important (Performance)

Modern CPUs rely heavily on **branch prediction**.

If a branch is mispredicted:

```
pipeline flush penalty ≈ 10–20 cycles
```

CMOV removes the branch:

```
compare → conditional move
```

Typical cost:

```
~1–3 cycles
```

Therefore CMOV is useful when:

* branch prediction is **unpredictable**
* inside **tight loops**
* **high-frequency trading / low latency systems**

---

# 5. Classic Example: Branchless Max

Branch version:

```c
int max(int a, int b){
    if(a > b)
        return a;
    else
        return b;
}
```

Compiler may produce:

```asm
cmp edi, esi
cmovl edi, esi
mov eax, edi
ret
```

---

# 6. Important Limitations

### 1. Destination must be register

❌ invalid

```
cmovg [rax], rbx
```

✔ valid

```
cmovg rax, rbx
```

---

### 2. Source can be memory

```
cmovg rax, [rbx]
```

---

### 3. Still executes speculatively

CPU still **reads the source operand** even if move is not taken.

This matters for:

* cache effects
* side channel attacks

Example:

```
cmovg rax, [secret_address]
```

Memory may still be accessed.

---

# 7. CMOV vs Branch

| Case                 | Faster |
| -------------------- | ------ |
| Predictable branch   | Branch |
| Unpredictable branch | CMOV   |
| Simple arithmetic    | CMOV   |
| Large memory access  | Branch |

---

# 8. When Compilers Emit CMOV

Compilers like GCC and Clang generate CMOV when:

* optimization enabled (`-O2`)
* branch prediction uncertain
* small conditional assignment

Example:

```bash
gcc -O2 max.c
```

---

# 9. Real HFT Trick

A classic **branchless clamp**:

```asm
; x = max(x, 0)

xor rbx, rbx
cmp rax, rbx
cmovl rax, rbx
```

Used in:

* risk checks
* price bounds
* array indexing

---

✅ **Rule of thumb for low-latency engineers**

```
Unpredictable branch → use CMOV
Predictable branch → keep branch
```

---

If you'd like, I can also show:

**"10 CMOV tricks used in high-frequency trading systems"**
(including branchless min/max, saturating math, fast order book comparisons).
