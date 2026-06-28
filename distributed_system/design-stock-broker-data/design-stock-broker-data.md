```
How to design US stock broker market data module.
- I have market data vendor, but consider what kind of data I need to persist? candlestick?
- US stocks count is not small, 10k+
- how to manage stock feed subscription dynamically ?
```

---


For a US stock broker / trading app, think of market data as **three layers**:

1. **Reference/master data** (static-ish)
2. **Realtime trading state** (hot, ephemeral)
3. **Historical analytics data** (persisted)

A common mistake is trying to persist *everything* (all ticks for 10k+ symbols). That becomes expensive fast.

---

## 1. Separate market data into domains

### A. Instrument master data (persist)

You definitely persist this.

Schema idea:

```sql
instrument
-----------
symbol              -- AAPL.US
ticker              -- AAPL
exchange            -- NASDAQ
name
asset_type          -- stock/etf/option
currency
lot_size
status              -- trading/suspended/delisted
ipo_date
sector
industry
is_active
timezone
market_open_time
market_close_time
updated_at
```

Why?

* symbol lookup
* search/autocomplete
* trading eligibility
* delisting/suspension
* watchlist display
* reference joins

For US equities this is ~10k–20k rows only → trivial.

---

### B. Corporate actions (persist)

Also persist.

```sql
corporate_action
----------------
symbol
type           -- split/dividend/merger
effective_date
ratio
cash_amount
metadata_json
```

Needed for:

* adjusted candlestick
* P/L correctness
* chart correctness
* historical reconciliation

Example:

Apple Inc. 4-for-1 split must adjust historical candles.

---

### C. Trading calendar / market status (persist + cache)

Persist exchange calendar.

```sql
market_calendar
----------------
exchange
date
is_open
session_type    -- regular/half-day/holiday
open_ts
close_ts
```

Needed for:

* “market closed”
* holiday reminders
* session status
* countdown timers

---

## 2. What market data to persist?

Short answer:

**Persist candles, not all raw ticks (initially).**

### Recommended

Persist:

* minute candles (1m)
* daily candles
* maybe 5s/15s candles if needed
* latest quote snapshot

Do **not** persist every trade tick unless you have a clear product need.

Think:

```text
tick stream
   ↓
aggregator
   ↓
1m candle persisted
```

Schema:

```sql
ohlcv_1m
----------
symbol
minute_ts
open
high
low
close
volume
trade_count
vwap
```

Partition:

```text
by date
or
(symbol hash + date)
```

Why candles?

For broker UI:

* charts
* movers
* technical indicators
* screening
* analytics

Almost everything can run on candles.

You rarely need raw ticks except:

* time & sales tape
* audit/replay
* quant backtesting
* best execution analysis
* tick charts

---

### What about tick persistence?

Two approaches.

#### Option A — No tick storage (recommended v1)

Keep realtime tick only in memory:

```text
Vendor WS
   ↓
market-data-service
   ↓
Redis pubsub / Kafka
   ↓
frontend websocket
```

No DB.

You only maintain latest snapshot:

```sql
latest_quote
-------------
symbol
last_price
bid
ask
volume
change
change_pct
updated_at
```

This scales surprisingly far.

---

#### Option B — Short retention tick store

Persist for debugging/replay:

Example:

```text
Kafka topic retention = 3 days
```

or

```sql
tick_20260601
```

TTL after few days.

Useful for:

* replay bugs
* PnL disputes
* incident debugging

But not forever.

---

## 3. Architecture for 10k+ US stocks

Don’t subscribe to 10k realtime feeds blindly.

Key idea:

> **interest-driven subscriptions**

Only subscribe what users actually need.

Architecture:

```text
              ┌─────────────┐
              │ market vendor│
              └──────┬──────┘
                     │
          dynamic subscriptions
                     │
        ┌────────────────────┐
        │ market-data-service│
        └──────┬─────────────┘
               │
    ┌──────────┼───────────┐
    │          │           │
 realtime   candle agg   cache
 ws fanout     persist    redis
```

---

## 4. Dynamic subscription strategy

Maintain a **reference count** per symbol.

Example:

```go
type SymbolSubscription struct {
    Count      int
    LastActive time.Time
}
```

When user opens:

* watchlist
* quote page
* chart
* portfolio

increment interest:

```text
AAPL +1
TSLA +1
NVDA +1
```

When user leaves:

```text
AAPL -1
```

If count reaches zero:

delay unsubscribe.

Example:

```text
grace period = 2 minutes
```

Why?

Avoid churn.

Without grace period:

```text
open page
close page
open again
unsubscribe
subscribe
unsubscribe
subscribe
```

Vendor costs explode.

Better:

```text
count=0
wait 2 min
still zero?
unsubscribe
```

Pseudo:

```go
func Release(symbol string) {
    s.count--

    if s.count == 0 {
        go delayedUnsub(symbol)
    }
}
```

---

## 5. Multi-tier subscription policy

Treat symbols differently.

### Tier 1 — Always hot

Keep permanently subscribed.

Examples:

* top indices
* portfolio holdings
* top traded symbols

Like:

```text
SPY
QQQ
AAPL
MSFT
NVDA
TSLA
```

Maybe top 500–1000.

Why?

High hit rate.

---

### Tier 2 — User-driven

Dynamic subscription.

Watchlist, quote page, positions.

Example:

User watches:

```text
PLTR
AMD
SHOP
```

Subscribe only when active.

---

### Tier 3 — Cold universe

Never subscribe.

For all 10k symbols:

use delayed pull or snapshot API.

Example:

User searches:

```text
ZM
```

Fetch quote on demand.

No stream.

---

## 6. Use snapshots + streams

For 10k stocks, do this:

Realtime stream:

```text
few hundred / few thousand
```

Snapshot polling:

```text
all universe
```

Example:

Every 15–60 sec:

update:

```text
latest_quote
```

for broad universe.

Realtime only for active symbols.

This avoids:

```text
10k websocket subscriptions
```

---

## 7. Candlestick generation

Do not ask vendor for every timeframe.

Generate internally.

Persist only:

```text
1m candle
```

Then derive:

```text
5m
15m
1h
1d
```

Example:

```text
1m bars
   ↓ aggregate
5m bars
```

Why?

Cheaper and consistent.

Storage smaller.

Vendor-independent.

You can recompute.

If using a time-series DB like TimescaleDB:

```text
tick -> 1m hypertable
continuous aggregate
```

or

```text
1m -> 5m materialized aggregate
```

Since you mentioned TimescaleDB before, it fits well.

Recommended retention:

```text
1m   : forever or 2–5 years
daily: forever
tick : 0–7 days (optional)
```

---

## 8. Suggested service split

For a broker backend:

```text
instrument-service
    static symbol metadata

market-data-service
    realtime feed/subscription manager

quote-service
    latest snapshot API

chart-service
    candle query API

market-calendar-service
    holidays/trading session
```

Or simpler:

```text
market-data-service
    ├── realtime
    ├── candle persistence
    ├── subscription mgmt
    ├── market status
```

Start monolith, split later.

---

## My practical recommendation for v1

For a Futu-like broker:

Persist:

✅ instruments
✅ market calendar
✅ corporate actions
✅ latest quote snapshot
✅ 1-minute candles
✅ daily candles

Optional:

🟡 raw ticks (3–7 day retention)

Do NOT:

❌ subscribe 10k realtime symbols
❌ persist infinite tick history
❌ precompute every timeframe candle

Instead:

```text
dynamic subscription
+ interest ref counting
+ Redis cache
+ 1m candle persistence
```

This gets you surprisingly far before scaling pain appears.
