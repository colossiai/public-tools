# Introduce Linux perf tool

Absolutely — here’s a clear, structured introduction to the **Linux `perf` tool**, one of the most powerful performance analysis utilities available on Linux systems.

---

## 🧭 What is `perf`?

**`perf`** is a **performance profiling and tracing tool** for Linux, built on top of the kernel’s **Performance Monitoring Unit (PMU)** and **ftrace** infrastructure.

It lets developers and system engineers **measure, analyze, and visualize performance** at both user and kernel levels — everything from CPU cycles and cache misses to function-level profiling and event tracing.

It’s often used for:

* Finding CPU bottlenecks
* Identifying hot functions or loops in code
* Measuring hardware performance counters
* Tracing system calls and kernel events
* Performance regression testing

---

## ⚙️ Installing `perf`

On most Linux distributions, it’s provided by a package that matches your kernel version:

```bash
# Ubuntu/Debian
sudo apt install linux-tools-common linux-tools-$(uname -r)

# Fedora/RHEL
sudo dnf install perf

# Arch Linux
sudo pacman -S perf
```

---

## 🧩 Basic Concepts

`perf` works by reading **performance counters** from the CPU or kernel. These include:

* **Hardware counters:** cycles, instructions, cache hits/misses, branch mispredictions, etc.
* **Software counters:** context switches, page faults, system calls, etc.
* **Tracepoints:** kernel or user-space events, such as `sched:sched_switch` (context switch).

---

## 🧪 Common Commands

Here are the key `perf` subcommands you’ll use most often:

| Command         | Description                                                |
| --------------- | ---------------------------------------------------------- |
| `perf stat`     | Collects overall performance statistics (summary).         |
| `perf record`   | Records performance data for later analysis.               |
| `perf report`   | Displays a breakdown of where time is spent in code.       |
| `perf top`      | Real-time “top”-like display of hottest functions.         |
| `perf annotate` | Shows annotated source or assembly code with event counts. |
| `perf trace`    | Traces system calls and kernel events (like `strace`).     |

---

## 🧠 Example Workflows

### 1. Get a quick performance summary:

```bash
perf stat ./my_program
```

Outputs counts for cycles, instructions, cache references, etc.

---

### 2. Profile and analyze hot functions:

```bash
perf record ./my_program
perf report
```

* `perf record` collects samples while the program runs.
* `perf report` shows a text-based interactive UI listing “hot spots” by function or symbol.

---

### 3. Live profiling like `top`:

```bash
sudo perf top
```

Shows which functions consume the most CPU time in real-time.

---

### 4. Trace system calls:

```bash
sudo perf trace
```

Similar to `strace`, but with additional kernel-level performance data.

---

## 🧩 Example Output: `perf stat`

```
 Performance counter stats for './my_program':

     1,234,567,890      cycles
       123,456,789      instructions              # 0.10  insn per cycle
         9,876,543      cache-misses
         1.23 seconds time elapsed
```

Interpretation: your program executed 1.2 billion CPU cycles, with a low instruction-per-cycle (IPC) ratio, suggesting inefficiency.

---

## 📈 Visualizing with Flame Graphs (Advanced)

You can export `perf` data and visualize it as **flame graphs**:

```bash
perf record -F 99 -a -g -- sleep 10
perf script | ./stackcollapse-perf.pl | ./flamegraph.pl > perf.svg
```

(Requires Brendan Gregg’s [FlameGraph](https://github.com/brendangregg/FlameGraph) tools.)

---

## 🧰 In Summary

| Feature                | Purpose                                 |
| ---------------------- | --------------------------------------- |
| **perf stat**          | Quick overview of performance metrics   |
| **perf record/report** | Detailed profiling by function          |
| **perf top**           | Real-time CPU usage by symbol           |
| **perf trace**         | System call and event tracing           |
| **perf annotate**      | View code-level performance annotations |

---

Would you like me to show you a **step-by-step tutorial** on using `perf record` and `perf report` to profile a real C/C++ program (with sample code and output)?


# Please provide example


Perfect 👍 Let’s go step-by-step through a **practical tutorial** on how to use `perf record` and `perf report` to **profile a real C program**.

We’ll:

1. Write a small C program with an intentional performance issue
2. Compile it with debug symbols
3. Run `perf record` to collect profiling data
4. Use `perf report` to analyze hot spots

---

## 🧩 Step 1. Create a Sample Program

Let’s make a simple program that computes a Fibonacci number recursively — slow on purpose.

**File: `fib.c`**

```c
#include <stdio.h>
#include <stdlib.h>

long fib(long n) {
    if (n <= 1)
        return n;
    return fib(n - 1) + fib(n - 2);
}

int main(int argc, char **argv) {
    long n = (argc > 1) ? atol(argv[1]) : 40;
    printf("fib(%ld) = %ld\n", n, fib(n));
    return 0;
}
```

This program will take quite some time for larger `n` (like 40), giving us something meaningful to profile.

---

## ⚙️ Step 2. Compile with Debug Info

We need debug symbols (`-g`) so that `perf` can map samples to function names and source lines.

```bash
gcc -O2 -g fib.c -o fib
```

> ✅ Note: Using `-O2` keeps the code optimized but still traceable thanks to `-g`.

---

## 🧪 Step 3. Collect Performance Data

Now, record performance events while the program runs:

```bash
perf record ./fib 40
```

`perf` will run the program and create a file named **`perf.data`**, which contains all collected profiling samples.

You’ll see output like:

```
fib(40) = 102334155
[ perf record: Woken up 1 times to write data ]
[ perf record: Captured and wrote 0.123 MB perf.data (1158 samples) ]
```

---

## 🔍 Step 4. Analyze with `perf report`

Now open the interactive report:

```bash
perf report
```

This will show something like:

```
# Overhead  Command  Shared Object     Symbol
# ........  .......  ................  ........................
    99.30%  fib      fib               [.] fib
     0.40%  fib      libc.so.6         [.] __libc_start_main
     0.30%  fib      [kernel.kallsyms] [k] entry_SYSCALL_64_after_hwframe
```

Interpretation:

* The program spends ~99% of CPU time in `fib()` — exactly where we expected the bottleneck.
* Other entries (like libc or kernel symbols) are just runtime overhead.

---

## 🧬 Step 5. (Optional) See Annotated Source

To see which **lines of code** consume the most CPU:

```bash
perf annotate fib
```

You’ll get output showing annotated assembly and C source, for example:

```
Percent |  Source line
--------+--------------------------------------
 99.0%  |    return fib(n - 1) + fib(n - 2);
```

This confirms that our recursive call dominates execution time.

---

## 🧠 Step 6. Optimize and Compare

Let’s optimize the Fibonacci function with memoization and measure again.

**File: `fib_fast.c`**

```c
#include <stdio.h>
#include <stdlib.h>

long fib_fast(long n, long *cache) {
    if (cache[n] != -1)
        return cache[n];
    if (n <= 1)
        cache[n] = n;
    else
        cache[n] = fib_fast(n - 1, cache) + fib_fast(n - 2, cache);
    return cache[n];
}

int main(int argc, char **argv) {
    long n = (argc > 1) ? atol(argv[1]) : 40;
    long cache[n + 1];
    for (long i = 0; i <= n; i++) cache[i] = -1;
    printf("fib_fast(%ld) = %ld\n", n, fib_fast(n, cache));
    return 0;
}
```

Compile and run with perf again:

```bash
gcc -O2 -g fib_fast.c -o fib_fast
perf stat ./fib_fast 40
```

You’ll see **dramatically fewer cycles** and instructions — a clear win.

---

## 📊 Example Output Comparison

| Metric       | Original | Optimized |
| ------------ | -------- | --------- |
| CPU cycles   | ~3.5e10  | ~1.2e6    |
| Instructions | ~2.7e10  | ~8e5      |
| Time elapsed | 12.3s    | 0.004s    |

---

## 🧰 Summary

| Step | Command                   | Purpose                       |
| ---- | ------------------------- | ----------------------------- |
| 1    | `gcc -O2 -g fib.c -o fib` | Compile with debug info       |
| 2    | `perf record ./fib 40`    | Collect performance samples   |
| 3    | `perf report`             | Analyze where time is spent   |
| 4    | `perf annotate fib`       | Inspect source-level hotspots |
| 5    | `perf stat ./fib 40`      | Compare overall metrics       |

---

Would you like me to show how to **generate a flame graph** from this `perf` data next (so you can visually see the function call hierarchy)?


# Show flame graph

Excellent choice 🔥 — **flame graphs** are one of the most powerful and intuitive ways to visualize profiling data.
They make it *obvious* which functions dominate CPU time, and how time is distributed across call stacks.

Let’s go step-by-step through **creating a flame graph from `perf` data**.

---

## 🧩 Step 1. Record with Call Stacks

We need to capture not just which functions are hot, but also **how we got there** (the call stack).
To do that, use the `-g` flag:

```bash
perf record -F 99 -g ./fib 40
```

**Explanation:**

* `-F 99` → sample at ~99 times per second (good default)
* `-g` → capture call graphs (backtraces)
* `./fib 40` → your program

This generates a `perf.data` file with full stack traces.

---

## 🧰 Step 2. Get Brendan Gregg’s FlameGraph Tools

These are open source and widely used in the performance community.

Clone the repository:

```bash
git clone https://github.com/brendangregg/FlameGraph.git
cd FlameGraph
```

Now you have a set of Perl scripts that convert stack traces into SVG flame graphs:

* `stackcollapse-perf.pl`
* `flamegraph.pl`

---

## 🧮 Step 3. Generate the Flame Graph

From the same directory where your `perf.data` file is located:

```bash
perf script | ./FlameGraph/stackcollapse-perf.pl > out.folded
./FlameGraph/flamegraph.pl out.folded > perf.svg
```

**Explanation:**

1. `perf script` — converts the binary `perf.data` into human-readable stack traces
2. `stackcollapse-perf.pl` — collapses identical stacks into aggregated counts
3. `flamegraph.pl` — creates a visual SVG graph (`perf.svg`)

---

## 🖼️ Step 4. Open and Explore

Now open the resulting SVG file in your browser:

```bash
xdg-open perf.svg
```

You’ll see something like this:

```
        [ fib ]==============================
           fib
            fib
             fib
              fib
----------------------------------------------
CPU time
```

Each **box** represents a function:

* **Width** → how much CPU time it consumed
* **Vertical position** → call depth (what called what)
* **Color** → just aesthetic (all colors mean "CPU time")

Hover your mouse over boxes to see function names and percentages.

---

## 🧠 Step 5. Interpret the Graph

In our recursive `fib()` example:

* You’ll see one **tall stack** where `fib` calls itself repeatedly — showing deep recursion.
* The **base of the widest stack** is your main bottleneck function.
* Any “wide” blocks near the top indicate functions that run frequently but shallowly.

When you switch to the optimized `fib_fast`, the graph will become **much shallower and narrower**, showing far fewer function calls.

---

## 📈 Optional: Flame Graph for System-Wide Profiling

You can also profile *everything* running on the system (not just one program):

```bash
sudo perf record -F 99 -a -g -- sleep 10
sudo perf script | ./FlameGraph/stackcollapse-perf.pl | ./FlameGraph/flamegraph.pl > system.svg
```

This gives you a global view of CPU usage across all processes.

---

## 🧰 Summary

| Step | Command                         | Purpose                    |
| ---- | ------------------------------- | -------------------------- |
| 1    | `perf record -F 99 -g ./fib 40` | Record call stacks         |
| 2    | `perf script`                   | Convert to text traces     |
| 3    | `stackcollapse-perf.pl`         | Aggregate stacks           |
| 4    | `flamegraph.pl`                 | Generate SVG visualization |
| 5    | `xdg-open perf.svg`             | View the flame graph       |

---

Would you like me to explain **how to interpret flame graphs in detail** (e.g., spotting inlined functions, recursive patterns, and multi-threaded bottlenecks)?
