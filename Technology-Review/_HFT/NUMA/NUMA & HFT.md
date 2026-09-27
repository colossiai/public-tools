# **How NUMA Helps in High-Frequency Trading (HFT)**

High-Frequency Trading (HFT) relies on ultra-low latency and high throughput to execute trades in microseconds or even nanoseconds. NUMA (Non-Uniform Memory Access) optimizations help by reducing memory access latency and improving CPU cache locality, leading to faster order execution and lower jitter.

#### **1. How NUMA Improves HFT Performance**

- **Reduces Memory Access Latency:** In NUMA systems, each CPU socket has its own local memory. If a thread accesses remote memory (attached to another CPU socket), it introduces additional latency. NUMA-aware applications pin processes and memory allocations to the same NUMA node, reducing cross-socket memory access.

- **Optimizes CPU Affinity:** Trading applications can pin specific threads (such as order book updates or market data processing) to a NUMA node to ensure minimal CPU contention and cache thrashing.

- **Improves Network Performance:** HFT firms use **kernel bypass** and **Direct Memory Access (DMA)** with network cards (e.g., Mellanox NICs) mapped to specific NUMA nodes to ensure the lowest-latency packet processing.

### **2. NUMA Optimization in HFT: Example**

Let's consider an HFT trading system running on a multi-socket NUMA server with 2 CPU sockets, each with 16 cores.

#### **Scenario:**

- **NUMA-ignorant setup:** If the trading engine runs without NUMA awareness, it may schedule threads across different sockets, leading to **remote memory accesses** and **higher latency**.

- **NUMA-optimized setup:** If the order-matching engine is pinned to NUMA node 0 and the market data feed handler to NUMA node 1, each process accesses its local memory and CPU cache efficiently.

#### **Example: NUMA Optimization Using numactl**

Assuming an HFT trading engine runs on Linux with two NUMA nodes, we can optimize process execution:

1️⃣ **Check NUMA Nodes:**

numactl --hardware

Output:

available: 2 nodes (0-1)

node 0 cpus: 0-15

node 1 cpus: 16-31

2️⃣ **Bind Market Data Processing to NUMA Node 0:**

numactl --cpunodebind=0 --membind=0 ./market_data_feed

3️⃣ **Bind Order Matching Engine to NUMA Node 1:**

numactl --cpunodebind=1 --membind=1 ./order_matching

### **3. NUMA Optimization in HFT Network Stack**

In HFT, **network packet processing** is a critical factor. To reduce latency:

- **Use DPDK (Data Plane Development Kit)** or **Solarflare Onload** to bypass the Linux kernel and directly process packets in user space.

- **Bind the network interface card (NIC) to a specific NUMA node** to avoid cross-socket memory transfers.

Example:

ethtool -S eth0 \| grep numa

If eth0 is on NUMA node 1, pin the trading engine there:

numactl --cpunodebind=1 --membind=1 ./trading_engine

### **4. NUMA in Golang for HFT**

Since you're using Golang, you can optimize NUMA manually. While Go’s runtime scheduler doesn’t provide built-in NUMA awareness, you can:

- **Use GOMAXPROCS to limit execution to a specific NUMA node.  **

- **Manually allocate memory and pin goroutines to cores.  **

Example:

runtime.GOMAXPROCS(16) // Restrict execution to one NUMA node

For better CPU affinity, you may need to use **CGO with sched_setaffinity** or use libraries like numactl via syscall.

### **5. Key Takeaways**

✅ **Reduce remote memory access:** Bind processes to NUMA nodes.  
✅ **Improve cache locality:** Ensure core trading logic runs on the same NUMA node as its memory.  
✅ **Optimize network processing:** Bind NIC interrupts and packet handling to the same NUMA node.  
✅ **Use kernel bypass:** Employ DPDK or other low-latency networking stacks.

Would you like help setting up a NUMA-aware Go-based trading engine? 🚀
