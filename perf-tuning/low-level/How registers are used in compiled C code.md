
# How registers are used in compiled C code

Registers are **the primary workspace of compiled C code**. When a C compiler (like GCC or Clang) translates C into assembly for the x86-64 architecture, it tries to keep **as many variables as possible inside CPU registers** instead of memory because registers are dramatically faster.

Below is a practical explanation from C → assembly → registers.

---

# 1. Simple C Example

C code:

```c
int add(int a, int b) {
    int c = a + b;
    return c;
}
```

Compile (conceptually):

```
gcc -O2 add.c
```

Assembly (simplified):

```asm
add:
    mov eax, edi
    add eax, esi
    ret
```

Registers used:

| Register | Meaning         |
| -------- | --------------- |
| `EDI`    | first argument  |
| `ESI`    | second argument |
| `EAX`    | return value    |

So the CPU executes:

```
EAX = EDI + ESI
```

No RAM access at all. Everything stays in **registers**.

---

# 2. How Function Arguments Use Registers

Modern x86-64 calling convention (System V used by Linux/macOS):

| Argument | Register |
| -------- | -------- |
| 1st      | RDI      |
| 2nd      | RSI      |
| 3rd      | RDX      |
| 4th      | RCX      |
| 5th      | R8       |
| 6th      | R9       |

Example C:

```c
int sum(int a, int b, int c) {
    return a + b + c;
}
```

Assembly:

```asm
sum:
    mov eax, edi
    add eax, esi
    add eax, edx
    ret
```

Registers:

```
EDI = a
ESI = b
EDX = c
EAX = return value
```

---

# 3. Local Variables in Registers

Example:

```c
int f() {
    int a = 5;
    int b = 7;
    int c = a + b;
    return c;
}
```

Assembly (optimized):

```asm
mov eax, 12
ret
```

The compiler did **constant folding**.

But if values are dynamic:

```c
int f(int x) {
    int a = x + 5;
    int b = a * 2;
    return b;
}
```

Assembly:

```asm
lea eax, [rdi+5]
add eax, eax
ret
```

Registers:

```
RDI = x
EAX = a
EAX = b
```

The same register is reused.

---

# 4. Register Allocation (Compiler Magic)

Compilers try to **map variables → registers**.

Example C:

```c
int f(int a, int b) {
    int x = a + b;
    int y = x * 3;
    int z = y + 5;
    return z;
}
```

Possible register mapping:

| Variable | Register |
| -------- | -------- |
| a        | RDI      |
| b        | RSI      |
| x        | RAX      |
| y        | RAX      |
| z        | RAX      |

Assembly:

```asm
mov eax, edi
add eax, esi
lea eax, [rax + rax*2]
add eax, 5
ret
```

Notice something important:

```
x → y → z
all reuse EAX
```

This is called **register reuse**.

---

# 5. When Registers Are Not Enough (Spilling)

CPU only has **16 general registers**.

If there are too many variables:

```c
int f(int a,int b,int c,int d,int e,int f,int g,int h)
{
    int x1=a+b;
    int x2=c+d;
    int x3=e+f;
    int x4=g+h;
    return x1+x2+x3+x4;
}
```

The compiler may **spill variables to the stack**.

Assembly (simplified):

```asm
mov eax, edi
add eax, esi
mov [rsp-4], eax
```

Here:

```
[rsp-4]
```

means **temporary variable stored in stack memory**.

This is called:

```
register spilling
```

---

# 6. Registers for Loops

Example:

```c
int sum(int *arr, int n) {
    int s = 0;
    for(int i=0;i<n;i++)
        s += arr[i];
    return s;
}
```

Typical register usage:

| Register | Role          |
| -------- | ------------- |
| RDI      | array pointer |
| ESI      | n             |
| EAX      | sum           |
| ECX      | loop index    |

Assembly idea:

```asm
xor eax, eax
xor ecx, ecx

loop:
add eax, [rdi + rcx*4]
inc ecx
cmp ecx, esi
jl loop

ret
```

Registers hold:

```
EAX = sum
ECX = i
RDI = arr
ESI = n
```

---

# 7. Pointer Access

C:

```c
int x = arr[i];
```

Assembly:

```asm
mov eax, [rdi + rcx*4]
```

Meaning:

```
address = RDI + RCX*4
load into EAX
```

Registers are used for:

```
base pointer
index
result
```

---

# 8. Stack Registers

Registers controlling stack:

| Register | Meaning       |
| -------- | ------------- |
| RSP      | stack pointer |
| RBP      | stack frame   |

Example function:

```asm
push rbp
mov rbp, rsp
sub rsp, 32
```

This creates **local variable space on stack**.

---

# 9. SIMD Registers in C

If you compile with vectorization (`-O3`):

```c
for(int i=0;i<n;i++)
    c[i] = a[i] + b[i];
```

Compiler may use:

```
YMM registers (AVX)
```

Assembly:

```asm
vmovups ymm0, [rdi]
vmovups ymm1, [rsi]
vaddps ymm0, ymm0, ymm1
vmovups [rdx], ymm0
```

One instruction processes:

```
8 floats simultaneously
```

---

# 10. What the Compiler Optimizes For

Compilers try to:

```
keep variables in registers as long as possible
```

Because latency comparison:

| Location | Latency     |
| -------- | ----------- |
| Register | ~1 cycle    |
| L1 cache | ~4 cycles   |
| L2 cache | ~12 cycles  |
| RAM      | ~100 cycles |

So **register allocation is one of the most important compiler optimizations**.

---

# 11. Real Visualization

Example C:

```c
int f(int a,int b){
    int c=a+b;
    int d=c*2;
    return d+1;
}
```

Register flow:

```
RDI = a
RSI = b

EAX = RDI + RSI
EAX = EAX * 2
EAX = EAX + 1

return EAX
```

Everything in **one register**.

---

✅ **Key takeaway**

Compiled C code is basically:

```
load values → registers
compute → registers
store result → memory (if needed)
```

Registers are the **CPU’s working variables**.

---

If you'd like, I can also show something extremely useful for low-level programmers:

**How a modern CPU actually has ~200+ physical registers using "register renaming" even though x86 exposes only 16 registers.**

This is one of the **most important secrets behind modern CPU performance**.
