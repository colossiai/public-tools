# **How to do WAL crash recovery with Kafka**

Suppose a trading exchange use kafka for messaging as Write-ahead-log, how to do crash recovery with this kafka?

Using **Kafka as a Write-Ahead Log (WAL)** for a trading exchange is a powerful design choice, but **crash recovery** must be carefully planned. Here's a structured explanation on how to do it:

### **✅ 1. Kafka as WAL: Basic Idea**

Kafka topics store **every transaction event**, such as:

- Order placement

- Order cancellation

- Trade execution

- Balance changes

These events are **appended** to Kafka in order, creating an **immutable log**, similar to a database WAL.

### **✅ 2. Key Kafka Features for Recovery**

Kafka provides the following features that help in crash recovery:

- **Durability:** Messages are persisted to disk.

- **Replication:** Topics can be replicated across brokers.

- **Offset management:** Consumers can restart from specific offsets.

### **✅ 3. Crash Recovery Strategy**

Assume your exchange services crashed (order matcher, balance engine, etc.). Here’s how to recover:

#### **Step 1: Stop All Producers and Consumers**

Prevent any new messages or partial processing during recovery.

#### **Step 2: Replay Kafka Topics**

Each service (matching engine, balance engine, etc.) should **replay Kafka topics** from the last known safe state. This could be:

- From the **beginning** (cold start), or

- From a **checkpoint offset** (warm restart)

##### **You typically need to:**

- Keep **offset checkpoints** in a durable store (e.g., database, RocksDB, Redis, or a local file with fsync).

- On recovery, read messages from the **checkpoint offset** onward.

#### **Step 3: Rebuild In-Memory State**

While replaying:

- Rebuild the **order book** (for matching engine)

- Recalculate **balances** (for wallet/balance engine)

- Reconstruct **positions** (for risk engine)

If all business logic is deterministic, replaying the same events will bring the system back to the correct state.

#### **Step 4: Checkpointing (Recommended)**

To reduce replay time:

- Periodically **snapshot** the in-memory state (e.g., every 1M events or every minute)

- On crash, load the latest snapshot and **replay only the tail** of the Kafka log

#### **Step 5: Resume Operation**

Once the recovered state is consistent:

- Resume message consumption and production

- Resume accepting client requests

### **🔒 Data Safety Best Practices**

| **Item**          | **Practice**                                          |
|-------------------|-------------------------------------------------------|
| Kafka Acks        | Use acks=all to ensure broker replication             |
| Topic Replication | Set replication factor ≥ 3                            |
| Consumer Offsets  | Do **not** rely on Kafka auto-commit; manage manually |
| Idempotency       | Make consumers **idempotent** to handle replays       |
| Monitoring        | Track lag and offsets per partition/consumer          |

### **✅ Example Recovery Flow**

Suppose your **order matcher** consumes from orders-topic.

1.  It crashed at offset 134215.

2.  Last **checkpointed state** was at offset 134000.

3.  On restart:

    - Load snapshot at offset 134000

    - Replay messages from offset 134001 to 134215 from Kafka

    - Catch up and resume

### **🧠 Extra Tips**

- Use **partitioning** to shard by symbolId or userId for parallelism.

- Use compacted topics for "latest state" streams if needed (e.g., user balances).

- Store snapshots in a versioned blob storage (e.g., S3).

Would you like a sample code structure for recovery logic in Go, Java, or another language?

# **Sample Golang code.**

Great! Below is a simplified **Golang sample** that demonstrates **Kafka-based WAL recovery logic**. It simulates:

- Kafka consumer

- Reading from a **checkpointed offset  **

- **Replaying** messages to rebuild in-memory state (e.g., order book)

- **Checkpointing** the latest processed offset

We'll use the [<u>segmentio/kafka-go</u>](https://github.com/segmentio/kafka-go) library for simplicity.

### **🧱 Assumptions**

- Kafka topic: "orders-topic"

- Partition: 0

- Checkpoints stored in local file: offset.checkpoint

- Message format: JSON with orderId, userId, and action

### **✅ Golang Example: WAL Recovery**

package main

import (

"bufio"

"context"

"encoding/json"

"fmt"

"os"

"strconv"

"time"

"github.com/segmentio/kafka-go"

)

const (

kafkaBroker = "localhost:9092"

kafkaTopic = "orders-topic"

partition = 0

checkpointFile = "offset.checkpoint"

checkpointEvery = 100 // number of messages between checkpoints

)

type OrderEvent struct {

OrderID string \`json:"orderId"\`

UserID string \`json:"userId"\`

Action string \`json:"action"\` // e.g. "place", "cancel"

}

var orderBook = make(map\[string\]OrderEvent)

func main() {

ctx := context.Background()

offset := loadCheckpoint()

// Setup Kafka reader from a specific offset

r := kafka.NewReader(kafka.ReaderConfig{

Brokers: \[\]string{kafkaBroker},

Topic: kafkaTopic,

Partition: partition,

MinBytes: 1e3,

MaxBytes: 1e6,

})

defer r.Close()

fmt.Printf("Replaying from offset: %d\n", offset)

r.SetOffset(offset)

messageCount := 0

for {

m, err := r.ReadMessage(ctx)

if err != nil {

fmt.Println("Error reading message:", err)

break

}

var evt OrderEvent

if err := json.Unmarshal(m.Value, &evt); err != nil {

fmt.Println("Invalid message format:", err)

continue

}

// Process and rebuild state

processEvent(evt)

// Update checkpoint every N messages

messageCount++

if messageCount%checkpointEvery == 0 {

saveCheckpoint(m.Offset + 1) // +1 to resume after this

fmt.Println("Checkpointed at offset", m.Offset+1)

}

}

}

// processEvent simulates rebuilding order book state

func processEvent(evt OrderEvent) {

switch evt.Action {

case "place":

orderBook\[evt.OrderID\] = evt

case "cancel":

delete(orderBook, evt.OrderID)

default:

fmt.Println("Unknown action:", evt.Action)

}

}

// loadCheckpoint returns the last saved offset

func loadCheckpoint() int64 {

f, err := os.Open(checkpointFile)

if err != nil {

fmt.Println("No checkpoint found. Starting from offset 0.")

return 0

}

defer f.Close()

scanner := bufio.NewScanner(f)

if scanner.Scan() {

offsetStr := scanner.Text()

offset, err := strconv.ParseInt(offsetStr, 10, 64)

if err == nil {

return offset

}

}

return 0

}

// saveCheckpoint writes the latest offset to disk

func saveCheckpoint(offset int64) {

f, err := os.Create(checkpointFile)

if err != nil {

fmt.Println("Failed to write checkpoint:", err)

return

}

defer f.Close()

\_, \_ = f.WriteString(strconv.FormatInt(offset, 10))

}

### **🧪 How to Test It**

1.  Produce events to orders-topic in Kafka (use kafka-console-producer.sh or Go)

2.  Kill the app midway

3.  Restart it — it should resume from the last checkpointed offset

### **🧠 Extensions for Real-World Use**

- Use **RocksDB** instead of map\[string\]OrderEvent for durability

- Use **gRPC** or **REST** interface to query state

- Store **checkpoint offsets** in a dedicated Kafka topic or PostgreSQL for HA

- Add **idempotency** check (e.g., deduplicate order IDs)

Let me know if you'd like to see a **producer**, **snapshot mechanism**, or an extension for **multi-partition** handling.

# **Consistency of snapshot saving**

1)  saveCheckpoint() only save offset, which is not enough, it need to save the orderBook snapshot along with the offset.

2)  Offset and orderbook snapshot need to be save atomically, otherwise will lead to data corruption

Excellent observation. You are absolutely right — **offset and snapshot must be stored atomically** to guarantee **strong consistency** between the Kafka log position and in-memory state.

If saveCheckpoint() succeeds but saveSnapshot() fails (or vice versa), then on recovery, you either:

- replay already-applied events (→ **duplicate effects**),

- or skip some events (→ **data loss**).

## **✅ Goal: Atomic Persistence of Offset + Snapshot**

We need to ensure **both offset and orderBook are persisted together** in a single atomic operation.

## **✅ Option 1: Save Both to a Single File (Recommended for Simplicity)**

Instead of two files, use **one JSON file** that stores:

{

"offset": 134201,

"orderBook": {

"order123": { "orderId": "order123", "userId": "u1", "action": "place" }

}

}

### **✅ Updated Go Types**

type Snapshot struct {

Offset int64 \`json:"offset"\`

OrderBook map\[string\]OrderEvent \`json:"orderBook"\`

}

## **✅ Revised Code for Atomic Snapshot**

### **🔧 saveSnapshotAtomic()**

func saveSnapshotAtomic(offset int64) {

snap := Snapshot{

Offset: offset,

OrderBook: orderBook,

}

data, err := json.MarshalIndent(snap, "", " ")

if err != nil {

fmt.Println("Failed to serialize snapshot:", err)

return

}

tmpFile := snapshotFile + ".tmp"

if err := os.WriteFile(tmpFile, data, 0644); err != nil {

fmt.Println("Failed to write temp snapshot:", err)

return

}

// Atomic rename

if err := os.Rename(tmpFile, snapshotFile); err != nil {

fmt.Println("Failed to commit snapshot atomically:", err)

}

}

### **🔧 loadSnapshotAtomic()**

func loadSnapshotAtomic() (int64, bool) {

data, err := os.ReadFile(snapshotFile)

if err != nil {

fmt.Println("No snapshot found. Starting fresh.")

return 0, false

}

var snap Snapshot

if err := json.Unmarshal(data, &snap); err != nil {

fmt.Println("Failed to decode snapshot:", err)

return 0, false

}

orderBook = snap.OrderBook

return snap.Offset, true

}

## **✅ Usage in main()**

Replace both loadCheckpoint() and loadSnapshot() with:

offset, ok := loadSnapshotAtomic()

if !ok {

offset = 0 // fallback

}

And replace both saveCheckpoint() and saveSnapshot() with:

saveSnapshotAtomic(offset)

## **✅ Benefits**

| **✅ Feature** | **✅ Description** |
|----|----|
| Atomicity | Snapshot and offset always match — no mismatch or corruption |
| Simplicity | Easy to reason about recovery |
| Durability | Ensures persisted state reflects only fully processed messages |

## **🧠 Production Enhancements (Optional)**

- Add version or timestamp fields to snapshot

- Compress using zstd/gzip

- Use **fsync()** or os.File.Sync() for extra durability

- Store in **WAL + snapshot folder rotation** (snapshot_00000012.json)

Would you like this wrapped into a reusable package or extended to support sharded topics or RocksDB?

# **Why recommend RocksDB not other db like mysql, postgresql?**

Great question. When designing a **high-performance, fault-tolerant trading system**, the choice of database is critical. Here's **why RocksDB is often recommended** over traditional databases like MySQL or PostgreSQL for use in **Kafka-backed WAL-based recovery systems**, especially in trading or real-time systems.

## **✅ Why RocksDB Over MySQL/PostgreSQL**

||
||
||
||
||
||
||
||
||
||

## **🧠 Design Philosophy Fit**

RocksDB aligns better with **event-sourcing** and **log-replay** architectures where:

- Kafka is the source of truth (append-only WAL)

- Services **rebuild state** by replaying Kafka messages

- State is stored **locally** per service/matching engine/shard

In this model, **RocksDB is used as a fast, durable key-value state store**, not a queryable relational database.

## **📈 Use Cases Where RocksDB Wins**

- Order matching engines per symbol or shard

- User balance/state recovery per userId partition

- Real-time market data aggregation

- Millisecond/µs-level latency-sensitive apps

## **🛠️ When MySQL/PostgreSQL May Be Better**

- Need **complex relational queries  **

- Require **multi-table joins, foreign keys, constraints  **

- Build **reporting, analytics, dashboards  **

- Data lives in a **centralized system** (vs embedded engine per service)

In such cases, Kafka → RocksDB can still be the **runtime state** layer, and PostgreSQL can be the **sink layer** (using tools like Kafka Connect or CDC).

## **✅ Hybrid Model (Recommended for Trading Systems)**

| **Layer**          | **Technology**           | **Purpose**                   |
|--------------------|--------------------------|-------------------------------|
| Real-time state    | RocksDB                  | Fast local access, WAL-backed |
| System-of-record   | Kafka                    | Append-only source of truth   |
| Analytical storage | PostgreSQL or ClickHouse | Reporting, queries            |
| Archival           | S3 or HDFS               | Cold storage, snapshots       |

## **TL;DR**

> Use RocksDB because it's **fast**, **embedded**, **resilient**, and **perfectly suited** for building deterministic, replayable, Kafka-driven services — especially in trading or low-latency systems.

Let me know if you’d like an example of how to use RocksDB in Go for order book persistence!
