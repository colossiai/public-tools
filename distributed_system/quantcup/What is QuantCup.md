**QuantCup** was a **programming competition focused on quantitative trading infrastructure**, especially **ultra-fast exchange matching engines**. ([그대안의작은호수 | 살아온 날의 흔적, 살아갈 날의 기록][1])

It became famous in the **HFT / low-latency systems community** because the challenge was extremely close to what real trading firms build.

---

## 1. What QuantCup was

**QuantCup** was a **quant trading–themed programming contest** where participants had to implement a **high-performance limit order book matching engine** (like those used by stock exchanges). ([EJRH][2])

The goal:

* Implement the **fastest possible order matching engine**
* Handle operations such as:

  * **Add order**
  * **Match orders**
  * **Cancel order**
* Optimize **latency and throughput**

Contestants were given a **baseline implementation** and had to rewrite it to achieve better performance. ([그대안의작은호수 | 살아온 날의 흔적, 살아갈 날의 기록][1])

---

## 2. The core problem in QuantCup

Participants had to build an engine that processes a stream of orders:

Example operations:

```
limit(order)    // add new order
cancel(orderId) // cancel existing order
match()         // match buy and sell orders
```

Typical order structure:

```
order {
    trader
    side   (BUY / SELL)
    price
    size
}
```

The engine must maintain a **limit order book (LOB)**:

```
Bids (buy orders)
price: 100  size: 5
price: 99   size: 8

Asks (sell orders)
price: 101  size: 3
price: 102  size: 10
```

Matching rule (standard exchange rule):

**Price-time priority**

1. Best price first
2. FIFO within the same price

---

## 3. Why QuantCup became famous

QuantCup became popular because it highlights **real HFT engineering techniques**.

Participants optimized things like:

### Memory layout

Instead of trees or maps:

```
price -> array index
```

Pre-allocate all price levels.

### Cache locality

Avoid pointer chasing.

```
struct Order orders[MAX_ORDERS];
```

### Preallocation

Avoid malloc/free during trading.

### Intrusive data structures

Use linked lists embedded in structs.

These techniques are common in **real exchange engines and HFT systems**.

---

## 4. Example performance improvement

The baseline implementation score:

```
~14,500
```

Winning solution:

```
~437
```

Huge speedup due to **data-structure and memory optimization**. ([그대안의작은호수 | 살아온 날의 흔적, 살아갈 날의 기록][1])

---

## 5. What engineers learn from QuantCup

QuantCup is basically a **microcosm of exchange engine design**.

Important lessons:

### 1️⃣ Data structure choice matters more than algorithms

Example:

```
TreeMap  -> slow
Array    -> very fast
```

### 2️⃣ Memory allocation kills latency

Use:

```
object pools
static arrays
```

### 3️⃣ Cache locality dominates performance

Contiguous arrays >> linked structures.

### 4️⃣ Branch prediction & predictable code paths

---

## 6. Why trading firms care about this

Real trading systems must process:

```
1M+ orders / second
microsecond latency
```

So the matching engine must be:

* lock-free
* cache friendly
* allocation-free
* deterministic

QuantCup simulates this environment.

---

## 7. QuantCup example architecture

```
Market data feed
        │
        ▼
+--------------------+
|  Matching Engine   |
|                    |
| Order Book         |
|  - price levels    |
|  - order queues    |
+--------------------+
        │
        ▼
Trade events / executions
```

---

✅ **In short**

QuantCup =
**a programming competition about building an ultra-fast limit order book matching engine**, similar to what real stock exchanges and HFT firms implement.

---

If you're interested, I can also show:

* **The famous QuantCup winning order book design (very clever)**
* **How real exchanges like NASDAQ implement matching engines**
* **The 5 data structures used in HFT order books** (this is a very interesting topic).

[1]: https://smallake.kr/?p=6851&utm_source=chatgpt.com "매매체결엔진 퀀트컵"
[2]: https://ejrh.wordpress.com/2011/04/21/price-time-matching-engine/?utm_source=chatgpt.com "Price-time matching engine | EJRH - WordPress.com"
