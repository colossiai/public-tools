# What is the effect of "cmp  op1, op2"

In **x86 assembly**, the instruction:

```
cmp op1, op2
```

**compares two operands by performing a subtraction internally**:

```
op1 - op2
```

But **the result is NOT stored anywhere**.
It only **updates the CPU status flags** in the **FLAGS register / RFLAGS register**.

These flags are then used by conditional instructions like `je`, `jg`, `jl`, etc.

---

# 1. Conceptual Meaning

```
cmp op1, op2
```

is equivalent to:

```
temp = op1 - op2
update_flags(temp)
discard temp
```

So it **sets flags exactly like a `sub` instruction**, but **does not store the result**.

---

# 2. Flags Affected

`cmp` mainly affects these flags:

| Flag   | Meaning       | Condition        |
| ------ | ------------- | ---------------- |
| **ZF** | Zero Flag     | op1 == op2       |
| **SF** | Sign Flag     | result < 0       |
| **CF** | Carry Flag    | unsigned borrow  |
| **OF** | Overflow Flag | signed overflow  |
| **PF** | Parity Flag   | parity of result |

---

# 3. Example

```asm
mov eax, 5
cmp eax, 3
```

Internally:

```
5 - 3 = 2
```

Flags:

```
ZF = 0
SF = 0
CF = 0
```

So:

```
jg label     ; jump if greater
```

will jump.

---

# 4. Example: Equal

```asm
mov eax, 5
cmp eax, 5
```

Internally:

```
5 - 5 = 0
```

Flags:

```
ZF = 1
```

Then:

```
je label
```

will jump.

---

# 5. Signed vs Unsigned Comparisons

`cmp` itself **does not know signed vs unsigned**.

The **jump instruction determines interpretation**.

### Signed comparison

```
cmp eax, ebx
jg label   ; signed >
jl label   ; signed <
```

### Unsigned comparison

```
cmp eax, ebx
ja label   ; unsigned >
jb label   ; unsigned <
```

---

# 6. Common Pattern in Compiled C

C code:

```c
if (a > b)
```

Typical assembly:

```asm
cmp eax, ebx
jg  label
```

---

# 7. Important: Operand Order

This is a common beginner mistake.

```
cmp op1, op2
```

means

```
op1 - op2
```

Example:

```
cmp eax, ebx
```

means

```
eax - ebx
```

---

# 8. Relation to `test`

Another similar instruction is:

```
test op1, op2
```

Difference:

| Instruction | Operation   |
| ----------- | ----------- |
| `cmp`       | subtraction |
| `test`      | bitwise AND |

---

✅ **Summary**

```
cmp op1, op2
```

* performs `op1 - op2`
* discards result
* sets CPU flags
* used by conditional jumps

---

If you'd like, I can also show a **real `objdump` example of how `cmp` appears in compiled C code**, which is extremely useful for reverse engineering and performance tuning.
