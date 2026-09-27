# **Show how to build O(1) time complexity orderbook**

Nice — let’s build an **O(1) time-complexity** order book (for the common operations) and explain exactly when that guarantee holds and what the tradeoffs are.

**Short summary / result up front**

- You can get **O(1)** insert(limit), cancel(orderId), modify(orderId), and match() (consume best price) **if** you use a fixed-price grid (bounded price range + fixed tick) and store orders in price buckets indexed by price.

- Key ingredients: an array (direct-indexed by price ticks) of price-level buckets, each bucket holds a FIFO queue of orders (linked list/deque), and a fast bitset (or small hierarchy) to find the best non-empty price level in O(1).

- If price space is **unbounded** or you must maintain arbitrary price ordering, strict O(1) for best-price discovery is not possible without additional constraints — typical approaches are O(log N) trees/heaps or O(1) expected with approximate methods.

# When O(1) is possible (assumptions)

1.  **Fixed tick size** and **bounded price range**: e.g. prices are integers after mapping price_index = round((price - min_price)/tick) and 0 \<= price_index \< M. M is reasonable (e.g. millions).

2.  You accept memory proportional to M (not just number of active price levels).

3.  You can maintain a **bitset** (or small-level summary) of which buckets are non-empty, and can find the highest/lowest set bit in O(1) (hardware ffs/bsf or a small two-level table).

If you can accept those, the core operations are constant time.

# Data structures (conceptual)

- M = number of price buckets.

- buckets\[0..M-1\]: array where each entry is a price level that contains:

  - deque (or linked list) of orders at that price (maintains FIFO within same price level).

  - total_quantity at that price.

- order_map: hash map orderId -\> (price_index, pointer_to_order_node) for O(1) cancel/modify.

- bitset (size M): bit i = 1 if buckets\[i\] non-empty.

  - Use hardware find-first-set to get best bid/ask index in O(1). If hardware not available, use two-level bitsets to achieve O(1) table lookups.

- best_bid_index, best_ask_index: can also be cached and updated on changes (still O(1) updates).

Order object fields: orderId, side (buy/sell), qty, remaining, price_index, linked-list pointers (O(1) removal).

# Operations & complexity

- insert_limit(order):

  - compute i = price_to_index(price), append to buckets\[i\].deque, set bitset\[i\]=1 if was empty, add entry to order_map. → **O(1)**.

- cancel(orderId):

  - lookup order_map\[orderId\] -\> (i, node), remove node from deque (O(1) with pointer), update buckets\[i\].total_quantity, if bucket empty clear bitset\[i\], remove from map. → **O(1)**.

- match_market(order):

  - while remaining \> 0:

    - find best price index via bitset.find_first_set() → **O(1)**.

    - pop from bucket deque front, do fill (partial or full), update maps, clear bitset if empty. → each popped order O(1); overall matching cost proportional to number of fills, which is correct work; per-order operation is O(1).

- modify(orderId, new_qty):

  - O(1) via order_map and node pointer; if changing price to different index you do a cancel then insert (both O(1)).

# Implementation — illustrative Python (for clarity)

This is simplified, single-threaded, and assumes integer price indices 0..M-1. It demonstrates the structures and constant-time ops. In production you'd write in a systems language and add concurrency primitives.

\# Simplified O(1) orderbook using fixed-price grid.

from collections import deque

from dataclasses import dataclass

@dataclass

class Order:

order_id: str

side: str \# 'buy' or 'sell'

qty: int

remaining: int

price_idx: int

class PriceBucket:

def \_\_init\_\_(self):

self.queue = deque()

self.total = 0

class Bitset:

\# naive python bitset wrapper using ints; find_first_set uses bit_length

def \_\_init\_\_(self, M):

self.M = M

self.bits = 0

def set(self, i):

self.bits \|= (1 \<\< i)

def clear(self, i):

self.bits &= ~(1 \<\< i)

def any(self):

return self.bits != 0

def highest_set_index(self):

\# returns highest index where bit is 1, or None if none

if self.bits == 0:

return None

return self.bits.bit_length() - 1

def lowest_set_index(self):

if self.bits == 0:

return None

\# isolate lowest set bit

low = self.bits & -self.bits

return (low.bit_length() - 1)

class O1OrderBook:

def \_\_init\_\_(self, M, min_price_idx=0, max_price_idx=None):

self.M = M

self.buckets = \[PriceBucket() for \_ in range(M)\]

self.order_map = {} \# order_id -\> (Order, node represented by same Order object)

self.buy_bitset = Bitset(M) \# for bids (we'll treat higher index = better)

self.sell_bitset = Bitset(M) \# for asks (lower index = better)

\# mapping from price to index depends on tick/min_price etc in real system

def insert_limit(self, order_id, side, qty, price_idx):

order = Order(order_id, side, qty, qty, price_idx)

bucket = self.buckets\[price_idx\]

bucket.queue.append(order)

bucket.total += qty

self.order_map\[order_id\] = order

if side == 'buy':

self.buy_bitset.set(price_idx)

else:

self.sell_bitset.set(price_idx)

def cancel(self, order_id):

o = self.order_map.get(order_id)

if not o:

return False

bucket = self.buckets\[o.price_idx\]

\# remove o from deque: O(n) if using deque.remove; to be O(1) in practice, maintain linked nodes

\# For demonstration, assume we have the node; here we do a linear remove (not ideal)

try:

bucket.queue.remove(o)

except ValueError:

pass

bucket.total -= o.remaining

if not bucket.queue:

if o.side == 'buy':

self.buy_bitset.clear(o.price_idx)

else:

self.sell_bitset.clear(o.price_idx)

del self.order_map\[order_id\]

return True

def match_market(self, side, qty):

\# side is incoming side; match against opposite side

remaining = qty

if side == 'buy':

\# buy market order consumes from sell side (best ask = lowest index)

bitset = self.sell_bitset

get_index = bitset.lowest_set_index

else:

bitset = self.buy_bitset

get_index = bitset.highest_set_index

trades = \[\]

while remaining \> 0:

idx = get_index()

if idx is None:

break \# no liquidity

bucket = self.buckets\[idx\]

\# pop orders from front

while bucket.queue and remaining \> 0:

maker = bucket.queue\[0\]

take = min(remaining, maker.remaining)

maker.remaining -= take

remaining -= take

bucket.total -= take

trades.append((maker.order_id, take, idx))

if maker.remaining == 0:

bucket.queue.popleft()

del self.order_map\[maker.order_id\]

if not bucket.queue:

\# clear bit

bitset.clear(idx)

return trades

\# Example usage:

book = O1OrderBook(M=1000000) \# large fixed grid

book.insert_limit("o1", "sell", 100, price_idx=500) \# someone offers at bucket 500

book.insert_limit("o2", "sell", 50, price_idx=500)

book.insert_limit("o3", "buy", 200, price_idx=480)

print(book.match_market("buy", 120)) \# buy market order of 120 matches best asks

**Important note:** In that demo, deque.remove is O(n) so cancel isn't O(1). To make cancel truly O(1), implement orders as nodes in a doubly-linked list and store a direct pointer (reference) to the node in order_map. Removing a node from a doubly-linked list given the node pointer is O(1). In Python you'd implement small node objects; in C++/Rust/Go you'd use explicit pointers.

# How to implement the O(1) bitset lookup in practice

- Use machine instruction bsf/tzcnt/lzcnt via intrinsics (gives index of first/last set bit) → effectively O(1).

- If M can be very large (≥ 64k) you can use a two-level bitset:

  - top-level bitset with ceil(M / W) words (W=word size, e.g. 64), and second-level per-word bitsets.

  - Find first non-zero word (top-level) using bsf (O(1) on word count ~ M/W), then find the bit inside the word. With small top-level size this is still constant-time practically.

# Caveats, tradeoffs & production concerns

- **Memory**: the array-of-buckets approach uses O(M) memory even if few levels are used. Acceptable if M is bounded and not huge.

- **Unbounded price range**: if you need arbitrary prices, you cannot guarantee strict O(1) to find best price without additional assumptions; typical production implementations use balanced trees (O(log L) per price-level op) where L is active price-levels.

- **Precision & tick mapping**: map floats to integer indices deterministically to avoid rounding issues.

- **Concurrency**: true low-latency exchange code is lock-free or uses fine-grained locks per bucket. Serialization/atomicity is necessary for correctness under concurrent matching and cancels.

- **Persistent state / recovery**: store events (add/cancel/match) to durable log for recovery.

- **Orderbook features**: iceberg orders, hidden orders, pegged orders add complexity (often handled as metadata attached to nodes).

- **Latency**: Python demo is educational; production would be C/C++/Rust/Go to hit low-latency targets (microsecond order matching).

- **Edge cases**: partial fills, out-of-order cancels (cancels for already filled orders), etc. must be carefully handled.

# TL;DR / final recipe

1.  Choose a fixed-price grid (map price → integer index) with known M.

2.  Use buckets\[M\] array; each bucket keeps a doubly-linked list (queue) of orders and aggregate quantity.

3.  Keep order_map mapping orderId → node pointer.

4.  Keep a fast bitset marking non-empty buckets and use CPU bit ops or 2-level bitset to find best index in O(1).

5.  Insert/cancel/modify/pop from bucket using pointer removals → O(1). Matching repeatedly pops buckets (each pop is O(1)).

If you want, I can:

- produce a **production-ready, lock-free Go implementation** with node structs and O(1) cancel using direct node pointers,

- or implement the two-level bitset helper for M up to, say, 1 million,

- or sketch the version for **unbounded prices** (explain the best practical O(log L) tree alternative).

Which of those would you like next?
