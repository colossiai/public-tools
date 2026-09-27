# Explain: snapshot+log to replay 

**“Snapshot + log to replay”** is a common technique in databases, message systems, and stateful services to reconstruct state efficiently and reliably.

Here’s the idea explained clearly:

# **✅ What is “snapshot + log” replay?**

It is a **state recovery strategy** that stores:

1.  **A snapshot** — a full copy of the system state at a point in time

2.  **A log (journal / WAL / event log)** — a sequential record of all updates after the snapshot

To recover state, you:

> **Load the snapshot → then replay the log entries → rebuild the latest state.**

# **🔍 Why use snapshot + log?**

If you only have a log, recovering state means replaying **all events since the beginning**, which can be very slow.

Example:  
If you have 50M log entries, replaying from the start is expensive.

So you take an occasional **snapshot** (e.g., every hour or every N events).  
Then you only replay logs **after** the snapshot.

# **🧠 How it works (step-by-step)**

Imagine an order book, a cache, or account balance system:

### **1️⃣ System runs and writes logs:**

Log \#1: A deposits \$100

Log \#2: A buys BTC

Log \#3: A withdraws \$10

...

### **2️⃣ At some interval, take a snapshot of current state:**

Snapshot at time T:

A balance = \$5230

B balance = \$110

Open orders: \[...\]

Positions: \[...\]

### **3️⃣ Continue writing logs after snapshot:**

Log \#1000231: A opens new position

Log \#1000232: B cancels order

### **4️⃣ Recovery:**

- Load snapshot (instant)

- Replay only the logs AFTER that snapshot (fast)

# **🏎️ Why this makes recovery efficient**

Recovery time = snapshot load time + replay logs since snapshot.

If snapshot is taken every 10 minutes, you only replay up to 10 minutes of logs, not years of history.

# **📦 Where “snapshot + log” is used?**

### **Databases**

- MySQL → binlog + snapshot

- PostgreSQL → base backup + WAL

- LevelDB/rocksDB → SST snapshots + WAL

### **Messaging & event systems**

- Kafka → compacted topic + log

- Event sourcing architectures

### **Trading systems / order books**

- Exchange matching engines use:

  - **Periodic state snapshot  **

  - **Incremental order events** for fast restart

### **Caches**

- Redis RDB snapshot + AOF log

# **🎯 Summary**

| **Component** | **Purpose**                                        |
|---------------|----------------------------------------------------|
| **Snapshot**  | Stores full state quickly for fast load            |
| **Log / WAL** | Stores all updates in order                        |
| **Replay**    | Apply logs to snapshot to rebuild the newest state |

**This gives durability, fast recovery, and correctness.**

If you want I can explain:

- how to implement this in **Go  **

- snapshot formats (binary/JSON/Protobuf)

- consistency guarantees (atomic snapshot + log rotation)

- how exchanges implement snapshot + delta feeds

Just tell me!

# Suggest snapshot+log architecture for low-latency trading?

Nice — below is a practical, production-ready **snapshot + log architecture** tuned for **low-latency trading** (matching engines, risk engines, real-time PnL, etc.). I’ll give the architecture overview, concrete data/layout suggestions, recovery algorithm, replication options, tuning knobs and trade-offs you’ll need to make.

# **Goals & constraints**

- **Recovery fast** (seconds or less) — load snapshot + replay tiny WAL window

- **Runtime latency minimal** (micro- to low-millisecond order flow)

- **Durable** (no silent data loss for accepted fills) with configurable durability vs latency trade-offs

- **Deterministic replay** (idempotent, ordered state application)

- **Operationally simple to test & observe  **

# **High-level architecture**

1.  **In-memory primary state** — ultra-fast structures (arrays, lock-free maps, LMAX/Disruptor ring for event dispatch).

2.  **Append-only WAL (log)** — write-ahead, binary, segmented, immutable files with sequence numbers and checksums.

3.  **Periodic snapshots (checkpoints)** — compact binary dump of full or partitioned state to disk (or persistent memory).

4.  **Replication** — leader ships WAL records and snapshots to followers (sync/async options).

5.  **Recovery** — load latest snapshot, then replay WAL records with sequence numbers \> snapshot.last_seq.

6.  **Monitoring & health** — metrics for last snapshot seq, WAL size, replay time, ack lag.

Diagram (conceptual):  
Primary (in-memory) ← writes WAL → disk/NVMe → replicate WAL → followers  
Primary periodically writes Snapshot → disk / distribute → followers

# **Data formats & layout (concrete)**

**WAL entry (binary compact):**

\[magic 4B\]\[version 1B\]\[entry_len 4B\]\[seq 8B\]\[timestamp 8B\]\[op_type 1B\]\[payload ...\]\[crc32 4B\]

- seq = strictly increasing 64-bit sequence (global ordering)

- op_type = trade, order_add, order_cancel, balance_adjust, etc.

- payload = binary-encoded fields (use fixed-width where possible)

- Write using a preallocated buffer and single write() syscall (or pwrite to append position).

**Segmenting WAL:**

- Segment size = e.g. 64MB or 128MB. Name segments wal.\<start_seq\>.seg.

- On rotate, fsync the segment then atomically create new segment file.

- Keep an index/manifest mapping segment -\> start_seq -\> checksum.

**Snapshot file (binary):**

snapshot.\<last_seq\>.bin

\[header\]{last_seq, timestamp, version, manifest_offset, crc}

\[payload\]{serialized state partitions}

- Use compact binary (flatbuffers/CBOR/custom), or memory-map a binary image for zero-copy load.

- Include a small manifest JSON or protobuf for metadata (checksums, partition offsets).

**Atomic snapshot pattern:**

1.  Write snapshot to temp file snapshot.\<seq\>.tmp

2.  fsync temp

3.  rename -\> snapshot.\<seq\>.bin (atomic)

4.  update snapshot.latest symlink or small meta file with last_seq

# **Checkpointing strategy (how often)**

- For **ultra-low latency** systems: snapshot every **1–10 seconds** OR every **N events** (e.g., 100k ops) whichever happens first. This keeps replay windows small.

- For cheaper durability: snapshot less frequently but ensure WAL group-commit and replication keep logs small.

- Use **incremental snapshots** where you snapshot only changed partitions (orderbooks per symbol) — critical for exchanges with many symbols.

# **WAL durability & fsync policies (tradeoffs)**

- **Sync-per-event** (fsync each WAL append): safest but huge latency cost — not recommended for high throughput.

- **Group commit** (recommended): buffer writes, flush every X ms or after Y events. Typical: 1–5ms / up to 1–4k events. Achieves low latency while batching fsyncs.

- **O_DIRECT + AIO**: avoids page cache double-copy; careful with alignment and complexity.

- **Persistent memory (PMEM / NVDIMM)**: best latency; if available, treat WAL as persistent circular buffer in PMEM.

- **NVMe with battery-backed RAID** also helps.

Recommendation: **group commit** with latency SLO (e.g., 1ms–5ms) and explicit ack modes:

- **Accept modes**:

  - ACK_LOCAL — persisted to leader's WAL (fast)

  - ACK_REPLICA — persisted to at least one follower (safer)

  - ACK_QUORUM — wait for majority (strong durability, more latency)

# **Replication & high-availability**

Options:

1.  **Leader + followers (asynchronous)  **

    - Leader writes WAL and streams to followers (over TCP/Aeron/RDMA).

    - Followers apply asynchronously — very low leader latency.

    - Risk: small window of data lost if leader fails and followers haven’t persisted.

2.  **Leader + synchronous follower(s)** (recommended for critical fills)

    - Leader waits for follower ack for durability level required (one follower or quorum).

    - Use batching to reduce latency penalty.

3.  **Consensus (Raft/Paxos)  **

    - Guarantees consistency but adds protocol overhead and higher tail latency. Use only if you must avoid split-brain with automatic leader election and strong consistency.

Implementation tip: separate **durability replication** (WAL shipping) from **state machine replication** (apply), stream WAL segments to followers and let them persist then apply.

Transport choices:

- **Aeron** (UDP + reliable) or **raw TCP** with sendfile for speed.

- **RDMA** if cluster supports it — ultra low latency.

# **Snapshot distribution to followers**

- After snapshot creation, push to followers via:

  - **Streaming**: leader sends delta blocks and manifests; followers apply and atomically replace snapshot.

  - **Shared storage**: write to fast distributed filesystem (only if latency and consistency acceptable).

- Use rsync / sendfile or proprietary zero-copy transfer for speed.

- Followers must ensure snapshot.last_seq ≤ leader's WAL start for safe replay.

# **Recovery algorithm (explicit steps)**

1.  Find latest snapshot file snapshot.\<S\>.bin. Read last_seq = S.

2.  Load snapshot payload into in-memory structures (prefer mmap or optimized deserialization).

3.  Locate WAL segment(s) starting from sequence S+1.

4.  For each WAL entry with seq \> S:

    - Validate checksum and seq continuity.

    - Apply entry deterministically (ops must be idempotent or include seq guard).

5.  Mark last_applied_seq = last WAL seq.

6.  If incomplete/corrupt WAL segment discovered → fallback to earlier snapshot or fail-safe.

Make WAL application **idempotent** by having each state change keyed with seq and rejecting re-applies (if necessary). Keep last_applied_seq persisted.

# **Partitioning to minimize snapshot size & latency**

- Partition state by **symbol** (orderbook per symbol) or **shard** (range by symbol hash).

- Snapshot only partitions with changes since last snapshot (incremental).

- For recovery of particular symbol, only load snapshot + WAL for that partition (useful for sharded systems).

# **In-process performance patterns**

- Use lock-free queues / ring buffers (Disruptor-style) for inbound orders and internal processing to eliminate mutex latency.

- Keep WAL writes off the critical path if possible: append to in-memory buffer and let a dedicated I/O thread flush with group commit.

- Minimize allocations—use object pools.

- Use fixed-size binary encodings for most fields to avoid parsing overhead.

# **Concrete example parameters (starting point)**

- WAL segment size: **128 MB  **

- Snapshot interval: **every 2s** or **every 200k events  **

- Group commit flush interval: **1 ms** (or when \> 2k events)

- Retain WAL segments for: **2x snapshot interval** + extra for replication lag (configurable)

- Replication: leader → 2 followers; ack policy default ACK_LOCAL, critical ops use ACK_REPLICA.

# **Example WAL write pseudo-code (Go-like)**

// Called on matching engine accept, off critical path

entry := makeWALEntry(seq, now, opType, payload)

buf := entry.Bytes()

// append to in-memory write buffer for WALIO thread

walWriteQueue.Push(buf)

// WAL IO thread (single-threaded) batches:

for {

batch := queue.PopBatch(maxBytes, maxEvents)

write(batch) // single write syscall per batch

if shouldFsync() { fsync() }

if replicate { streamToFollowers(batch) }

ackWaitingRequests(batch.lastSeq) // wake up waiting acks if any

}

# **Observability & testing**

- Expose metrics: last_snapshot_seq, last_wal_seq, wal_size_bytes, replication_lag_ms, replay_time_ms

- Automated chaos testing: kill leader immediately after an accepted critical ACK_LOCAL and verify data durability / loss window.

- Recovery time tests: measure snapshot load + replay time under production-sized state.

# **Trade-offs & recommendations summary**

- Want absolute zero data loss → use sync replication (quorum) — higher latency.

- Want lowest latency → group commit + async replication + short snapshot interval; accept small recent-loss window.

- Use incremental partitioned snapshots to keep snapshot sizes tiny and recovery fast.

- Prefer memory-mapped snapshot load for minimal deserialization overhead.

- Use sequence numbers and checksums for deterministic replay and corruption detection.

- Consider PMEM/NVMe + RDMA/Aeron for extreme low-latency setups.

# **Quick checklist before implementation**

- Define durability SLOs & ack modes.

- Choose sequence numbering scheme (64-bit monotonic).

- Decide snapshot frequency & partitioning scheme.

- Choose WAL segment size and rotation policy.

- Implement atomic snapshot pipeline (write tmp → fsync → rename).

- Implement idempotent apply logic and last_applied_seq persistence.

- Design replication (async vs sync) and transport.

- Build observability & automated recovery tests.

If you want, I can:

- produce **detailed Go code** for WAL writer + snapshot writer (ready-to-run), or

- sketch the **matching-engine integration** (how to make operations idempotent and where to place fsync), or

- propose a **testing plan / chaos tests** for verifying durability and recovery.

Which follow-up would you like?
