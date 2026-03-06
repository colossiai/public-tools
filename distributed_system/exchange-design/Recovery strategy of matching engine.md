# In the top trading exchange, what is recovery strategy of the matching engine and tech stack?

Below is a **concise but industry-accurate** overview of the **recovery strategies** and **tech stacks** used by top-tier trading exchanges (CME, NASDAQ, ICE, HKEX, Eurex, etc.). Much of the detail is public knowledge from exchange technical docs, patents, engineering talks, and job descriptions.

---

# ✅ **1. Recovery Strategy of a Modern Matching Engine**

Top exchanges aim for **deterministic, lossless, sub-second recovery** with no order loss and no double execution. Nearly all major venues use some form of:

## **(A) Deterministic State Machine + Write-Ahead Log (WAL)**

Matching engine is a deterministic event processor:

* Input = market order events (AddOrder, Cancel, Modify, etc.)
* Output = trades
* State = order books + sequence numbers + user sessions

Every input event is durably written **before** applying:

* Write to replicated log (Aeron Archive / custom UDP multicast with disk append / shared memory + journal)
* Apply to engine
* Snapshot periodically
* On failure: replay WAL from last snapshot → rebuild full book

This is the same design style used by:

* **NASDAQ INET**
* **CME Globex**
* **LSE Millennium**
* **Eurex T7**
* **Binance/OKX/Huobi core engines** (modern crypto exchanges)

---

## **(B) Snapshot + Replay (Snapshot-Delta Recovery)**

Most exchanges take **frequent snapshots** of the matching engine state:

* Every **30 seconds → 5 minutes**, depending on venue and load
* Snapshot includes:

  * All order books
  * All live orders
  * Internal sequence counters
  * Risk limits (sometimes)

Recovery:

1. Load latest snapshot into a stand-by engine
2. Replay log events (delta) from snapshot position
3. Promote to primary, reconnect sessions

Snapshot formats typically:

* Memory-mapped binary dump (Agrona, SBE)
* Exchange proprietary serialized structs

---

## **(C) Hot/Warm Standby Matching Engines**

Almost all exchanges run:

* **Primary matching engine**
* **Hot standby** with continuous state replication
* **Warm DR engine** in secondary data center

Replication methods:

* Synchronous or async log replication
* Checkpoint state transfers
* Double journal commit (primary to mirror)

Failover target:

* **≤ 500 ms** (NASDAQ, CME class)
* **≤ 2 seconds** for lower-tier crypto exchanges

---

## **(D) Sequence-Number Guarantee**

Market data + order entry gateways enforce:

* Strict monotonically increasing sequence numbers
* Drop / request retransmission for gaps
* Ensure replay restoration produces **identical execution results**

---

## **(E) FIX Session or Binary Native Protocol Recovery**

Top exchanges use **binary protocols** for order entry:

* NASDAQ: **OUCH**, **ITCH**
* CME: **MBO + MDP 3.0 (SBE)**
* Eurex: **ETI (T7)**

Client recovery supported by:

* Flow control windows
* Fast resend for sequence gaps
* Drop & recover with "re-request from seq N"

---

# ✅ **2. Tech Stack Used in Top Exchanges**

Below is a realistic, widely-used tech stack in modern venues.

---

## **(A) Programming Languages**

### **1. Matching Engine / Market Data**

* **C++** (90% of legacy & current high-tier exchanges)
* **Java** (LSEG Millennium, some crypto, Eurex T7 gateway)
* **Rust** (some newer crypto exchanges)
* **Kotlin/Go** → rarely used in core, only edges

---

## **(B) Transport Layer**

### **Low-latency messaging**

* **Aeron** (Many crypto exchanges, some modern rebuilds)
* **UDP Multicast + custom binary protocol**
* **Solarflare/OpenOnload** or **DPDK** kernel bypass
* **Infiniband** for internal cluster replication

### **Protocols**

* **SBE (Simple Binary Encoding)**
* **FIX/FAST (older)**
* **Proprietary binary protocols**

---

## **(C) Persistence / Logging**

High-speed persistent logs:

* **Aeron Archive (journal + replay)**
* **LMDB** or **RocksDB** (rare, usually not used for book state)
* **Custom write-ahead logs** using:

  * Direct I/O
  * Memory-mapped files
  * HugePages
  * Pre-allocated files

---

## **(D) State Storage**

Most matching engine state is **kept in memory only**, with periodic snapshots.

Tools:

* **Agrona** (Java/C++) for off-heap structs
* **FlatBuffers** / **Cap’n Proto**
* **Custom lock-free data structures**

---

## **(E) Orchestration / OS**

* **Linux (RHEL / Ubuntu LTS)**
* **CPU pinning & isolation**
* **NUMA-aware memory layout**
* **RT kernel (low-latency tuned)**

---

## **(F) Monitoring**

* **Grafana + Prometheus**
* **Alerts via custom telemetry bus**
* **Kernel perf + perf_events**

---

# ✅ **3. What Specific Exchanges Use (Public Info)**

## **NASDAQ INET**

* Language: **C++**
* Protocol: **OUCH/ITCH**, FAST, SBE modernized feeds
* Logging: **deterministic replay journals**
* Recovery: **snapshot + replay**, <500ms
* Transport: **UDP multicast**, kernel bypass

## **CME Globex**

* Language: **C++**
* Market data: **MDP 3.0 (SBE)**
* Recovery: Engine snapshots + full WAL replay

## **LSE Millennium**

* Language: **Java**
* Messaging: **SBE**
* Persistence: shared memory journal

## **Eurex T7**

* Languages: **Java + C++ hybrid**
* Transport: **TCP + UDP multicast**
* Recovery: “Market Recovery Mode” replaying missing packets

## **HKEX Orion**

* C++ matching engine
* Multicast MMDP feed
* HA: multi-site active/passive DR

## **Crypto Exchanges (Binance / OKX / Coinbase / Deribit)**

Modern rebuilds log much public tech:

* **Aeron** for transport + archive
* **Java or C++** matching cores
* **LMAX Disruptor style ring buffers**
* **Snapshot + delta replay**
* Kernel bypass network stack

---

# ✅ **4. Reference Architecture Diagram (Common Across Exchanges)**

```
 Incoming Orders → Gateway → Journal Log → Matching Engine (Primary)
                                          ↘ Real-time Replication → Hot Standby

 Snapshot Service ← Matching Engine Memory Dump

 Recovery:
   Load snapshot
   Replay journal
   Promote engine
```

---

# If you want…

I can also generate:

📦 **A full matching-engine example (Java Aeron Snapshot + Replay) with downloadable zip**
📦 **A C++ version**
📚 **A full research-style comparison of exchange architectures**
🔧 **Explain how to build your own exchange-grade snapshot + WAL system**

Just tell me and I'll produce it.
