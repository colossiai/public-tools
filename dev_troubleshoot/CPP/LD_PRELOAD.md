# Show me how to use LD_PRELOAD to troubleshoot C++ memory leak


Excellent — this is a powerful Linux trick. Let’s go step-by-step on **how to use `LD_PRELOAD` to detect and trace memory leaks in a running C++ program** — *without modifying source code*.

---

## 🧩 1. Concept

`LD_PRELOAD` lets you **override libc functions** (like `malloc`, `free`, `new`, etc.) by loading your own shared library **before** the program starts.

This allows you to **hook** all allocations/frees and record them for leak analysis.

---

## 🧰 2. Common Tools That Use LD_PRELOAD

| Tool                              | Description                               | Use                     |
| --------------------------------- | ----------------------------------------- | ----------------------- |
| **libSegFault.so**                | Shows stack traces on segmentation faults | Built into glibc        |
| **libasan.so** (AddressSanitizer) | Detects leaks, use-after-free, OOB        | Compile-time or preload |
| **libmemusage.so**                | Tracks heap usage summary                 | Built-in glibc utility  |
| **mtrace**                        | Simple malloc/free trace via LD_PRELOAD   | Lightweight debugging   |
| **jemalloc / tcmalloc / libleak** | Drop-in allocators with leak tracking     | Runtime preload         |

---

## 🧪 3. Easiest Built-in Option: `mtrace`

### Example program `leak.cpp`

```cpp
#include <cstdlib>

int main() {
    char* leak1 = (char*)malloc(100);    // leaked
    char* leak2 = new char[200];         // leaked
    char* ok = (char*)malloc(50);
    free(ok);
    return 0;
}
```

### Compile

```bash
g++ -g -o leak leak.cpp
```

### Run with `mtrace`

`mtrace` is part of glibc and works via LD_PRELOAD under the hood.

```bash
export MALLOC_TRACE=trace.log
LD_PRELOAD=/usr/lib/x86_64-linux-gnu/libmtrace.so ./leak
mtrace ./leak $MALLOC_TRACE
```

Output example:

```
Memory not freed:
-----------------
   Address     Size     Caller
0x0000000000602010 0x64  at 0x7f30e09b7e9a
0x0000000000602080 0xc8  at 0x7f30e09b7e9a
```

This shows addresses and sizes of leaks.

---

## 🔬 4. Using a Custom `LD_PRELOAD` Leak Tracker

If you want more control, you can make your own **interposer library**.

### `leak_hook.cpp`

```cpp
#define _GNU_SOURCE
#include <dlfcn.h>
#include <stdio.h>
#include <stdlib.h>
#include <execinfo.h>
#include <pthread.h>

static void* (*real_malloc)(size_t) = nullptr;
static void (*real_free)(void*) = nullptr;
static pthread_mutex_t lock = PTHREAD_MUTEX_INITIALIZER;

extern "C" void* malloc(size_t size) {
    if (!real_malloc) real_malloc = (void*(*)(size_t)) dlsym(RTLD_NEXT, "malloc");
    void* ptr = real_malloc(size);
    pthread_mutex_lock(&lock);
    fprintf(stderr, "[LEAKTRACE] malloc(%zu) = %p\n", size, ptr);
    pthread_mutex_unlock(&lock);
    return ptr;
}

extern "C" void free(void* ptr) {
    if (!real_free) real_free = (void(*)(void*)) dlsym(RTLD_NEXT, "free");
    pthread_mutex_lock(&lock);
    fprintf(stderr, "[LEAKTRACE] free(%p)\n", ptr);
    pthread_mutex_unlock(&lock);
    real_free(ptr);
}
```

### Build shared library

```bash
g++ -shared -fPIC -ldl -pthread -o libleaktrace.so leak_hook.cpp
```

### Run target program

```bash
LD_PRELOAD=$PWD/libleaktrace.so ./leak
```

You’ll see:

```
[LEAKTRACE] malloc(100) = 0x55c16c2d6260
[LEAKTRACE] malloc(200) = 0x55c16c2d62f0
[LEAKTRACE] malloc(50)  = 0x55c16c2d63d0
[LEAKTRACE] free(0x55c16c2d63d0)
```

You can later analyze which pointers were never freed (the leaked ones).

---

## ⚙️ 5. Advanced: Combine with Backtrace

To see **where** each allocation happened:

Add to your malloc hook:

```cpp
void* buffer[20];
int nptrs = backtrace(buffer, 20);
backtrace_symbols_fd(buffer, nptrs, fileno(stderr));
```

That prints stack traces of each allocation.

---

## 🧠 6. Pros and Cons

✅ **Pros**

* No code modification required.
* Works with binaries you can’t recompile.
* Customizable (record backtraces, filter allocations, etc.)

❌ **Cons**

* Some allocators override malloc internally (like tcmalloc).
* Can slow down execution.
* Limited visibility into C++ `new[]` unless you hook it too.

---

## 🪄 7. Practical Tips

* For **production-safe leak reports**, consider `tcmalloc` or `jemalloc` with profiling enabled:

  ```bash
  LD_PRELOAD=/usr/lib/libtcmalloc.so HEAPPROFILE=heap ./app
  ```

  Then analyze with `pprof`.

* Use `valgrind --leak-check=full ./app` if you can afford the slowdown (no preload needed).

---
