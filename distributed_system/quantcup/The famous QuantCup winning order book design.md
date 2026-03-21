The **QuantCup winning order book design** is famous in low-latency trading circles because it shows how a **simple memory layout can outperform sophisticated data structures** like trees or maps.

The key idea:

> **Use arrays and intrusive linked lists instead of dynamic data structures.**

This design is extremely **cache-friendly, allocation-free, and branch-predictable**.

Let's walk through it.

---

# 1. Core idea: Array-based price levels

Instead of storing price levels in a tree:

```
TreeMap<price, orders>
```

The winning design used a **direct index array**:

```
price_points[MAX_PRICE]
```

Example:

```
price = 100.25
index = 10025
```

Then:

```
price_points[index]
```

gives the order queue immediately.

### Structure

```c
PricePoint pricePoints[MAX_PRICE];
```

```
pricePoints
 ├─ 10000
 ├─ 10001
 ├─ 10002
 ├─ ...
 └─ 20000
```

This gives **O(1) price lookup**.

No trees.
No hashing.
No comparisons.

---

# 2. Each price level holds a FIFO order queue

Orders at the same price must follow **price-time priority**.

So each price level maintains a **linked list**.

```
pricePoints[10025]

head → order1 → order2 → order3 → NULL
```

Example structure:

```c
struct PricePoint {
    Order *head;
    Order *tail;
};
```

Appending an order:

```
tail->next = newOrder
tail = newOrder
```

This is **O(1)**.

---

# 3. Intrusive order structure (no extra allocations)

Orders contain their own pointers.

```c
struct Order {
    int id;
    int size;
    int price;
    struct Order *next;
};
```

So the list pointer is **inside the order itself**.

No external list nodes.

Benefits:

```
less memory
better cache locality
fewer allocations
```

---

# 4. Preallocated order pool

Instead of:

```
malloc(order)
```

they preallocate all orders.

```c
Order orders[MAX_ORDERS];
```

When a new order arrives:

```
Order *o = &orders[nextIndex++];
```

Benefits:

* zero allocation latency
* contiguous memory
* perfect cache behavior

---

# 5. Fast cancel using order ID lookup

Cancel requires **finding an order quickly**.

So they use **direct indexing by order ID**.

```
orders_by_id[order_id]
```

Example:

```c
Order *orderMap[MAX_ORDERS];
```

Now cancel is:

```
order = orderMap[id]
order->size = 0
```

Sometimes they **lazy delete** instead of removing from the list.

---

# 6. Tracking best bid and ask

Scanning the whole price array would be expensive.

So the engine maintains:

```
best_bid
best_ask
```

When an order is added or removed:

```
update best_bid / best_ask
```

Matching becomes:

```
while best_bid >= best_ask
    match orders
```

---

# 7. Full simplified architecture

```
                   +--------------------+
                   |    Order Map       |
                   | orders_by_id[id]   |
                   +---------+----------+
                             |
                             |
+-------------------------------------------------+
|               PRICE LEVEL ARRAY                 |
|                                                 |
| pricePoints[0]                                  |
| pricePoints[1]                                  |
| pricePoints[2]                                  |
| ...                                             |
| pricePoints[10025] -> order1 -> order2 -> ...   |
| ...                                             |
+-------------------------------------------------+

best_bid  ---> index of highest bid
best_ask  ---> index of lowest ask
```

---

# 8. Why this design is insanely fast

### 1️⃣ No memory allocation

Everything preallocated.

```
Order orders[MAX]
PricePoint levels[MAX]
```

---

### 2️⃣ Perfect cache locality

Sequential arrays:

```
orders[]
priceLevels[]
```

CPU cache loves this.

---

### 3️⃣ O(1) operations

Add order:

```
O(1)
```

Cancel order:

```
O(1)
```

Find price level:

```
O(1)
```

---

### 4️⃣ No complex structures

Avoid:

```
Red-black trees
Hash maps
Heaps
```

These cause:

* pointer chasing
* cache misses
* branch misprediction

---

# 9. Real trading systems use similar designs

This idea appears in:

* **NASDAQ matching engine**
* **LMAX exchange**
* **crypto exchanges**
* **HFT internal order books**

But production engines add:

```
lock-free queues
NUMA partitioning
SIMD optimizations
kernel bypass networking
```

---

# 10. Minimal pseudo-code

### Add order

```c
add_order(id, price, size):

o = &orders[next++]

o->price = price
o->size = size
o->next = NULL

level = pricePoints[price]

if level.tail:
    level.tail->next = o
else:
    level.head = o

level.tail = o
```

---

### Match

```c
while best_bid >= best_ask:

    buy  = pricePoints[best_bid].head
    sell = pricePoints[best_ask].head

    trade_size = min(buy.size, sell.size)

    buy.size  -= trade_size
    sell.size -= trade_size
```

---

✅ **Key takeaway**

The winning QuantCup design proved that:

> **The fastest data structure is often just a carefully designed array.**

Not a fancy algorithm.

---

If you want, I can also show something **even more interesting**:

* **The 3 real order book designs used in HFT firms**
  (Array book vs Tree book vs Hybrid book)

This is one of the **most important low-latency system design topics**.
