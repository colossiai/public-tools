# Introduce Apple CPU registers

Apple CPUs (Apple Silicon like **Apple M1**, **Apple M2**, **Apple M3**) use the **ARM64** instruction set.
Their registers follow the **AArch64 register model**, which is very different from the older **x86** registers like `eax`, `ebx`, etc.

Below is a practical overview useful for systems programmers.

---

# 1. General Purpose Registers (GPR)

Apple ARM64 CPUs have **31 general-purpose registers**.

| Register  | Description                                   |
| --------- | --------------------------------------------- |
| x0 – x7   | Function arguments / return values            |
| x8        | Indirect return value register                |
| x9 – x15  | Temporary registers                           |
| x16 – x17 | Intra-procedure call scratch registers        |
| x18       | Platform register (reserved on Apple systems) |
| x19 – x28 | Callee-saved registers                        |
| x29       | Frame pointer (FP)                            |
| x30       | Link register (LR) – return address           |

Important special register:

| Register | Meaning       |
| -------- | ------------- |
| SP       | Stack pointer |

### Width variants

Each register has **32-bit and 64-bit views**:

| 64-bit | 32-bit |
| ------ | ------ |
| x0     | w0     |
| x1     | w1     |
| ...    | ...    |

Example:

```asm
mov x0, #10     // 64-bit
mov w0, #10     // 32-bit
```

---

# 2. Stack Pointer

```
SP
```

Points to the current stack top.

Typical function prologue:

```asm
stp x29, x30, [sp, -16]!
mov x29, sp
```

This:

1. Saves frame pointer
2. Saves return address
3. Creates a new stack frame

---

# 3. Program Counter (PC)

```
PC
```

* Holds the address of the next instruction
* Usually **not directly writable**

Branches modify it:

```asm
b label
blr x3
ret
```

---

# 4. SIMD / Vector Registers

Apple CPUs are extremely strong in vector computing.

They implement **NEON SIMD registers**.

Total:

```
v0 – v31
```

Each register is **128-bit**.

Views:

| Name | Size    |
| ---- | ------- |
| v0   | 128-bit |
| q0   | 128-bit |
| d0   | 64-bit  |
| s0   | 32-bit  |
| h0   | 16-bit  |
| b0   | 8-bit   |

Example:

```asm
add v0.4s, v1.4s, v2.4s
```

Meaning:

```
v0 = v1 + v2
4 parallel 32-bit integers
```

This is heavily used in:

* video
* audio
* machine learning
* graphics

---

# 5. Floating Point Registers

Floating-point operations also use:

```
v0 – v31
```

Example:

```asm
fadd d0, d1, d2
```

---

# 6. Condition Flags (PSTATE)

Status flags stored in **PSTATE**.

Important flags:

| Flag | Meaning  |
| ---- | -------- |
| N    | Negative |
| Z    | Zero     |
| C    | Carry    |
| V    | Overflow |

Example:

```asm
cmp x0, x1
b.eq equal
```

---

# 7. Special Apple Notes

Apple Silicon reserves:

```
x18
```

for **platform use** (thread pointer / system runtime).

You should **not use x18 in user assembly**.

---

# 8. Function Calling Convention (Important)

On Apple ARM64 ABI:

Arguments:

```
x0 – x7
```

Return value:

```
x0
```

Example C:

```c
int add(int a, int b) {
    return a + b;
}
```

Compiled assembly:

```asm
add:
    add w0, w0, w1
    ret
```

Explanation:

```
w0 = a
w1 = b
return in w0
```

---

# 9. Register Overview Diagram

```
General Purpose
----------------
x0  x1  x2  x3  x4  x5  x6  x7   (arguments)
x8
x9-x15                         (temp)
x16-x17                        (scratch)
x18                            (reserved Apple)
x19-x28                        (callee saved)
x29                            (frame pointer)
x30                            (link register)

Special
-------
SP    stack pointer
PC    program counter
PSTATE flags

Vector
------
v0 – v31 (128-bit SIMD / FP)
```

---

# 10. Apple CPU vs x86 Registers

| x86 | ARM64 (Apple) |
| --- | ------------- |
| eax | w0            |
| rax | x0            |
| rbx | x19           |
| rsp | sp            |
| rip | pc            |

ARM64 has:

* **more registers**
* **cleaner calling convention**
* **fixed instruction size (32-bit)**

Which simplifies CPU pipelines.

---

✅ If you'd like, I can also show:

1. **Real compiled assembly from Clang on Apple Silicon**
2. **How Go / Java / C compilers map variables to registers**
3. **A diagram of register usage during a function call on Apple M-series CPUs** (very useful for systems engineers).
