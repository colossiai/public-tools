Vyukov's **bounded MPMC queue** is a **lock-free** multi-producer, multi-consumer ring buffer that allows multiple threads to **enqueue (push)** and **dequeue (pop)** concurrently without blocking. It was designed by Dmitry Vyukov and is known for its performance and low contention.

Here’s a breakdown of the core algorithm logic:

### **🔁 Ring Buffer Layout**

- The queue is implemented as a fixed-size ring buffer (bounded).

- Each slot in the buffer is a **cell** containing:

  - The **data value  **

  - A **sequence number** used for coordination between producers and consumers.

### **🧠 Core Concepts**

1.  **Sequence Numbers  **

    - Used to detect whether a slot is ready for enqueue or dequeue.

    - Every cell starts with a sequence number corresponding to its index.

    - This number helps determine if a cell is:

      - Ready to be written (seq == index)

      - Ready to be read (seq == index + 1)

2.  **Atomic Indices  **

    - enqueuePos (aka tail): Atomic counter used by producers.

    - dequeuePos (aka head): Atomic counter used by consumers.

3.  **Slot Indexing  **

The index into the ring buffer is calculated using:  
  
index = pos % buffer_size;

- 

### **✍️ Enqueue Operation (Producer)**

bool enqueue(T value) {

size_t pos = enqueuePos.fetch_add(1);

Cell& cell = buffer\[pos % size\];

size_t seq = cell.seq.load();

intptr_t diff = seq - pos;

if (diff == 0) {

// slot is free to write

cell.data = value;

cell.seq.store(pos + 1); // mark as full

return true;

} else {

// slot not ready, queue might be full

return false;

}

}

**Steps:**

1.  Atomically fetch and increment enqueuePos.

2.  Get the cell at pos % size.

3.  Check if cell.seq == pos (indicates slot is empty).

4.  If yes, write value and update cell.seq = pos + 1 to mark it full.

5.  If not, the queue is full or not yet consumed → return false.

### **🧾 Dequeue Operation (Consumer)**

bool dequeue(T& value) {

size_t pos = dequeuePos.fetch_add(1);

Cell& cell = buffer\[pos % size\];

size_t seq = cell.seq.load();

intptr_t diff = seq - (pos + 1);

if (diff == 0) {

// slot is full and ready to read

value = cell.data;

cell.seq.store(pos + size); // mark as empty

return true;

} else {

// slot not ready, queue might be empty

return false;

}

}

**Steps:**

1.  Atomically fetch and increment dequeuePos.

2.  Get the cell at pos % size.

3.  Check if cell.seq == pos + 1 (indicates slot is full).

4.  If yes, read the value and update cell.seq = pos + size to mark empty.

5.  If not, the queue is empty or not yet written → return false.

### **⚙️ Memory Ordering & Synchronization**

- It uses **atomic operations** and **memory fences** (often via std::atomic).

- The sequence number ensures proper **happens-before relationships**:

  - A consumer never sees uninitialized data.

  - A producer never overwrites unread data.

### **✅ Key Properties**

- **Lock-free**: No locks or mutexes; threads make progress independently.

- **Bounded**: Fixed size ring buffer, no dynamic memory allocation.

- **False-sharing minimized**: Padding is used to avoid cache-line contention.

### **📌 Visualization**

\[0\] \[1\] \[2\] \[3\] \[4\] ← circular buffer

↑ ↑

head tail

- Each slot holds a seq like: 0, 1, 2, etc.

- Enqueue compares seq == pos, dequeue compares seq == pos + 1.

Let me know if you want a C++ implementation or a diagram to help visualize it better.
