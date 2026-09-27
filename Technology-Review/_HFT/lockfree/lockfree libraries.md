For **High-Frequency Trading (HFT)**, you need a **low-latency, lock-free queue** that minimizes CPU cache contention and supports ultra-fast message passing. The best options are:

### **🔹 Top Lock-Free Queues for HFT**

| **Library** | **Latency** | **Throughput** | **Memory Usage** | **Best For** |
|----|----|----|----|----|
| **MoodyCamel ConcurrentQueue** | ⚡ Extremely low | 🚀 Very high | 🔥 Efficient | **Real-time trading** |
| **Folly MPMCQueue** | ⚡ Low | 🚀 High | 🔥 Efficient | **Multi-threaded market data processing** |
| **Disruptor (Java-based, but has C++ versions)** | ⚡ Ultra-low | 🚀 Ultra-high | 🔥 Efficient | **Order matching, event-driven systems** |

### **1️⃣ MoodyCamel ConcurrentQueue (Best for HFT)**

📌 **GitHub**: [<u>https://github.com/cameron314/concurrentqueue</u>](https://github.com/cameron314/concurrentqueue)  
📌 **Why it’s good for HFT**: ✅ **Lock-free, wait-free (MPMC)** → No blocking, perfect for market data handling  
✅ **No dynamic allocations after init** → Avoids latency spikes  
✅ **Single-writer/single-reader optimizations** for extreme performance  
✅ **Very cache-efficient** → Reduces false sharing

🔹 **Example Code:**

\#include "readerwriterqueue.h"

\#include \<iostream\>

int main() {

moodycamel::ReaderWriterQueue\<int\> queue(1024); // Pre-allocated size

queue.enqueue(42); // Producer

int value;

if (queue.try_dequeue(value)) { // Consumer

std::cout \<\< "Dequeued: " \<\< value \<\< std::endl;

}

return 0;

}

🔥 **Performance**: **Sub-microsecond latency** with millions of messages per second

### **2️⃣ Folly MPMCQueue (Used at Facebook, Very Fast)**

📌 **GitHub**: [<u>https://github.com/facebook/folly</u>](https://github.com/facebook/folly)  
📌 **Why it’s good for HFT**: ✅ **Lock-free multi-producer, multi-consumer (MPMC)**  
✅ **Optimized for low-latency, multi-core CPUs**  
✅ **Atomic operations reduce contention**  
✅ **Used in large-scale systems like Facebook Ads processing**

🔹 **Example Code:**

\#include \<folly/MPMCQueue.h\>

\#include \<iostream\>

int main() {

folly::MPMCQueue\<int\> queue(1024); // Lock-free, multi-producer/multi-consumer queue

queue.write(1); // Producer

int value;

queue.read(value); // Consumer

std::cout \<\< "Dequeued: " \<\< value \<\< std::endl;

return 0;

}

🔥 **Performance**: **Low-latency, high throughput** with strong multi-core scaling

### **3️⃣ Disruptor (Ultra-Low Latency, Event-Driven)**

📌 **Website**: [<u>https://lmax-exchange.github.io/disruptor/</u>](https://lmax-exchange.github.io/disruptor/)  
📌 **Why it’s good for HFT**: ✅ **Designed for trading exchanges** (Used at LMAX Exchange)  
✅ **Memory preallocation → No heap allocation latency**  
✅ **Single-producer, multiple-consumer optimized**  
✅ **Ring buffer architecture eliminates cache contention**

🔹 **Performance Benchmark**:

- **Throughput:** Millions of messages per second

- **Latency:** \<1µs (microsecond)

🔥 **Best for:** Order matching engines, FIX message processing, event-driven systems

### **🚀 Final Recommendation for HFT**

1️⃣ **MoodyCamel ConcurrentQueue** → Best for **low-latency, lock-free message passing**  
2️⃣ **Folly MPMCQueue** → Best for **multi-threaded processing with high throughput**  
3️⃣ **Disruptor** → Best for **event-driven HFT architectures** (order matching, FIX engines)

**🛠️ Want help implementing one of these in a real trading system?** 🚀
