# show c strstr() source code


The C standard library function **`strstr()`** finds the **first occurrence of a substring inside another string**.

Signature:

```c
char *strstr(const char *haystack, const char *needle);
```

* **haystack** → the big string to search in
* **needle** → the substring to search for
* Returns a pointer to the first match or `NULL`.

Below is a **simple reference implementation (similar to many libc implementations)**.

---

# Minimal `strstr()` Source Code

```c
char *strstr(const char *haystack, const char *needle)
{
    if (!*needle)
        return (char *)haystack;

    for (; *haystack; haystack++) {
        const char *h = haystack;
        const char *n = needle;

        while (*h && *n && *h == *n) {
            h++;
            n++;
        }

        if (!*n)
            return (char *)haystack;
    }

    return NULL;
}
```

---

# How It Works

Example:

```
haystack = "hello world"
needle   = "wor"
```

Algorithm:

```
hello world
^
compare "hel" vs "wor" -> fail

 hello world
 ^
compare "ell" vs "wor" -> fail

  hello world
  ^
compare "llo" vs "wor" -> fail

       hello world
       ^
compare "wor" vs "wor" -> success
```

Returns pointer to:

```
"world"
```

---

# Visual Execution

```
haystack:  a b c d e f g
needle:        d e f
```

Step scan:

```
a b c d e f g
^

a b c d e f g
  ^

a b c d e f g
    ^
    d e f
    d e f  ✓ match
```

Return pointer to `d`.

---

# Time Complexity

Worst case:

```
O(n * m)
```

Where:

* `n` = length of haystack
* `m` = length of needle

Example worst case:

```
haystack = "aaaaaaaaaaaaaaaaab"
needle   = "aaaab"
```

Many partial matches cause repeated comparisons.

---

# Real libc implementations are MUCH faster

Modern `strstr()` implementations use:

* **Two-Way string matching algorithm**
* **Boyer–Moore–Horspool**
* **SIMD scanning**
* **word-at-a-time comparisons**

For example:

* **glibc `strstr`** is ~300 lines of optimized code.
* Uses **vectorized scanning** for long strings.

---

# Ultra-optimized concept used in libc

Fast libraries do:

```
1. Find first character match quickly (memchr)
2. Then compare remaining substring
```

Pseudo pattern:

```c
while ((p = strchr(haystack, needle[0]))) {
    if (memcmp(p, needle, needle_len) == 0)
        return p;
    haystack = p + 1;
}
```

---

# Dangerous Bug Example

A common mistake:

```c
char buf[8];
if (strstr(input, "admin"))
    strcpy(buf, input);  // buffer overflow
```

If attacker sends:

```
AAAAAAAAAAAAAAAAAAAAAAAAAAAAadmin
```

Overflow occurs.

---

# Want to see something cool?

I can also show you:

1. **The real glibc `strstr()` (SIMD optimized)**
2. **A 40-line Boyer-Moore substring search** (used in search engines)
3. **How attackers exploit `strstr()` in auth bypass bugs**
4. **A visual animation of substring search**

The **glibc implementation is fascinating for systems programmers.** 🚀


# The real glibc strstr() (SIMD optimized)

The real **`strstr()`** in the GNU C Library (glibc) is **much more sophisticated** than the textbook implementation.

It uses **three different strategies depending on the needle length**:

1. **Needle length = 1–3 → specialized fast search**
2. **Needle length ≤ 256 → modified Horspool algorithm**
3. **Needle length > 256 → Two-Way linear-time algorithm** ([Debian Sources][1])

The SIMD parts usually live in helper functions (`memchr`, `memcmp`, `strlen`) that are **vectorized with SSE/AVX**, so `strstr()` indirectly benefits from SIMD scanning.

Below is a **cleaned excerpt from the real glibc source** (simplified but structurally identical).

---

# Real glibc `strstr()` Core (simplified)

```c
char *
STRSTR (const char *haystack, const char *needle)
{
    const unsigned char *hs = (const unsigned char *) haystack;
    const unsigned char *ne = (const unsigned char *) needle;

    /* Empty needle */
    if (ne[0] == '\0')
        return (char *)hs;

    /* Find first character quickly (SIMD strchr underneath) */
    hs = (const unsigned char *)strchr((const char*)hs, ne[0]);
    if (hs == NULL || ne[1] == '\0')
        return (char*)hs;

    /* Small needle specializations */
    if (ne[2] == '\0')
        return strstr2(hs, ne);

    if (ne[3] == '\0')
        return strstr3(hs, ne);

    size_t ne_len = strlen((const char*)ne);
    size_t hs_len = __strnlen((const char*)hs, ne_len | 512);

    if (hs_len < ne_len)
        return NULL;

    /* Early match check */
    if (memcmp(hs, ne, ne_len) == 0)
        return (char*)hs;

    /* Long needles use Two-Way algorithm */
    if (ne_len > 256)
        return two_way_long_needle(hs, hs_len, ne, ne_len);

    const unsigned char *end = hs + hs_len - ne_len;

    uint8_t shift[256];
    memset(shift, 0, sizeof(shift));

    size_t m1 = ne_len - 1;

    /* Build bad-character shift table */
    for (size_t i = 1; i < m1; i++)
        shift[ne[i]] = i;

    while (hs <= end) {
        unsigned char c = hs[m1];

        if (c == ne[m1] && memcmp(hs, ne, m1) == 0)
            return (char*)hs;

        size_t s = shift[c];
        hs += (m1 - s);
    }

    return NULL;
}
```

---

# Why This Is Fast ⚡

### 1️⃣ SIMD scanning for first character

This line:

```c
hs = strchr(hs, ne[0]);
```

On modern x86 CPUs, `strchr` uses **AVX2 / SSE2**:

```
load 32 bytes
compare all 32 bytes with needle char
generate mask
jump to first match
```

So it scans **32 characters per CPU instruction**.

---

### 2️⃣ Horspool skipping

Instead of checking every position:

```
abcxxxxxxxxxxxxxxxxxxxxxxxx
```

If the last character doesn't match:

```
shift forward several bytes
```

Example:

```
needle = "world"
```

Shift table:

```
w -> 4
o -> 3
r -> 2
l -> 1
```

So mismatches jump ahead.

---

### 3️⃣ Two-Way algorithm for long needles

For large substrings (>256 bytes) glibc switches to:

**Two-Way string matching**

Properties:

```
Time complexity: O(n)
Memory: O(1)
Worst case guaranteed linear
```

This avoids catastrophic cases like:

```
haystack = "aaaaaaaaaaaaaaaaaaaaaaaaab"
needle   = "aaaaaaaaaaaaab"
```

---

# Why glibc `strstr` is ~20× faster than naive

Naive:

```
O(n*m)
compare every character
```

glibc:

```
SIMD scanning
skip table jumps
linear-time algorithm fallback
```

Result:

```
Typical speedup: 5×–20×
```

---

# The *really scary part* 😄

On **x86-64**, the functions it calls look like this:

```
strlen-avx2.S
strchr-avx2.S
memcmp-avx2.S
```

Example concept:

```
vmovdqu ymm0, [ptr]
vpcmpeqb ymm1, ymm0, needle
vpmovmskb eax, ymm1
tzcnt eax, eax
```

Meaning:

```
compare 32 characters at once
```

---

✅ **Key takeaway**

Real `strstr()` is a **hybrid of algorithms + SIMD + heuristics**, not a simple nested loop.

---

If you'd like, I can also show a **100-line educational version of glibc `strstr()`** that includes:

* Horspool skip table
* Two-Way algorithm
* SIMD-style scanning idea

It's one of the **best pieces of systems programming code to study.** 🚀

[1]: https://sources.debian.org/src/glibc/2.31-13%2Bdeb11u5/string/strstr.c?utm_source=chatgpt.com "File: strstr.c | Debian Sources"

# show a 100-line educational version of glibc strstr()

Below is a **~100-line educational implementation of `strstr()` inspired by glibc**.
It demonstrates the **three key ideas used in real libc implementations**:

1. **SIMD-style scanning idea** (fast search for first character)
2. **Boyer–Moore–Horspool skip table** for medium needles
3. **Two-Way algorithm fallback** for very long needles

This is **not production libc**, but it mirrors the architecture used in high-performance libraries.

---

# Educational `strstr()` (~100 lines)

```c
#include <stddef.h>
#include <stdint.h>
#include <string.h>

#define LONG_NEEDLE_THRESHOLD 256

/* ---------------------------------------------------
   SIMD-style scanning idea
   (real libc uses AVX/SSE; here we simulate by
   scanning multiple bytes per iteration)
--------------------------------------------------- */
static const char* simd_memchr(const char *s, char c)
{
    const uint64_t *p = (const uint64_t*)s;

    while (1) {
        uint64_t block = *p;

        /* XOR trick to detect matching byte */
        uint64_t mask = block ^ (0x0101010101010101ULL * (unsigned char)c);

        /* detect zero byte */
        if (((mask - 0x0101010101010101ULL) & ~mask & 0x8080808080808080ULL)) {
            const char *b = (const char*)p;
            for (int i = 0; i < 8; i++)
                if (b[i] == c)
                    return b + i;
        }

        p++;
    }
}

/* ---------------------------------------------------
   Two-Way algorithm (simplified educational version)
--------------------------------------------------- */
static const char* two_way_search(
    const char *haystack, size_t hlen,
    const char *needle, size_t nlen)
{
    size_t i = 0;
    size_t period = 1;

    /* compute maximal suffix (simplified) */
    for (size_t j = 1; j < nlen; j++) {
        if (needle[j] == needle[j % period])
            continue;
        if (needle[j] > needle[j % period])
            period = j + 1;
        else
            period = 1;
    }

    while (i + nlen <= hlen) {
        size_t j = 0;

        while (j < nlen && haystack[i + j] == needle[j])
            j++;

        if (j == nlen)
            return haystack + i;

        i += (j < period) ? (j + 1) : period;
    }

    return NULL;
}

/* ---------------------------------------------------
   Main strstr implementation
--------------------------------------------------- */
char *educational_strstr(const char *haystack, const char *needle)
{
    if (!*needle)
        return (char*)haystack;

    size_t nlen = strlen(needle);
    size_t hlen = strlen(haystack);

    if (hlen < nlen)
        return NULL;

    /* ------------------------------------------------
       Step 1: SIMD-style fast search for first char
    ------------------------------------------------ */
    const char *p = simd_memchr(haystack, needle[0]);
    if (!p)
        return NULL;

    haystack = p;
    hlen -= (p - haystack);

    /* ------------------------------------------------
       Step 2: Long needles → Two-Way algorithm
    ------------------------------------------------ */
    if (nlen > LONG_NEEDLE_THRESHOLD) {
        return (char*)two_way_search(haystack, hlen, needle, nlen);
    }

    /* ------------------------------------------------
       Step 3: Horspool skip table
    ------------------------------------------------ */
    uint8_t shift[256];
    memset(shift, nlen, sizeof(shift));

    for (size_t i = 0; i < nlen - 1; i++)
        shift[(unsigned char)needle[i]] = nlen - 1 - i;

    const char *end = haystack + hlen - nlen;

    while (haystack <= end) {

        char last = haystack[nlen - 1];

        if (last == needle[nlen - 1] &&
            memcmp(haystack, needle, nlen - 1) == 0)
            return (char*)haystack;

        haystack += shift[(unsigned char)last];
    }

    return NULL;
}
```

---

# Architecture of Modern `strstr()`

```
                 strstr()
                     │
     ┌───────────────┴───────────────┐
     │                               │
SIMD scan                     compute needle length
(find first char)                    │
     │                               │
     ├──────── short needles ────────┤
     │                               │
fast compare                 Horspool skip table
                                     │
                               big needles
                                     │
                               Two-Way algorithm
```

---

# Why These 3 Techniques Work

### 1️⃣ SIMD scanning

Real libc does something like:

```
load 32 bytes
compare all bytes with target char
create bitmask
find first match
```

Example AVX idea:

```
vmovdqu ymm0, [ptr]
vpcmpeqb ymm1, ymm0, needle_char
vpmovmskb eax, ymm1
tzcnt eax, eax
```

Search **32 bytes at once**.

---

### 2️⃣ Horspool skipping

Instead of checking every position:

```
aaaaaaaaaaaaaaaaaaaaaaaaab
```

Needle:

```
aaab
```

Algorithm jumps ahead based on **bad character shift table**.

Typical skip:

```
1 → 4 → 7 → 10 → ...
```

---

### 3️⃣ Two-Way algorithm

Guarantees **linear time**.

Worst-case example:

```
haystack = aaaaaaaaaaaaaaaaaaaaaaaab
needle   = aaaaaaaaaaaaaaaaaaaab
```

Naive search becomes:

```
O(n*m)
```

Two-Way guarantees:

```
O(n)
```

---

# Why studying libc string functions is valuable

These functions combine:

* **algorithm theory**
* **CPU architecture**
* **branch prediction**
* **cache behavior**
* **SIMD vectorization**

That's why they are **among the most optimized code in systems programming**.

---

✅ If you'd like, I can also show something extremely interesting:

**The 20-line trick glibc uses to detect zero bytes in a 64-bit word (bit-hack used in `strlen`, `memchr`, `strchr`).**

It's one of the **most famous bit tricks in systems programming**.






