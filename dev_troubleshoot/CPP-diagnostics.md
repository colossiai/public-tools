# Introduce C++ linux diagnostic tools to troubleshoot CPU high load/Memory leak


Here’s a concise but complete overview of **C++ Linux diagnostic tools** that you can use to troubleshoot **CPU high load** and **memory leaks**, categorized by purpose and depth level.

---

## 🧠 1. CPU High Load Diagnostics

### **A. Quick System-Level Tools**

| Tool               | Description                                                            | Typical Command                             |       |
| ------------------ | ---------------------------------------------------------------------- | ------------------------------------------- | ----- |
| **top** / **htop** | Realtime CPU and memory usage; shows threads and per-core utilization. | `top` / `htop`                              |       |
| **pidstat**        | Per-process CPU usage over time; helps find spikes.                    | `pidstat -p <pid> 1`                        |       |
| **mpstat**         | Per-core CPU utilization breakdown.                                    | `mpstat -P ALL 1`                           |       |
| **ps**             | Snapshot of process status; useful for one-time check.                 | `ps -eo pid,ppid,cmd,%mem,%cpu --sort=-%cpu | head` |

---

### **B. Deeper Thread-Level Analysis**

| Tool                                               | Description                                                              | Typical Command                                            |                       |                          |
| -------------------------------------------------- | ------------------------------------------------------------------------ | ---------------------------------------------------------- | --------------------- | ------------------------ |
| **perf top / record / report**                     | Kernel + user-space profiler; shows which functions consume CPU time.    | `perf top -p <pid>` or `perf record -p <pid>; perf report` |                       |                          |
| **gdb** (attach mode)                              | Attach to process and inspect which function each thread is running.     | `sudo gdb -p <pid>` then `thread apply all bt`             |                       |                          |
| **strace**                                         | Trace system calls; useful to detect blocking or busy loops in syscalls. | `strace -p <pid>`                                          |                       |                          |
| **ltrace**                                         | Trace library calls (malloc, free, I/O calls).                           | `ltrace -p <pid>`                                          |                       |                          |
| **flamegraph** (via `perf` + `FlameGraph` scripts) | Visualize CPU hotspots.                                                  | `perf record -F 99 -p <pid> -g` → `perf script             | stackcollapse-perf.pl | flamegraph.pl > out.svg` |

---

## 💾 2. Memory Leak and Usage Diagnostics

### **A. Basic Tools**

| Tool                   | Description                                          | Typical Command          |
| ---------------------- | ---------------------------------------------------- | ------------------------ |
| **free / vmstat**      | Quick view of overall memory usage.                  | `vmstat 1`               |
| **smem**               | Shows proportional set size (PSS) memory by process. | `smem -r`                |
| **pmap**               | Shows memory map of a process.                       | `pmap <pid>`             |
| **/proc/<pid>/status** | Detailed info on process memory usage (RSS, VSZ).    | `cat /proc/<pid>/status` |

---

### **B. Leak Detection Tools**

| Tool                           | Description                                                          | Typical Command                                                       |
| ------------------------------ | -------------------------------------------------------------------- | --------------------------------------------------------------------- |
| **valgrind --leak-check=full** | Classic memory leak detector for C/C++.                              | `valgrind --leak-check=full ./your_program`                           |
| **AddressSanitizer (ASan)**    | Compiler-based runtime memory error detector (faster than Valgrind). | Compile with `-fsanitize=address -g`, run as normal.                  |
| **heaptrack**                  | Profiles heap allocations and memory growth over time.               | `heaptrack ./your_program` → `heaptrack_gui heaptrack.your_program.*` |
| **massif (Valgrind tool)**     | Measures heap usage snapshots over time.                             | `valgrind --tool=massif ./your_program` → `ms_print massif.out.*`     |
| **gperftools (tcmalloc)**      | Lightweight allocator with heap profiler.                            | `LD_PRELOAD=/usr/lib/libtcmalloc.so HEAPPROFILE=heap ./your_program`  |

---

### **C. Runtime Observation Tools**

| Tool                                | Description                                                     | Typical Command                                                         |
| ----------------------------------- | --------------------------------------------------------------- | ----------------------------------------------------------------------- |
| **glibc `MALLOC_TRACE` / `mtrace`** | Logs malloc/free for analysis.                                  | `export MALLOC_TRACE=trace.log; mtrace ./your_program trace.log`        |
| **bcc / eBPF tools**                | Kernel-level observability (e.g. trace malloc/free, CPU sched). | `sudo /usr/share/bcc/tools/` (e.g., `memleak`, `offcputime`, `profile`) |
| **systemtap**                       | Dynamic tracing for kernel + user space.                        | `stap -v -e 'probe process("prog").function("malloc") {exit()}'`        |

---

## 🧩 3. Combined CPU + Memory Profilers (C++ Focused)

| Tool                                 | Description                                                                 |
| ------------------------------------ | --------------------------------------------------------------------------- |
| **Google Perf Tools (gperftools)**   | Heap + CPU profiler; low overhead, simple to integrate.                     |
| **perf + flamegraph**                | Unified CPU analysis, can combine with memory events.                       |
| **Intel VTune Profiler**             | Commercial-grade detailed performance and memory profiler (supports Linux). |
| **Visual Studio Code + C/C++ Tools** | With `perf` or `gdb` integration for visual profiling.                      |

---

## ⚙️ Example Diagnostic Workflow

### Case 1: **CPU 100%**

1. `top` → find PID using 100%.
2. `pidstat -p <pid> 1` → verify CPU pattern.
3. `perf top -p <pid>` → see which functions consume time.
4. If in user code → attach `gdb -p <pid>` and `thread apply all bt`.
5. Optionally → generate `perf record -p <pid> -g` + flamegraph.

### Case 2: **Memory keeps growing**

1. `pmap <pid>` → confirm increasing RSS.
2. `valgrind --leak-check=full ./prog` or re-run with ASan.
3. For long-running server → use `heaptrack` or `gperftools` heap profiler.
4. For live production → `sudo /usr/share/bcc/tools/memleak -p <pid>` (eBPF).

---

Would you like me to give you a **step-by-step example** of diagnosing a **real C++ program (e.g., a server with a memory leak or CPU spin)** using these tools?
That could show actual commands + typical output interpretation.

# Example

Perfect 👍 — let’s go through **two real-world style diagnostic walkthroughs** using C++ programs on **Linux**, one for **CPU high load**, and one for **memory leak**.

I’ll show **the workflow, tools, sample commands, and how to interpret results**.

---

# 🧩 Scenario 1: C++ Process Consuming 100% CPU

## 🧠 Situation

You have a background service `my_server` written in C++.
Users report high CPU usage — even when no requests are being processed.

---

## 🔍 Step-by-Step Diagnosis

### **Step 1: Identify culprit**

```bash
top
```

You see:

```
PID   USER  PR  NI  VIRT  RES  SHR S %CPU %MEM TIME+  COMMAND
1234  root  20   0  240M  20M  4M  R 99.9  0.5  10:00 my_server
```

→ PID `1234` is spinning CPU.

---

### **Step 2: Check threads**

```bash
top -H -p 1234
```

Output:

```
PID   USER  %CPU  COMMAND
1234  root  99.9  my_server
1235  root   0.0  my_server
```

→ The main thread (`1234`) is burning CPU.

---

### **Step 3: See what it’s doing**

Attach debugger:

```bash
sudo gdb -p 1234

#  instructs GDB to take a snapshot of the call stack for every thread 
(gdb) thread apply all bt 
```

Sample output:

```
Thread 1 (LWP 1234):
#0  0x00007f1b4e2b30fa in std::this_thread::sleep_for (...)
#1  0x0000000000408a3b in busy_loop() at worker.cpp:42
#2  0x00000000004079d2 in main() at main.cpp:20
```

→ You see it’s stuck in a **busy loop** inside `busy_loop()` instead of waiting on condition variable — logic bug.

```bash
Thread 2 (Thread 0x75d3289ff6c0 (LWP 2711) "cpu_spin"):
#0  0x00005a4e16b254a8 in busy_worker() ()                  <--------------------------
#1  0x000075d328eecdb4 in ?? () from /lib/x86_64-linux-gnu/libstdc++.so.6
#2  0x000075d328a9caa4 in start_thread (arg=<optimized out>) at ./nptl/pthread_create.c:447
#3  0x000075d328b29c6c in clone3 () at ../sysdeps/unix/sysv/linux/x86_64/clone3.S:78

Thread 1 (Thread 0x75d32907e740 (LWP 2710) "cpu_spin"):
#0  0x000075d328aecadf in __GI___clock_nanosleep (clock_id=clock_id@entry=0, flags=flags@entry=0, req=0x7fffcb6905f0, rem=0x7fffcb6905f0) at ../sysdeps/unix/sysv/linux/clock_nanosleep.c:78
#1  0x000075d328af9a27 in __GI___nanosleep (req=<optimized out>, rem=<optimized out>) at ../sysdeps/unix/sysv/linux/nanosleep.c:25
#2  0x00005a4e16b2532b in main ()
```

---

### **Step 4: Optional – Profile with perf**

```bash
sudo perf record -p 4706 -g -- sleep 10
sudo perf report
```

### 🛠️ Command Breakdown

The table below explains each part of the command:

| Command Component | Explanation |
| :--- | :--- |
| `sudo` | Runs the command with root privileges, necessary for profiling system-wide performance and kernel functions. |
| `perf record` | The main command to sample and record performance data into a file (default: `perf.data`). |
| `-p 4706` | Attaches the profiler to the existing process with the Process ID (PID) **4706**. |
| `-g` | Short for `--call-graph`. This enables call stack recording, allowing you to see the full chain of function calls leading to a sample. |
| `--` | Separates `perf` options from the command to be executed. This is good practice but optional in this case. |
| `sleep 10` | A simple command that runs for 10 seconds, determining the data collection duration. |

### Generate the Report: 
Following command to open an interactive analysis interface:

```bash
sudo perf report
```


Look for top functions:

![alt text](perf-report-cpu_spin.png)


→ Confirms same function consumes almost all CPU.

You can generate a **FlameGraph** for better visualization:

```bash
sudo perf script | stackcollapse-perf.pl | flamegraph.pl > cpu.svg
```

Open `cpu.svg` in browser → tall flame = hotspot.

✅ **Root cause:** Infinite loop / spin-wait in `busy_loop()`.

---

# 🧩 Scenario 2: Memory Keeps Growing (Leak)

## 🧠 Situation

`my_server`’s RSS grows slowly over hours until OOM kills it.

---

## 🔍 Step-by-Step Diagnosis

### **Step 1: Watch growth**

```bash
pmap 1234 | grep total
```

Repeat after few minutes → numbers increasing → leak confirmed.

---

### **Step 2: Quick Heap Snapshot**

Use `smem` or `ps`:

```bash
ps -p 1234 -o pid,vsz,rss,cmd
```

→ RSS keeps increasing.

---

### **Step 3: Profile allocations with Valgrind**

If reproducible in test:

```bash
valgrind --leak-check=full --show-leak-kinds=all ./my_server
```

Example output:

```
==2345== 100 bytes in 5 blocks are definitely lost in loss record 12 of 50
==2345==    at 0x4C2FB55: operator new(unsigned long) (vg_replace_malloc.c:334)
==2345==    by 0x4012FA: MyCache::addItem(std::string const&, std::string const&) (cache.cpp:27)
==2345==    by 0x401AFB: handle_request() (server.cpp:88)
```

→ Leaked allocations inside `MyCache::addItem()`.

---

### **Step 4: Long-running leak (production)**

If leak happens slowly, use **heaptrack**:

```bash
heaptrack ./my_server
# After some workload
heaptrack_gui heaptrack.my_server.*  # Open in GUI
```

In GUI:

* See **allocation hot spots**
* Plot **live heap size vs time**
* Filter by function name to locate leak sources

---

### **Step 5: Runtime lightweight profiling (production-safe)**

Install `gperftools`:

```bash
sudo apt install google-perftools
LD_PRELOAD=/usr/lib/libtcmalloc.so HEAPPROFILE=heap ./my_server
```

After running a while, files like `heap.0001.heap` appear.
Then:

```bash
pprof --text ./my_server heap.0001.heap
pprof --gv ./my_server heap.0001.heap  # Visualize
```

You’ll see which classes/functions allocated most memory.

✅ **Root cause:** Cache grows unbounded — no eviction logic.

---

# 🧠 Summary Table

| Symptom     | Best Tools                            | Workflow                                           |
| ----------- | ------------------------------------- | -------------------------------------------------- |
| High CPU    | `top`, `perf`, `gdb`                  | Identify PID → Thread backtrace → Profile hotspots |
| Memory Leak | `valgrind`, `heaptrack`, `gperftools` | Confirm growth → Leak trace or heap profile        |

---

Would you like me to give you a **self-contained C++ demo program** that intentionally triggers **CPU spin** and **memory leak**, so you can practice using these tools directly?

# C++ demo program with CPU spin/memory leak

Great 👌 — here are **two minimal C++ demo programs** you can compile and run to **practice diagnosing CPU spin** and **memory leak** problems using Linux tools like `top`, `gdb`, `perf`, and `valgrind`.

---

# 🧩 1. High CPU Demo — *Busy Loop Bug*

### 🧱 `cpu_spin.cpp`

```cpp
#include <iostream>
#include <thread>
#include <chrono>
#include <atomic>

std::atomic<bool> running{true};

// Simulates a bug: spinning loop instead of proper sleep
void busy_worker() {
    while (running.load()) {
        // Wrong: missing std::this_thread::sleep_for or condition variable wait
        int x = 0;
        for (int i = 0; i < 1000; ++i)
            x += i;
        // no sleep here -> 100% CPU
    }
}

int main() {
    std::cout << "Starting busy worker..." << std::endl;
    std::thread t(busy_worker);

    std::this_thread::sleep_for(std::chrono::seconds(20)); // let it spin
    running = false;
    t.join();
    std::cout << "Stopped." << std::endl;
}
```

### ⚙️ Compile & Run

```bash
g++ -O2 -std=c++17 cpu_spin.cpp -o cpu_spin -pthread
./cpu_spin
```

### 🧪 Try diagnosing:

1. Run `top` — notice 100% CPU.
2. Run `top -H -p <pid>` — see one thread fully loaded.
3. Attach:

   ```bash
   sudo gdb -p <pid>
   (gdb) thread apply all bt
   ```

   → You’ll see it looping inside `busy_worker()`.
4. (Optional) Profile:

   ```bash
   sudo perf record -p <pid> -g -- sleep 5
   sudo perf report
   ```

   → The function `busy_worker()` will dominate CPU samples.

✅ *Fix:* Add `std::this_thread::sleep_for(10ms)` or use condition variables.

---

# 🧩 2. Memory Leak Demo — *Forgot to Free Allocations*

### 🧱 `memory_leak.cpp`

```cpp
#include <iostream>
#include <vector>
#include <thread>
#include <chrono>

struct Data {
    char payload[1024]; // 1 KB
};

int main() {
    std::cout << "Simulating memory leak..." << std::endl;
    std::vector<Data*> leaked;

    for (int i = 0; i < 100000; ++i) {
        leaked.push_back(new Data()); // Never freed
        if (i % 1000 == 0)
            std::this_thread::sleep_for(std::chrono::milliseconds(10));
    }

    std::cout << "Allocated " << leaked.size() << " objects. Sleeping..." << std::endl;
    std::this_thread::sleep_for(std::chrono::seconds(30)); // keep alive
}
```

### ⚙️ Compile & Run

```bash
g++ -O2 -std=c++17 memory_leak.cpp -o memory_leak -pthread
./memory_leak
```

### 🧪 Try diagnosing:

#### 🔹 Observe leak

```bash
ps -p <pid> -o pid,rss,vsz,cmd
```

→ RSS increases over time.

#### 🔹 With `valgrind`

```bash
valgrind --leak-check=full ./memory_leak
```

You’ll see:

```
==12345== 102400000 bytes in 100000 blocks are definitely lost
==12345==    at 0x4C2FB55: operator new(unsigned long)
==12345==    by 0x4011AA: main (memory_leak.cpp:13)
```

#### 🔹 With `heaptrack`

```bash
heaptrack ./memory_leak
heaptrack_gui heaptrack.memory_leak.*   # visualize leak source
```

✅ *Fix:* Replace `new Data()` with `std::make_unique<Data>()` or delete objects when done.

---

# 🧠 Summary

| Demo              | Symptom      | Diagnostic Tools        | Key Finding                 |
| ----------------- | ------------ | ----------------------- | --------------------------- |
| `cpu_spin.cpp`    | 100% CPU     | `top`, `gdb`, `perf`    | Infinite loop without sleep |
| `memory_leak.cpp` | Memory grows | `valgrind`, `heaptrack` | Missing delete/free         |

---

Would you like me to show you a **shell script** that automatically compiles both, runs them, and prints diagnostic hints (so you can test interactively on Linux)?
