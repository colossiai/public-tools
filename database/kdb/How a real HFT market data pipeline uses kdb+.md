# How a real HFT market data pipeline uses kdb+

High-frequency trading (HFT) firms often use **kdb+** as the **core market-data time-series engine**. It is not just a database; it acts as a **real-time streaming analytics layer + historical store**.

Below is a **realistic architecture used by many trading firms** (Citadel / Jane Street / Two Sigma style).

---

# 1. Typical HFT Market Data Pipeline with kdb+

```
Exchange Feeds
   │
   │  (ITCH / OUCH / FIX / Binary feeds)
   ▼
Feed Handlers (C++ / FPGA)
   │
   │ normalize + decode
   ▼
Tickerplant (kdb+ real-time bus)
   │
   ├──────────────► Realtime Subscribers
   │                   ├ strategy engines
   │                   ├ risk engine
   │                   └ monitoring
   │
   ▼
Realtime Database (RDB)
   │
   ▼
Historical Database (HDB)
```

---

# 2. Stage 1 — Exchange Feed Handlers

Written in **C++ or FPGA** for minimal latency.

Responsibilities:

```
Exchange Binary Feed
     ↓
Decode
     ↓
Normalize
     ↓
Publish
```

Example normalized message:

```
timestamp,symbol,price,size,type
09:30:00.001234,AAPL,192.34,100,trade
```

Feeds:

Typical protocols:

* NASDAQ **ITCH**
* OUCH
* CME MDP
* FIX market data
* proprietary binary feeds

The handler usually publishes data via:

* TCP
* UDP multicast
* shared memory
* Aeron

to the **kdb+ tickerplant**.

---

# 3. Stage 2 — Tickerplant (the core kdb+ process)

The **tickerplant (TP)** is a **central real-time message bus** implemented in **q**.

Responsibilities:

1. Receive normalized market data
2. Append to log
3. Broadcast to subscribers
4. Guarantee replay ability

```
Feed Handler
     │
     ▼
Tickerplant
     │
     ├── publish to subscribers
     └── write to transaction log
```

Example q schema inside TP:

```q
trade:([]
    time:`timestamp$();
    sym:`symbol$();
    price:`float$();
    size:`int$()
)
```

Insert message:

```q
insert[`trade; (time;sym;price;size)]
```

Tickerplant does:

```
append → log file
publish → all subscribers
```

Typical latency:

```
5–20 microseconds
```

---

# 4. Stage 3 — Real-Time Database (RDB)

The **RDB** subscribes to the tickerplant.

Purpose:

```
Real-time in-memory analytics
```

Example:

```
Tickerplant
     │
     ▼
RDB (memory tables)
```

Example query:

```q
select last price by sym from trade
```

Example VWAP:

```q
select vwap:sum price*size % sum size by sym from trade
```

Strategies often query the RDB directly.

Latency:

```
< 100 microseconds
```

---

# 5. Stage 4 — Historical Database (HDB)

At **end of day**, the RDB data is **written to disk partitions**.

Structure:

```
/hdb
   /2026.03.20
       trade
       quote
```

kdb+ partition format:

```
date/symbol/time-series
```

Example query:

```q
select from trade
where date=2026.03.20,
      sym=`AAPL
```

Query performance:

```
billions of rows in milliseconds
```

---

# 6. Strategy Access Pattern

Strategies combine **live + historical** queries.

Example:

```
Strategy
   │
   ├─ realtime query → RDB
   └─ historical query → HDB
```

Example:

```q
/ current price
last select price from trade where sym=`AAPL

/ 30-day average
avg select price from trade
where sym=`AAPL,
      date within 2026.02.20 2026.03.20
```

---

# 7. Full Production Architecture

A real deployment looks like:

```
                 +------------------+
Exchange Feeds → | Feed Handlers    |
                 +------------------+
                           │
                           ▼
                 +------------------+
                 |  Tickerplant     |
                 +------------------+
                     │         │
                     │         │
                     ▼         ▼
               +---------+  +---------+
               |  RDB    |  |  Log    |
               +---------+  +---------+
                    │
                    ▼
               +---------+
               |  HDB    |
               +---------+
                    │
                    ▼
        Research / Backtesting / ML
```

---

# 8. Why HFT Firms Love kdb+

kdb+ has unique advantages:

### 1. Columnar time-series database

Perfect for market data.

Example:

```
timestamp | sym | price | size
```

Column scans are extremely fast.

---

### 2. Vectorized execution

Example:

```q
select avg price by sym from trade
```

Operates on **millions of rows per CPU instruction batch**.

---

### 3. In-memory + disk unified

Same query works on:

```
RDB (memory)
HDB (disk)
```

---

### 4. Built-in streaming

Tickerplant is essentially a **message broker + database**.

No Kafka needed.

---

# 9. Latency Expectations

Typical numbers inside trading firms:

| Component           | Latency   |
| ------------------- | --------- |
| Feed decode         | 1–5 µs    |
| Tickerplant publish | 5–20 µs   |
| RDB query           | 10–100 µs |
| Strategy decision   | 5–50 µs   |

Total pipeline:

```
~50–200 microseconds
```

---

# 10. Real Advanced Extensions

Top HFT firms add:

### FPGA feed handlers

```
Exchange → FPGA → kdb+
```

### Aeron transport

Using **Aeron** instead of TCP.

### GPU analytics

For research workloads.

### distributed kdb+

```
multiple HDB shards
```

---

# 11. Interesting Insight

Even **crypto exchanges** like **Coinbase** and traditional firms like **Citadel** have used architectures very close to this.

The **kdb+ tickerplant model became the industry standard** for market data.

---

✅ If you'd like, I can also show:

**1️⃣ The real kdb+ tickerplant q code (~60 lines)**
**2️⃣ How a strategy subscribes to tickerplant**
**3️⃣ How firms scale kdb+ to billions of ticks per day**
**4️⃣ How kdb+ compares with modern streaming stacks (Kafka + ClickHouse)**

The **tickerplant code is surprisingly small but extremely powerful.**
