# x86-64 Assembly Quick Reference

## Register Overview

### General Purpose Registers (64-bit)

| 64-bit | 32-bit | 16-bit | 8-bit | Purpose/Convention |
|--------|--------|--------|-------|-------------------|
| rax    | eax    | ax     | al    | Accumulator, return value |
| rbx    | ebx    | bx     | bl    | Base (callee-saved) |
| rcx    | ecx    | cx     | cl    | Counter, 4th argument |
| rdx    | edx    | dx     | dl    | Data, 3rd argument |
| rsi    | esi    | si     | sil   | Source index, 2nd argument |
| rdi    | edi    | di     | dil   | Destination index, 1st argument |
| rbp    | ebp    | bp     | bpl   | Base pointer (callee-saved) |
| rsp    | esp    | sp     | spl   | Stack pointer |
| r8-r15 | r8d-r15d | r8w-r15w | r8b-r15b | Extended registers |

### Special Registers

- **rip** - Instruction pointer (program counter)
- **rflags** - Status flags (ZF, SF, CF, OF, etc.)

## System V AMD64 Calling Convention

### Function Arguments (Linux)

| Argument | Register | Argument | Register |
|----------|----------|----------|----------|
| 1st      | rdi      | 4th      | rcx      |
| 2nd      | rsi      | 5th      | r8       |
| 3rd      | rdx      | 6th      | r9       |
| 7+       | stack (right to left) |

### Syscall Convention

| Item | Register |
|------|----------|
| Syscall number | rax |
| Return value   | rax |
| Arguments      | rdi, rsi, rdx, r10, r8, r9 |

**Note:** Syscalls use r10 instead of rcx for 4th argument!

### Register Preservation

- **Caller-saved** (caller must save if needed): rax, rcx, rdx, rsi, rdi, r8-r11
- **Callee-saved** (callee must preserve): rbx, rbp, r12-r15

## Common Instructions

### Data Movement

```nasm
mov  dest, src      ; dest = src
movzx dest, src     ; Move with zero-extension
movsx dest, src     ; Move with sign-extension
lea  dest, [addr]   ; Load effective address
xchg op1, op2       ; Exchange/swap values
```

### Arithmetic

```nasm
add  dest, src      ; dest = dest + src
sub  dest, src      ; dest = dest - src
inc  dest           ; dest = dest + 1
dec  dest           ; dest = dest - 1
neg  dest           ; dest = -dest (two's complement)

mul  src            ; rdx:rax = rax * src (unsigned)
imul src            ; rdx:rax = rax * src (signed)
imul dest, src      ; dest = dest * src
imul dest, src, imm ; dest = src * imm

div  src            ; rax = rdx:rax / src, rdx = remainder (unsigned)
idiv src            ; rax = rdx:rax / src, rdx = remainder (signed)
```

**Understanding rdx:rax notation:**

The notation `rdx:rax` represents a **128-bit value** formed by concatenating two 64-bit registers:
- `rdx` holds the **upper/high 64 bits** (bits 127-64)
- `rax` holds the **lower 64 bits** (bits 63-0)

**Example with mul:**
```nasm
mov rax, 0x0000000100000000    ; rax = 4,294,967,296 (2^32)
mov rbx, 2                      ; rbx = 2
mul rbx                         ; Multiply: rax * rbx
; Result: rdx:rax = 0x00000002_00000000 (128-bit value)
;         rdx = 0x0000000000000002 (high 64 bits)
;         rax = 0x0000000000000000 (low 64 bits)
; This represents 8,589,934,592 as a 128-bit number
```

**Why 128 bits?**
Multiplying two 64-bit numbers can produce a 128-bit result:
- Maximum 64-bit value: 2^64 - 1
- (2^64 - 1) × (2^64 - 1) = 2^128 - 2^65 + 1 (requires 128 bits!)

**For small numbers:**
```nasm
mov rax, 10
mov rbx, 20
mul rbx             ; 10 × 20 = 200
; Result: rdx = 0 (high bits all zero)
;         rax = 200 (entire result fits in low 64 bits)
```

**For division (rdx:rax as input):**
```nasm
; Divide 128-bit rdx:rax by src
xor rdx, rdx        ; Clear rdx (high bits = 0)
mov rax, 100        ; Low bits = 100
mov rbx, 7          ; Divisor
div rbx             ; Divide 100 by 7
; Result: rax = 14 (quotient)
;         rdx = 2 (remainder: 100 = 14×7 + 2)
```

**Common pattern:**
```nasm
; Before unsigned division, clear rdx
xor rdx, rdx        ; rdx:rax now represents just rax

; Before signed division, sign-extend rax into rdx
cqo                 ; rdx:rax = sign-extended rax
```

### Logical & Bitwise

```nasm
and  dest, src      ; Bitwise AND
or   dest, src      ; Bitwise OR
xor  dest, src      ; Bitwise XOR
not  dest           ; Bitwise NOT

shl  dest, count    ; Shift left (logical)
shr  dest, count    ; Shift right (logical)
sal  dest, count    ; Shift arithmetic left
sar  dest, count    ; Shift arithmetic right
rol  dest, count    ; Rotate left
ror  dest, count    ; Rotate right
```

### Comparison & Test

```nasm
cmp  op1, op2       ; Compare (sets flags: op1 - op2), set CPU flags, and used by je/jg/jl etc
test op1, op2       ; Test (sets flags: op1 & op2)
```

### Control Flow

```nasm
jmp  label          ; Unconditional jump
call label          ; Call function
ret                 ; Return from function

; Conditional jumps (after cmp/test)
je/jz    label      ; Jump if equal/zero
jne/jnz  label      ; Jump if not equal/not zero
jg/jnle  label      ; Jump if greater (signed)
jge/jnl  label      ; Jump if greater or equal (signed)
jl/jnge  label      ; Jump if less (signed)
jle/jng  label      ; Jump if less or equal (signed)
ja/jnbe  label      ; Jump if above (unsigned)
jae/jnb  label      ; Jump if above or equal (unsigned)
jb/jnae  label      ; Jump if below (unsigned)
jbe/jna  label      ; Jump if below or equal (unsigned)

loop label          ; Decrement rcx, jump if rcx != 0
```

### Stack Operations

```nasm
push src            ; rsp -= 8, [rsp] = src
pop  dest           ; dest = [rsp], rsp += 8
```

### String Operations (with rsi/rdi)

```nasm
movsb/movsw/movsd/movsq  ; Move string (byte/word/dword/qword)
stosb/stosw/stosd/stosq  ; Store string
lodsb/lodsw/lodsd/lodsq  ; Load string
cmpsb/cmpsw/cmpsd/cmpsq  ; Compare strings
scasb/scasw/scasd/scasq  ; Scan string

rep     ; Repeat while rcx != 0
repz    ; Repeat while rcx != 0 and ZF = 1
repnz   ; Repeat while rcx != 0 and ZF = 0
```

## NASM Directives

```nasm
section .data       ; Initialized data
section .bss        ; Uninitialized data
section .text       ; Code

db  0x12            ; Define byte (1 byte)
dw  0x1234          ; Define word (2 bytes)
dd  0x12345678      ; Define dword (4 bytes)
dq  0x123456789ABCDEF0 ; Define qword (8 bytes)

resb 100            ; Reserve 100 bytes (in .bss)
resw 50             ; Reserve 50 words
resd 25             ; Reserve 25 dwords
resq 10             ; Reserve 10 qwords

equ                 ; Define constant
%define             ; Define macro constant
%macro / %endmacro  ; Define macro

global _start       ; Export symbol
extern printf       ; Import symbol
```

## CPU Flags (RFLAGS)

| Flag | Name | Set when |
|------|------|----------|
| ZF   | Zero | Result is zero |
| SF   | Sign | Result is negative |
| CF   | Carry | Unsigned overflow |
| OF   | Overflow | Signed overflow |
| PF   | Parity | Even number of bits set |

## Common Syscalls (Linux x86-64)

| Syscall | Number | Arguments |
|---------|--------|-----------|
| read    | 0      | fd, buffer, count |
| write   | 1      | fd, buffer, count |
| open    | 2      | filename, flags, mode |
| close   | 3      | fd |
| exit    | 60     | error_code |
| fork    | 57     | - |
| execve  | 59     | filename, argv, envp |

**Full list:** `/usr/include/x86_64-linux-gnu/asm/unistd_64.h`

## Memory Addressing Modes

```nasm
mov rax, 42         ; Immediate
mov rax, [var]      ; Direct
mov rax, [rbx]      ; Indirect
mov rax, [rbx + 8]  ; Base + displacement
mov rax, [rbx + rcx*4]      ; Base + index*scale
mov rax, [rbx + rcx*4 + 8]  ; Base + index*scale + displacement

; Scale can be 1, 2, 4, or 8
```

## Useful Idioms

```nasm
; Clear register (faster than mov rax, 0)
xor rax, rax

; Set register to -1
or  rax, -1

; Multiply by power of 2
shl rax, 3          ; Multiply by 8

; Divide by power of 2 (unsigned)
shr rax, 2          ; Divide by 4

; Check if even/odd
test rax, 1         ; ZF=1 if even, ZF=0 if odd

; Conditional move (branchless)
cmp rax, rbx
cmovg rax, rbx      ; if rax > rbx: rax = rbx

; Sign-extend rax into rdx:rax (before idiv)
cqo

; Zero-extend (before div)
xor rdx, rdx
```

## Compile & Debug Workflow

```bash
# Assemble
nasm -f elf64 -g -F dwarf program.asm -o program.o

# Link
ld program.o -o program

# Run
./program
echo $?  # Check exit code

# Disassemble
objdump -d program
objdump -M intel -d program  # Intel syntax

# Debug with GDB
gdb ./program
(gdb) break _start
(gdb) run
(gdb) info registers
(gdb) stepi              # Step one instruction
(gdb) x/10gx $rsp        # Examine stack (10 qwords in hex)
(gdb) x/s $rsi           # Examine as string
(gdb) disas              # Disassemble current function
```

## Tips

1. **Always align stack to 16 bytes before calling C functions**
2. **Use `cqo` before `idiv`, `xor rdx,rdx` before `div`**
3. **Writing to 32-bit register zeros upper 32 bits**
4. **`test` is non-destructive, `and` modifies destination**
5. **`lea` is useful for arithmetic without affecting flags**
6. **Stack grows downward (toward lower addresses)**
7. **Check syscall numbers in `/usr/include/asm/unistd_64.h`**
