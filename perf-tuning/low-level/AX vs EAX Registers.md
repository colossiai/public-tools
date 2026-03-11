# for x86 registers, are ax and eax difference registers? or ax is part of eax?


In **x86 architecture**, **`AX` is part of `EAX`**, not a separate register.

Think of it as **different-sized views of the same physical register**.

### Register hierarchy

```
RAX  (64-bit)   ← full register in x86-64
│
└── EAX (32-bit)
     │
     └── AX (16-bit)
          │
          ├── AH (upper 8 bits)
          └── AL (lower 8 bits)
```

| Name  | Size   | Meaning                     |
| ----- | ------ | --------------------------- |
| `RAX` | 64-bit | Full register (x86-64 mode) |
| `EAX` | 32-bit | Lower 32 bits of RAX        |
| `AX`  | 16-bit | Lower 16 bits of EAX        |
| `AH`  | 8-bit  | High byte of AX             |
| `AL`  | 8-bit  | Low byte of AX              |

### Bit layout

```
RAX:  [63.........................0]

EAX:              [31.............0]

AX:                       [15.....0]

AH:                       [15..8]
AL:                       [7...0]
```

### Important behavior

#### 1️⃣ Writing to `EAX` zero-extends into `RAX`

```
mov eax, 1
```

Result:

```
RAX = 0x0000000000000001
```

Upper 32 bits are **cleared automatically**.

This is a **special rule in x86-64** used for performance.

---

#### 2️⃣ Writing to `AX`, `AH`, or `AL` does **NOT** clear upper bits

Example:

```
mov rax, 0x123456789ABCDEF0
mov ax, 1
```

Result:

```
RAX = 0x123456789ABC0001
```

Only **lower 16 bits changed**.

---

### Example

```
mov eax, 0x11223344
```

Registers become:

```
RAX = 0x0000000011223344
EAX = 0x11223344
AX  = 0x3344
AH  = 0x33
AL  = 0x44
```

---

### Why this matters (important for low-latency / asm optimization)

Since you're studying **assembly for low-latency systems**, a key rule is:

**Prefer writing to `EAX` instead of `AX` when possible.**

Reason:

* Writing `EAX` **breaks dependency chains**
* Writing `AX/AH/AL` can cause **partial register stalls** on some CPUs

Example:

Good:

```
xor eax, eax
```

Bad (can cause partial register dependency):

```
xor ax, ax
```

---

✅ **Summary**

* `AX` is the **lower 16 bits of `EAX`**
* `EAX` is the **lower 32 bits of `RAX`**
* They are **different views of the same register**

```
RAX → EAX → AX → AH/AL
```

---

If you want, I can also show **all x86 registers and their sub-registers (RAX/RBX/RCX/RDX etc.) in one table**, which is extremely useful when learning assembly for **HFT / low-latency programming**.
