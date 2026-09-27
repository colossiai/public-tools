# **Benchmarking NUMA Binding Performance**

To measure the effectiveness of NUMA binding, we need to compare **latency, memory bandwidth, and CPU affinity** between NUMA-aware and NUMA-agnostic executions. Below are **benchmarking tools and methods** for evaluating NUMA optimizations.

## **1. Key Metrics for NUMA Performance**

- **Memory Latency:** How fast a thread accesses local vs. remote memory.

- **Memory Bandwidth:** Data transfer speed within a NUMA node vs. cross-node.

- **Cache Efficiency:** Avoiding cache misses and improving locality.

- **Thread Affinity:** Ensuring CPU-bound tasks stay within their NUMA node.

## **2. Benchmarking Tools**

Here are some popular tools for benchmarking NUMA performance:

### **(A) numactl + stream (Memory Bandwidth Benchmark)**

The **STREAM** benchmark tests memory bandwidth between NUMA nodes.

#### **Steps:**

1️⃣ Install stream:

sudo apt install stream

2️⃣ Run STREAM without NUMA binding (default execution):

./stream

3️⃣ Run STREAM on a single NUMA node (e.g., Node 0):

numactl --cpunodebind=0 --membind=0 ./stream

4️⃣ Compare performance with cross-NUMA execution:

numactl --cpunodebind=0 --membind=1 ./stream

🔍 **Expected Results:**

- Local NUMA execution (--membind=0) should have **higher bandwidth** and **lower latency** compared to cross-NUMA execution (--membind=1).

### **(B) numactl + mbw (Memory Bandwidth Benchmark)**

The mbw (Memory Bandwidth) tool measures local vs. remote memory bandwidth.

#### **Steps:**

1️⃣ Install mbw:

sudo apt install mbw

2️⃣ Run without NUMA binding:

mbw 1000

3️⃣ Run with NUMA binding:

numactl --cpunodebind=0 --membind=0 mbw 1000

numactl --cpunodebind=0 --membind=1 mbw 1000

🔍 **Expected Results:**

- Memory bandwidth should be **higher** when using local memory (NUMA-aware).

### **(C) numactl + latency-bench (Memory Latency Benchmark)**

The latency-bench tool measures memory access latency between NUMA nodes.

#### **Steps:**

1️⃣ Install numactl (if not installed):

sudo apt install numactl

2️⃣ Run latency test:

numactl --hardware

numactl --membind=0 --cpunodebind=0 ./latency-bench

numactl --membind=1 --cpunodebind=0 ./latency-bench

🔍 **Expected Results:**

- Latency should be **lower** when accessing local memory (membind=0).

## **3. Benchmarking NUMA in a Custom C or Golang Program**

If you want to **benchmark NUMA performance in your HFT application**, you can write a custom memory-access benchmark.

### **(A) C-Based NUMA Benchmark**

Example: Measure local vs. remote memory access latency.

\#define \_GNU_SOURCE

\#include \<stdio.h\>

\#include \<stdlib.h\>

\#include \<numa.h\>

\#include \<time.h\>

\#include \<unistd.h\>

\#define ARRAY_SIZE 100000000 // 100 million elements

void benchmark(int node) {

struct timespec start, end;

double elapsed;

int \*arr = (int\*) numa_alloc_onnode(ARRAY_SIZE \* sizeof(int), node);

// Initialize array

for (int i = 0; i \< ARRAY_SIZE; i++) {

arr\[i\] = i;

}

clock_gettime(CLOCK_MONOTONIC, &start);

// Access array

for (int i = 0; i \< ARRAY_SIZE; i++) {

arr\[i\] \*= 2;

}

clock_gettime(CLOCK_MONOTONIC, &end);

elapsed = (end.tv_sec - start.tv_sec) + (end.tv_nsec - start.tv_nsec) / 1e9;

printf("NUMA Node %d, Time: %f sec\n", node, elapsed);

numa_free(arr, ARRAY_SIZE \* sizeof(int));

}

int main() {

if (numa_available() == -1) {

printf("NUMA not supported!\n");

return 1;

}

printf("Testing NUMA node 0...\n");

benchmark(0);

printf("Testing NUMA node 1...\n");

benchmark(1);

return 0;

}

#### **Compile and Run:**

gcc -o numa_test numa_test.c -lnuma

taskset -c 0 ./numa_test

🔍 **Expected Results:**

- Execution on **local NUMA node** should be **faster** than cross-NUMA execution.

### **(B) Golang NUMA Benchmark**

Go does not have native NUMA support, but you can bind execution manually.

#### **Example: Golang NUMA Benchmark**

package main

import (

"fmt"

"runtime"

"time"

)

// Simulate large memory operations

func benchmark(size int) {

data := make(\[\]int, size)

start := time.Now()

for i := range data {

data\[i\] \*= 2

}

elapsed := time.Since(start)

fmt.Printf("Execution Time: %v\n", elapsed)

}

func main() {

// Restrict execution to a single NUMA node (Linux only)

runtime.GOMAXPROCS(16)

fmt.Println("Benchmarking NUMA Optimized Execution:")

benchmark(100000000)

}

#### **Run with NUMA Binding:**

numactl --cpunodebind=0 --membind=0 ./numa_test

numactl --cpunodebind=0 --membind=1 ./numa_test

🔍 **Expected Results:**

- Execution time should be **lower** on the same NUMA node.

## **4. Advanced NUMA Profiling**

For **deep profiling**, use **perf** or **hwloc**.

### **(A) perf - Measure Cache & Memory Access**

sudo perf stat -e cache-misses,cache-references,cycles,instructions ./trading_app

- High **cache misses** → Indicate poor NUMA locality.

- High **remote memory accesses** → Suggests need for better thread binding.

### **(B) hwloc - Visualize NUMA Layout**

sudo apt install hwloc

lstopo

- This shows CPU, NUMA, and memory topology.

## **5. Summary**

✅ **NUMA-aware execution is faster** than NUMA-agnostic execution.  
✅ **Tools like stream, mbw, and latency-bench** measure memory performance.  
✅ **Use numactl and CPU affinity** to pin processes for lower latency.  
✅ **Custom C/Golang programs** allow fine-tuned NUMA benchmarking.

Would you like help with NUMA profiling in your trading engine? 🚀
