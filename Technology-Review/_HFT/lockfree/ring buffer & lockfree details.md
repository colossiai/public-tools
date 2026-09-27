# **Ring buffer compares Counter version vs One slot empty version.**

# 

When implementing a **ring buffer (circular buffer)**, there are two common approaches for tracking full/empty state:

### **✅ 1. One Slot Left Empty Version**

This approach **always leaves one slot unused** to differentiate between full and empty conditions.

#### **Logic**

- empty: head == tail

- full: (tail + 1) % size == head

#### **Pros**

- Simple logic.

- No need for extra metadata (just head and tail).

- Avoids race conditions more easily in multi-threaded scenarios.

#### **Cons**

- Wastes **1 slot** of capacity.

### **✅ 2. Counter Version**

This approach uses an **explicit counter** or boolean isFull flag to distinguish between full and empty.

#### **Logic**

- empty: head == tail && !isFull

- full: head == tail && isFull

Or use a counter:

- Maintain a count of elements.

- full: count == size

- empty: count == 0

#### **Pros**

- Utilizes **full capacity** of the buffer.

- Better when buffer size is small and every slot matters.

#### **Cons**

- Slightly more complex logic.

- Must be careful with updating count or isFull, especially in multi-threaded contexts (synchronization needed).

- Extra space for counter/flag.

### **🔄 Comparison Summary**

| **Feature**           | **One Slot Empty**      | **Counter Version** |
|-----------------------|-------------------------|---------------------|
| Max Capacity          | size - 1                | size                |
| Simplicity            | ✅ Simpler              | ❌ More complex     |
| Extra Metadata Needed | ❌ None                 | ✅ Yes (count/flag) |
| Risk in Concurrency   | ✅ Lower                | ❌ Higher           |
| Best For              | General use, simplicity | High utilization    |

### **👑 Recommendation**

- **Use One Slot Empty** version if:

  - You want simplicity and safety (especially for concurrent use).

  - The buffer is large enough that losing 1 slot is negligible.

- **Use Counter Version** if:

  - You need **100% utilization**.

  - You're okay with managing a little more complexity.

Would you like to see example code for each?

# **Give an ring buffer implementation in C++**

<span class="mark">– One slot empty version</span>

Here’s a simple, efficient, and thread-unsafe **ring buffer (circular buffer)** implementation in modern C++:

\#include \<iostream\>

\#include \<vector\>

\#include \<stdexcept\>

template\<typename T\>

class RingBuffer {

public:

explicit RingBuffer(size_t capacity)

: buffer(capacity), head(0), tail(0), full(false) {}

void push(const T& item) {

buffer\[head\] = item;

if (full) {

tail = (tail + 1) % buffer.size(); // overwrite oldest

}

head = (head + 1) % buffer.size();

full = head == tail;

}

T pop() {

if (empty()) {

throw std::runtime_error("Buffer is empty");

}

T item = buffer\[tail\];

full = false;

tail = (tail + 1) % buffer.size();

return item;

}

bool empty() const {

return (!full && (head == tail));

}

bool is_full() const {

return full;

}

size_t size() const {

if (full) {

return buffer.size();

}

if (head \>= tail) {

return head - tail;

}

return buffer.size() + head - tail;

}

size_t capacity() const {

return buffer.size();

}

private:

std::vector\<T\> buffer;

size_t head;

size_t tail;

bool full;

};

// Example usage:

int main() {

RingBuffer\<int\> rb(5);

for (int i = 1; i \<= 5; ++i) {

rb.push(i);

}

std::cout \<\< "Full? " \<\< rb.is_full() \<\< "\n";

rb.push(6); // Overwrites oldest (1)

while (!rb.empty()) {

std::cout \<\< rb.pop() \<\< " ";

}

std::cout \<\< "\n";

return 0;

}

### **Features:**

- Fixed-size, circular behavior.

- Overwrites oldest element when full.

- Efficient O(1) push and pop.

### **Notes:**

- This version is **not thread-safe**.

- You can use std::mutex if you want to make it thread-safe.

- If you need **blocking behavior** or **wait/notify**, you’d need to integrate condition variables.

Let me know if you want a multithreaded version!

# **Don't throw exception in pop(), don't overwrite oldest**

Got it! Here's a revised version of the ring buffer with the following changes:

1.  pop() **does not throw an exception** when the buffer is empty.

2.  push() **does not overwrite** the oldest item if the buffer is full — it simply refuses to insert and returns false.

### **✅ Safe & Non-overwriting Ring Buffer in C++**

\#include \<iostream\>

\#include \<vector\>

\#include \<optional\>

template\<typename T\>

class RingBuffer {

public:

explicit RingBuffer(size_t capacity)

: buffer(capacity), head(0), tail(0), full(false) {}

// Returns true if pushed, false if buffer is full

bool push(const T& item) {

if (full) {

return false; // Do not overwrite

}

buffer\[head\] = item;

head = (head + 1) % buffer.size();

full = head == tail;

return true;

}

// Returns std::optional\<T\>, std::nullopt if empty

std::optional\<T\> pop() {

if (empty()) {

return std::nullopt;

}

T item = buffer\[tail\];

tail = (tail + 1) % buffer.size();

full = false;

return item;

}

bool empty() const {

return (!full && head == tail);

}

bool is_full() const {

return full;

}

size_t size() const {

if (full) {

return buffer.size();

}

if (head \>= tail) {

return head - tail;

}

return buffer.size() + head - tail;

}

size_t capacity() const {

return buffer.size();

}

private:

std::vector\<T\> buffer;

size_t head;

size_t tail;

bool full;

};

// Example usage:

int main() {

RingBuffer\<int\> rb(3);

std::cout \<\< std::boolalpha;

std::cout \<\< "Push 1: " \<\< rb.push(1) \<\< "\n";

std::cout \<\< "Push 2: " \<\< rb.push(2) \<\< "\n";

std::cout \<\< "Push 3: " \<\< rb.push(3) \<\< "\n";

std::cout \<\< "Push 4 (should fail): " \<\< rb.push(4) \<\< "\n";

while (!rb.empty()) {

auto val = rb.pop();

std::cout \<\< "Popped: " \<\< \*val \<\< "\n";

}

auto emptyVal = rb.pop();

std::cout \<\< "Pop on empty: " \<\< (emptyVal ? std::to_string(\*emptyVal) : "nothing") \<\< "\n";

return 0;

}

### **✅ Summary of Behavior:**

- push() → returns false if buffer is full.

- pop() → returns std::optional\<T\>, use .has_value() or \*val if not empty.

- No exceptions. Clean and safe.

Want a thread-safe version with std::mutex and std::condition_variable too?

# **Why not keep size counter inside class?**

Great question! ✅ Keeping a **size counter** inside the RingBuffer class is often a better choice, especially for clarity and performance.

### **🔍 Why it's *not* in the original implementation**

In the code I gave you, the size() is calculated **on-the-fly** using head, tail, and full:

size_t size() const {

if (full) return buffer.size();

if (head \>= tail) return head - tail;

return buffer.size() + head - tail;

}

This avoids keeping an extra variable, but it adds complexity and small runtime cost every time you ask for the size.

### **✅ Why you *should* keep a size\_ member variable**

#### **✔ Cleaner**

The logic for size() becomes trivial:

size_t size() const { return size\_; }

#### **✔ More efficient**

You avoid calculating size repeatedly from positions and flags.

#### **✔ Easier to debug and extend**

A size\_ variable is immediately understandable and helps avoid bugs when extending the buffer logic (e.g., adding peek, reserve, etc).

### **🔧 Modified RingBuffer with size\_ Counter**

template\<typename T\>

class RingBuffer {

public:

explicit RingBuffer(size_t capacity)

: buffer(capacity), head(0), tail(0), size\_(0) {}

bool push(const T& item) {

if (is_full()) return false;

buffer\[head\] = item;

head = (head + 1) % buffer.size();

++size\_;

return true;

}

std::optional\<T\> pop() {

if (empty()) return std::nullopt;

T item = buffer\[tail\];

tail = (tail + 1) % buffer.size();

--size\_;

return item;

}

bool empty() const { return size\_ == 0; }

bool is_full() const { return size\_ == buffer.size(); }

size_t size() const { return size\_; }

size_t capacity() const { return buffer.size(); }

private:

std::vector\<T\> buffer;

size_t head;

size_t tail;

size_t size\_; // ✅ Explicit size tracker

};

Let me know if you want the same thing in a **thread-safe** or **lock-free** flavor — or with iterators or STL-style interface!

# **Make above RingBuffer thread-safe.**

Alright! Here's a **thread-safe** version of the RingBuffer using std::mutex to guard access, and std::condition_variable for optional blocking pop() and push() if you want them to wait instead of fail.

I'll show both **non-blocking** and **blocking** versions in one class for flexibility.

### **🔐 Thread-safe RingBuffer (C++17 or later)**

\#include \<iostream\>

\#include \<vector\>

\#include \<optional\>

\#include \<mutex\>

\#include \<condition_variable\>

template\<typename T\>

class ThreadSafeRingBuffer {

public:

explicit ThreadSafeRingBuffer(size_t capacity)

: buffer(capacity), head(0), tail(0), size\_(0) {}

// Non-blocking push: returns false if full

bool try_push(const T& item) {

std::lock_guard\<std::mutex\> lock(mtx);

if (is_full_unlocked()) return false;

buffer\[head\] = item;

head = (head + 1) % buffer.size();

++size\_;

not_empty.notify_one();

return true;

}

// Blocking push: waits until there's space

void push(const T& item) {

std::unique_lock\<std::mutex\> lock(mtx);

not_full.wait(lock, \[this\] { return !is_full_unlocked(); });

buffer\[head\] = item;

head = (head + 1) % buffer.size();

++size\_;

not_empty.notify_one();

}

// Non-blocking pop: returns nullopt if empty

std::optional\<T\> try_pop() {

std::lock_guard\<std::mutex\> lock(mtx);

if (is_empty_unlocked()) return std::nullopt;

T item = buffer\[tail\];

tail = (tail + 1) % buffer.size();

--size\_;

not_full.notify_one();

return item;

}

// Blocking pop: waits until there's data

T pop() {

std::unique_lock\<std::mutex\> lock(mtx);

not_empty.wait(lock, \[this\] { return !is_empty_unlocked(); });

T item = buffer\[tail\];

tail = (tail + 1) % buffer.size();

--size\_;

not_full.notify_one();

return item;

}

bool empty() const {

std::lock_guard\<std::mutex\> lock(mtx);

return size\_ == 0;

}

bool is_full() const {

std::lock_guard\<std::mutex\> lock(mtx);

return size\_ == buffer.size();

}

size_t size() const {

std::lock_guard\<std::mutex\> lock(mtx);

return size\_;

}

size_t capacity() const {

return buffer.size();

}

private:

std::vector\<T\> buffer;

size_t head;

size_t tail;

size_t size\_;

mutable std::mutex mtx;

std::condition_variable not_empty;

std::condition_variable not_full;

bool is_full_unlocked() const { return size\_ == buffer.size(); }

bool is_empty_unlocked() const { return size\_ == 0; }

};

### **🚀 Example Usage**

\#include \<thread\>

int main() {

ThreadSafeRingBuffer\<int\> rb(3);

std::thread producer(\[&\] {

for (int i = 0; i \< 5; ++i) {

rb.push(i); // blocks if full

std::cout \<\< "Produced: " \<\< i \<\< "\n";

}

});

std::thread consumer(\[&\] {

for (int i = 0; i \< 5; ++i) {

int val = rb.pop(); // blocks if empty

std::cout \<\< "Consumed: " \<\< val \<\< "\n";

}

});

producer.join();

consumer.join();

}

### **🔧 Options:**

- Use try_push / try_pop if you want **non-blocking** behavior.

- Use push / pop if you want **blocking** behavior with automatic wait.

Let me know if you want a **lock-free** version next — that's a bit more advanced but doable using atomics and CAS.

# **\>\>\> Provide lockfree version**

Creating a **lock-free ring buffer** is a more advanced task — and super useful when performance and low latency matter, like in real-time systems, trading engines, or high-throughput queues.

Here’s a lock-free **single-producer single-consumer (SPSC)** ring buffer using C++ atomics. This version assumes:

- 🧵 **One producer thread** (writing),

- 🧵 **One consumer thread** (reading),

- No mutexes, no locks — purely atomic.

### **⚡ Lock-Free SPSC Ring Buffer in C++ (C++11+)**

\#include \<atomic\>

\#include \<vector\>

\#include \<optional\>

template\<typename T\>

class LockFreeSPSCQueue {

public:

explicit LockFreeSPSCQueue(size_t capacity)

: buffer(capacity), capacity\_(capacity), head(0), tail(0) {}

bool push(const T& item) {

size_t currentHead = head.load(std::memory_order_relaxed);

size_t nextHead = increment(currentHead);

if (nextHead == tail.load(std::memory_order_acquire)) {

return false; // full

}

buffer\[currentHead\] = item;

head.store(nextHead, std::memory_order_release);

return true;

}

std::optional\<T\> pop() {

size_t currentTail = tail.load(std::memory_order_relaxed);

if (currentTail == head.load(std::memory_order_acquire)) {

return std::nullopt; // empty

}

T item = buffer\[currentTail\];

tail.store(increment(currentTail), std::memory_order_release);

return item;

}

bool empty() const {

return head.load(std::memory_order_acquire) == tail.load(std::memory_order_acquire);

}

bool is_full() const {

return increment(head.load(std::memory_order_acquire)) == tail.load(std::memory_order_acquire);

}

size_t size() const {

size_t h = head.load(std::memory_order_acquire);

size_t t = tail.load(std::memory_order_acquire);

return (h + capacity\_ - t) % capacity\_;

}

size_t capacity() const {

return capacity\_ - 1; // one slot left empty to differentiate full/empty

}

private:

size_t increment(size_t idx) const {

return (idx + 1) % capacity\_;

}

std::vector\<T\> buffer;

const size_t capacity\_;

std::atomic\<size_t\> head; // write index

std::atomic\<size_t\> tail; // read index

};

### **🧪 Example usage**

\#include \<thread\>

\#include \<iostream\>

int main() {

LockFreeSPSCQueue\<int\> queue(8);

std::thread producer(\[&\] {

for (int i = 0; i \< 20; ++i) {

while (!queue.push(i)) {

// spin if full

}

std::cout \<\< "Produced: " \<\< i \<\< "\n";

}

});

std::thread consumer(\[&\] {

int count = 0;

while (count \< 20) {

auto item = queue.pop();

if (item) {

std::cout \<\< "Consumed: " \<\< \*item \<\< "\n";

++count;

}

}

});

producer.join();

consumer.join();

}

### **✅ Key Features**

- **SPSC only**: One thread writes, one thread reads.

- **No locks or mutexes**.

- **Memory_order** used for correctness on multi-core CPUs.

- **One slot is always unused** to distinguish between full and empty.

### **❗Want more?**

- For **MPMC (Multi-producer Multi-consumer)** you’ll need a more advanced data structure like [<u>MoodyCamel's ConcurrentQueue</u>](https://github.com/cameron314/concurrentqueue) or bounded queues using hazard pointers or epoch-based GC.

- Want an MPMC version built from scratch?

Let me know your exact threading needs (SPSC, MPMC, etc.), and I’ll tailor it!

# **\>\>\> The size of the queue is equal to buffer.size() ?**

Great question — and it can be a bit subtle in **ring buffers**.

### **🔍 Is the queue size equal to buffer.size()?**

No — **not exactly**.

In most **ring buffer implementations**, including the lock-free one I gave you, the **actual usable size of the queue is**:

capacity = buffer.size() - 1;

This is because **one slot is always intentionally left unused** to differentiate between the **empty** and **full** states.

### **📌 Why leave one slot empty?**

Imagine this situation:

| **head** | **tail** | **Meaning**                          |
|----------|----------|--------------------------------------|
| x        | x        | Could mean **empty** or **full**! 😬 |

To avoid this ambiguity, we use this trick:

- **Buffer of size N → can hold at most N - 1 elements  **

- Full: (head + 1) % N == tail

- Empty: head == tail

This makes both states unambiguous.

### **✅ Example:**

If you declare:

LockFreeSPSCQueue\<int\> q(8); // buffer size = 8

- It can store **7 elements**, not 8.

- Internally: std::vector\<T\> buffer(8);

- Effective capacity: capacity = buffer.size() - 1 = 7

### **<span class="mark">🧠 TL;DR</span>**

| **<span class="mark">Term</span>** | **<span class="mark">Meaning</span>** |
|----|----|
| **<span class="mark">buffer.size()</span>** | **<span class="mark">The actual size of the internal array (N)</span>** |
| **<span class="mark">queue.capacity()</span>** | **<span class="mark">The usable capacity (N - 1)</span>** |
| **<span class="mark">queue.size()</span>** | **<span class="mark">Current number of elements in the queue</span>** |

Let me know if you’d like a version that supports a **full N capacity** without leaving a slot empty — it requires adding a separate count or flag!

# **Yes add count for the lock free version.**

Perfect — let's upgrade the lock-free SPSC queue to **support full use of the buffer**, without wasting a slot. We'll do that by explicitly tracking the number of elements using a separate atomic count.

### **✅ Lock-Free SPSC Queue With Full Capacity Support (Using Atomic count)**

\#include \<atomic\>

\#include \<vector\>

\#include \<optional\>

template\<typename T\>

class LockFreeSPSCQueue {

public:

explicit LockFreeSPSCQueue(size_t capacity)

: buffer(capacity), capacity\_(capacity),

head(0), tail(0), count(0) {}

bool push(const T& item) {

if (count.load(std::memory_order_acquire) == capacity\_) {

return false; // full

}

size_t currentHead = head.load(std::memory_order_relaxed);

buffer\[currentHead\] = item;

head.store((currentHead + 1) % capacity\_, std::memory_order_release);

count.fetch_add(1, std::memory_order_release);

return true;

}

std::optional\<T\> pop() {

if (count.load(std::memory_order_acquire) == 0) {

return std::nullopt; // empty

}

size_t currentTail = tail.load(std::memory_order_relaxed);

T item = buffer\[currentTail\];

tail.store((currentTail + 1) % capacity\_, std::memory_order_release);

count.fetch_sub(1, std::memory_order_release);

return item;

}

bool empty() const {

return count.load(std::memory_order_acquire) == 0;

}

bool is_full() const {

return count.load(std::memory_order_acquire) == capacity\_;

}

size_t size() const {

return count.load(std::memory_order_acquire);

}

size_t capacity() const {

return capacity\_;

}

private:

std::vector\<T\> buffer;

const size_t capacity\_;

std::atomic\<size_t\> head; // write index

std::atomic\<size_t\> tail; // read index

std::atomic\<size_t\> count; // ✅ number of elements

};

### **🔍 Key Differences From Previous Version**

| **Feature** | **Old Version (1 slot wasted)** | **New Version (count-based)** |
|----|----|----|
| Usable capacity | N - 1 | N |
| Needs count field | ❌ No | ✅ Yes |
| full condition | (head + 1) % N == tail | count == N |
| empty condition | head == tail | count == 0 |

### **🧪 Example Use**

LockFreeSPSCQueue\<int\> queue(4); // full usable 4-slot buffer

queue.push(1);

queue.push(2);

queue.push(3);

queue.push(4); // no slot wasted

std::cout \<\< "Size: " \<\< queue.size() \<\< "\n"; // should print 4

Want to make it **multi-producer/multi-consumer (MPMC)** next? That's a bit more complex but doable with atomic CAS and per-slot tagging.

# **Is there possible that atomic variables head and count have inconsistent state in multi-thread context?**

Excellent question — you're diving into the core of lock-free programming here. The short answer is:

> ✅ **Yes**, it's possible that head and count could be temporarily inconsistent in **multi-threaded** contexts **unless access patterns are carefully controlled.**

But let's break it down.

## **🧠 Key Concepts**

### **🔒 Our Lock-Free Queue is SPSC (Single Producer, Single Consumer)**

So we assume:

- Only **one thread** ever calls push() → updates head, count

- Only **one thread** ever calls pop() → updates tail, count

This is what keeps it safe *without locks*.

## **🔍 What Could Go Wrong With head and count?**

If we had **multiple producers or consumers**, then:

- One thread might update head

- Another thread might read count before it’s updated

- ✅ This could create a **temporary inconsistency** between head and count, breaking size checks or correctness

But in SPSC:

- One thread controls both head and incrementing count

- The other controls both tail and decrementing count

As long as the memory_order constraints are respected (which they are), **this is safe**.

## **🔐 Example: Why This Works in SPSC**

### **push() — done by producer thread:**

size_t currentHead = head.load(std::memory_order_relaxed);

buffer\[currentHead\] = item;

head.store(..., std::memory_order_release);

count.fetch_add(1, std::memory_order_release);

- The producer does both head and count updates.

- The memory_order_release ensures that writes to buffer and head are visible before count changes.

### **pop() — done by consumer thread:**

size_t currentTail = tail.load(std::memory_order_relaxed);

T item = buffer\[currentTail\];

tail.store(..., std::memory_order_release);

count.fetch_sub(1, std::memory_order_release);

- Consumer is the only one touching tail and decreasing count.

## **🚨 In Multi-Producer or Multi-Consumer?**

- Yes, you’d definitely get **race conditions** without proper synchronization.

- You’d need **atomic CAS**, or even per-slot tags with sequence numbers (like in [<u>Vyukov’s MPMC queue</u>](https://www.1024cores.net/home/lock-free-algorithms/queues/bounded-mpmc-queue)).

## **✅ Summary**

||
||
||
||

Want to extend this to **MPMC** (multi-thread safe in all cases)? I can guide you through the design and implementation with per-slot tagging and atomic CAS logic.

# **In LockFreeSPSCQueue push(), the statement size_t currentHead = head.load(std::memory_order_relaxed); is valid because only one thread use push(), so memory_order_relaxed is OK?**

Yes — you're **exactly right**! 💡 Let's break it down:

### **✅ std::memory_order_relaxed in push()**

size_t currentHead = head.load(std::memory_order_relaxed);

This is **valid** in LockFreeSPSCQueue **only because of the SPSC (Single-Producer, Single-Consumer) assumption**.

### **🧠 Why it's safe:**

In the SPSC model:

- Only **one thread (producer)** ever calls push() and accesses head.

- Only **one thread (consumer)** ever calls pop() and accesses tail.

- The producer and consumer never **both modify** the same variable.

So:

- head is only modified by the **producer  **

- tail is only modified by the **consumer  **

- Therefore, using std::memory_order_relaxed to load head is **safe**, because:

  - No one else is concurrently modifying it

  - You’re not synchronizing with another thread’s store to it

This avoids unnecessary cache synchronization and improves performance.

### **🧠 When to use stronger memory orderings**

However, for correctness across threads:

- **std::memory_order_release** ensures previous writes are visible before publishing the value

- **std::memory_order_acquire** ensures that subsequent reads see what was published before

In the push() and pop(), we use:

head.store(..., std::memory_order_release);

count.fetch_add(1, std::memory_order_release);

This ensures that:

- The data write (buffer\[currentHead\] = item) becomes visible **before** the update to count.

### **✅ TL;DR**

| **Operation** | **Memory Order** | **Why It's OK** |
|----|----|----|
| head.load(relaxed) (in push) | relaxed | Only producer reads/writes |
| tail.load(relaxed) (in pop) | relaxed | Only consumer reads/writes |
| head.store(..., release) | release | Publish writes to buffer |
| count.fetch_add(..., release) | release | Publish that buffer is ready |

Let me know if you want a version that validates all memory orderings with comments!

# **OK please extend LockFreeSPSCQueue to MPMC**

Awesome — let’s build a **lock-free MPMC (Multi-Producer Multi-Consumer) ring buffer** in C++. This version is based on the widely respected [<u>Vyukov's bounded MPMC queue</u>](https://www.1024cores.net/home/lock-free-algorithms/queues/bounded-mpmc-queue), which uses:

- A fixed-size ring buffer

- Atomic **per-slot sequence numbers  **

- Atomic head and tail indexes

- Compare-and-swap (CAS) for correctness

## **✅ Overview**

- Fully **lock-free** (no mutexes)

- Allows **multiple threads** to push and pop concurrently

- Bounded: size must be fixed at creation

- Uses std::atomic and per-slot metadata

### **💡 Key Ideas**

Each slot has:

- A value (T)

- A sequence number (std::atomic\<size_t\>) to track its readiness

We use CAS on the head/tail indexes to safely claim slots for pushing/popping.

## **🧱 MPMC Queue Implementation**

\#include \<vector\>

\#include \<atomic\>

\#include \<cstddef\>

\#include \<optional\>

\#include \<memory\>

template\<typename T\>

class LockFreeMPMCQueue {

public:

explicit LockFreeMPMCQueue(size_t capacity)

: capacity\_(capacity), buffer\_(new Cell\[capacity\]), head\_(0), tail\_(0) {

for (size_t i = 0; i \< capacity; ++i) {

buffer\_\[i\].seq.store(i, std::memory_order_relaxed);

}

}

bool push(const T& data) {

Cell\* cell;

size_t pos = head\_.load(std::memory_order_relaxed);

while (true) {

cell = &buffer\_\[pos % capacity\_\];

size_t seq = cell-\>seq.load(std::memory_order_acquire);

intptr_t diff = static_cast\<intptr_t\>(seq) - static_cast\<intptr_t\>(pos);

if (diff == 0) {

if (head\_.compare_exchange_weak(pos, pos + 1, std::memory_order_relaxed)) {

break;

}

} else if (diff \< 0) {

return false; // full

} else {

pos = head\_.load(std::memory_order_relaxed);

}

}

cell-\>data = data;

cell-\>seq.store(pos + 1, std::memory_order_release);

return true;

}

std::optional\<T\> pop() {

Cell\* cell;

size_t pos = tail\_.load(std::memory_order_relaxed);

while (true) {

cell = &buffer\_\[pos % capacity\_\];

size_t seq = cell-\>seq.load(std::memory_order_acquire);

intptr_t diff = static_cast\<intptr_t\>(seq) - static_cast\<intptr_t\>(pos + 1);

if (diff == 0) {

if (tail\_.compare_exchange_weak(pos, pos + 1, std::memory_order_relaxed)) {

break;

}

} else if (diff \< 0) {

return std::nullopt; // empty

} else {

pos = tail\_.load(std::memory_order_relaxed);

}

}

T result = cell-\>data;

cell-\>seq.store(pos + capacity\_, std::memory_order_release);

return result;

}

size_t capacity() const {

return capacity\_;

}

private:

struct Cell {

std::atomic\<size_t\> seq;

T data;

};

const size_t capacity\_;

std::unique_ptr\<Cell\[\]\> buffer\_;

std::atomic\<size_t\> head\_;

std::atomic\<size_t\> tail\_;

};

## **🧪 Example Usage**

\#include \<iostream\>

\#include \<thread\>

int main() {

LockFreeMPMCQueue\<int\> q(4);

std::thread prod1(\[&\] {

for (int i = 0; i \< 5; ++i) {

while (!q.push(i)) {}

std::cout \<\< "Producer 1 pushed: " \<\< i \<\< "\n";

}

});

std::thread prod2(\[&\] {

for (int i = 100; i \< 105; ++i) {

while (!q.push(i)) {}

std::cout \<\< "Producer 2 pushed: " \<\< i \<\< "\n";

}

});

std::thread cons1(\[&\] {

int count = 0;

while (count \< 5) {

auto val = q.pop();

if (val) {

std::cout \<\< "Consumer 1 popped: " \<\< \*val \<\< "\n";

++count;

}

}

});

std::thread cons2(\[&\] {

int count = 0;

while (count \< 5) {

auto val = q.pop();

if (val) {

std::cout \<\< "Consumer 2 popped: " \<\< \*val \<\< "\n";

++count;

}

}

});

prod1.join();

prod2.join();

cons1.join();

cons2.join();

return 0;

}

## **🛠 Notes**

- This implementation is very fast and widely used (e.g. in [<u>MoodyCamel's ConcurrentQueue</u>](https://github.com/cameron314/concurrentqueue)).

- It's lock-free but **not wait-free** — threads may spin briefly under contention.

- It's **bounded** — you must fix capacity at construction.

Want:

- A wait-free version?

- A blocking wrapper using condition variables?

- Benchmarks against std::queue or folly?

Let me know what you'd like to build on top!
