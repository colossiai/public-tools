# How to persist in-memory queues (e.g., Disruptor) to disk in low-latency trading?


In low-latency trading you generally **don’t “persist the queue” directly**. You **persist the events** flowing *through* it, using patterns that keep the hot path lock-free and cache-friendly. With things like Disruptor, persistence is usually **orthogonal** to the queue.

Here are the proven approaches, from most common to more specialized.

---

## 1. Side-by-side persistence consumer (the standard pattern)

**Idea:**
One consumer on the ring buffer is responsible for durable writes. Trading logic consumers stay purely in memory.

```
Producer
   ↓
RingBuffer
   ├── Strategy / Matching Engine
   ├── Risk Checks
   └── Persistence / Journal Writer
```

**How it works**

* Each event is immutable once published
* A persistence consumer:

  * Reads events in sequence
  * Appends them to disk (usually sequential I/O)
* Other consumers never block on disk

**Why it’s fast**

* Single-writer, sequential writes
* No locks
* No syscalls in the hot path of producers

**Failure model**

* On restart, replay the journal to rebuild in-memory state
* Exactly how exchanges do order-book recovery

**Key rule**

> Never make producers wait for fsync.

---

## 2. Append-only journal (not queue serialization)

Instead of snapshotting the queue, you persist **events**:

```text
[OrderAccepted]
[OrderAmended]
[TradeExecuted]
[OrderCancelled]
```

This gives you:

* Deterministic replay
* Auditable history (often legally required)
* No complex queue state recovery

**Implementation tips**

* Preallocate log files
* Use fixed-size records if possible
* Write binary, not JSON
* Keep sequence numbers identical to ring buffer sequence

---

## 3. Async fsync batching (latency vs durability tradeoff)

Most HFT systems use **delayed durability**:

* Write to OS page cache immediately
* fsync every:

  * N microseconds, or
  * N messages, or
  * On market state boundaries

Typical numbers:

* fsync every 1–10 ms
* Risk exposure = last few ms of messages

This is an explicit business decision.

---

## 4. Memory-mapped files (ultra-low overhead)

For extreme latency sensitivity:

* `mmap` a large file
* Persistence consumer copies events into mapped region
* OS handles flushing

**Pros**

* No syscalls per write
* Very cache-friendly

**Cons**

* Crash consistency is trickier
* Need careful ordering + markers
* Harder to reason about partial writes

Often combined with:

* Sequence markers
* Checksums per block

---

## 5. Double-buffered logging (hot/cold path split)

Another common trick:

* Hot thread writes events into an in-memory buffer
* Background thread:

  * Flushes full buffers to disk
  * Rotates buffers

This avoids disk stalls entirely on the producer side.

---

## 6. Snapshot + journal (for faster restarts)

For large books:

* Periodic snapshot of derived state (order book, positions)
* Journal only stores incremental events since snapshot

On restart:

1. Load snapshot
2. Replay journal tail

This keeps startup time predictable.

---

## 7. Things you should **not** do

❌ Serialize the ring buffer structure itself
❌ Put disk I/O in producers
❌ Use blocking queues or locks in the hot path
❌ Use general-purpose databases for event durability
❌ fsync per message

---

## Minimal latency architecture (typical exchange / HFT)

```
NIC → Decoder → RingBuffer
                ├── Trading Logic
                ├── Risk
                └── Journal Writer → Append-only log → fsync batch
```

Latency impact:

* Producers: ~0
* Consumers: predictable
* Disk I/O: amortized, off hot path

---

## When you might break these rules

* Regulatory requirements demand per-message durability
* You’re building a post-trade or clearing system
* You accept higher latency for stronger guarantees

In those cases, you still isolate persistence from the queue.

---

If you want, tell me:

* latency budget (µs / ms),
* durability guarantees (at-most-once vs exactly-once),
* asset class (equities, crypto, futures),

and I can sketch a **concrete design** that fits your constraints.
