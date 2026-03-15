# What does this mean "DUPLICATE KEY(order_id)", is this equivalent to mysql normal index?


No — **`DUPLICATE KEY(order_id)` in StarRocks is *not* equivalent to a normal index in MySQL.**

It actually defines the **table’s storage model**, not just an index.

Think of it more like **how the table is physically organized**.

---

# 1. What `DUPLICATE KEY(order_id)` means

Example:

```sql
CREATE TABLE orders (
    order_id BIGINT,
    user_id BIGINT,
    amount DOUBLE
)
DUPLICATE KEY(order_id)
DISTRIBUTED BY HASH(order_id);
```

Meaning:

| Property               | Behavior                     |
| ---------------------- | ---------------------------- |
| Duplicate rows allowed | YES                          |
| Deduplication          | NO                           |
| Aggregation            | NO                           |
| Sorting                | Data is sorted by `order_id` |

So rows like this are allowed:

| order_id | user_id | amount |
| -------- | ------- | ------ |
| 1        | 100     | 50     |
| 1        | 101     | 60     |
| 1        | 102     | 70     |

StarRocks simply **stores duplicates**.

---

# 2. What the KEY actually does

The key determines:

1. **Sort order of data**
2. **Prefix index columns**
3. **Query pruning capability**

Internally the storage is roughly:

```
segment
  ├── prefix index (order_id)
  ├── zone map
  └── column data
```

So queries like:

```sql
SELECT * FROM orders WHERE order_id = 1;
```

can quickly locate relevant segments.

---

# 3. How this differs from MySQL index

In MySQL:

```sql
CREATE INDEX idx_order_id ON orders(order_id);
```

creates a **B-tree secondary index**.

| Feature                 | MySQL index | StarRocks DUPLICATE KEY |
| ----------------------- | ----------- | ----------------------- |
| Separate structure      | Yes         | No                      |
| B-tree                  | Yes         | No                      |
| Used for point lookup   | Yes         | Partially               |
| Controls storage layout | No          | Yes                     |

StarRocks instead relies on **columnar storage + pruning**.

---

# 4. StarRocks table models

The key also defines the **table type**.

| Type            | Meaning          | Behavior           |
| --------------- | ---------------- | ------------------ |
| `DUPLICATE KEY` | raw data         | duplicates allowed |
| `PRIMARY KEY`   | upsert table     | deduplicates       |
| `UNIQUE KEY`    | unique rows      | merge on load      |
| `AGGREGATE KEY` | aggregated table | pre-aggregation    |

Example:

```sql
PRIMARY KEY(order_id)
```

means **UPSERT semantics**.

---

# 5. Example behavior comparison

### MySQL

```sql
INSERT INTO orders VALUES (1,100);
INSERT INTO orders VALUES (1,200);
```

If `order_id` is PK → second fails.

---

### StarRocks DUPLICATE KEY

```sql
INSERT INTO orders VALUES (1,100);
INSERT INTO orders VALUES (1,200);
```

Both rows stored.

---

# 6. When to use DUPLICATE KEY

Typical workloads:

| Workload      | Reason              |
| ------------- | ------------------- |
| event logs    | duplicates expected |
| clickstream   | append-only         |
| metrics       | many inserts        |
| raw ingestion | no dedupe needed    |

It is the **most common StarRocks table type**.

---

✅ **Short mental model**

```
MySQL index → lookup structure
StarRocks key → storage layout
```

---

💡 If you're exploring StarRocks seriously, the **most important concept to understand** is:

**Why `DUPLICATE KEY` tables are often *faster than PRIMARY KEY tables* for analytics queries.**

This surprises many engineers coming from MySQL. I can explain the internal reason (it involves **merge-on-read vs append storage**).


# Why DUPLICATE KEY tables are often faster than PRIMARY KEY tables for analytics queries.

In StarRocks, **`DUPLICATE KEY` tables are often faster than `PRIMARY KEY` tables for analytics queries** because their **storage and write path are simpler** and better optimized for **large scans**, which is what OLAP workloads usually do.

This is quite different from how things work in MySQL.

---

# 1. Storage model difference

### DUPLICATE KEY table

Storage is **append-only**.

```
INSERT
   ↓
write new segment
   ↓
query scans segments
```

Characteristics:

| Property       | Behavior                 |
| -------------- | ------------------------ |
| writes         | append                   |
| updates        | treated as new rows      |
| deduplication  | none                     |
| storage layout | simple columnar segments |

This makes reads **very efficient for scanning**.

---

### PRIMARY KEY table

Storage requires **deduplication / upsert handling**.

```
INSERT / UPSERT
   ↓
primary key index lookup
   ↓
merge with existing row
   ↓
write new version
```

Characteristics:

| Property         | Behavior          |
| ---------------- | ----------------- |
| writes           | upsert            |
| deduplication    | enforced          |
| storage layout   | merge-on-write    |
| extra structures | primary key index |

This adds **extra overhead**.

---

# 2. What happens during queries

### DUPLICATE KEY query

```
scan column segments
   ↓
vectorized filter
   ↓
aggregation
```

Very efficient for:

* full scans
* aggregations
* large analytics queries

---

### PRIMARY KEY query

Extra steps may occur:

```
scan
   ↓
check latest row version
   ↓
skip outdated versions
```

This adds CPU and memory overhead.

---

# 3. Data structure complexity

| Feature            | DUPLICATE KEY | PRIMARY KEY       |
| ------------------ | ------------- | ----------------- |
| storage            | append-only   | merge-on-write    |
| index              | prefix index  | primary key index |
| version management | none          | required          |
| scan complexity    | simple        | more complex      |

So analytic scans are usually faster on `DUPLICATE KEY`.

---

# 4. Write amplification

PRIMARY KEY tables may perform:

* index updates
* compaction
* version merges

While DUPLICATE KEY tables simply append:

```
new segment → done
```

Less write overhead → better ingestion throughput.

---

# 5. Typical workload comparison

### Analytics workload

Example:

```sql
SELECT user_id, COUNT(*)
FROM events
GROUP BY user_id;
```

Best table type:

```
DUPLICATE KEY
```

Because it scans all rows anyway.

---

### Upsert workload

Example:

```sql
UPDATE user_balance
SET balance = balance + 100
WHERE user_id = 123;
```

Best table type:

```
PRIMARY KEY
```

Because duplicates must be prevented.

---

# 6. Real-world StarRocks usage pattern

Many production systems use:

| Table type    | Purpose                |
| ------------- | ---------------------- |
| DUPLICATE KEY | raw events             |
| PRIMARY KEY   | dimension tables       |
| AGGREGATE KEY | pre-aggregated metrics |

---

# 7. Performance rule of thumb

In StarRocks:

```
DUPLICATE KEY → fastest scan performance
PRIMARY KEY → best for upsert workloads
```

---

# 8. Why OLAP engines prefer append-only storage

Columnar analytics engines (including StarRocks) are optimized for:

* **large sequential scans**
* **vectorized execution**
* **data skipping (zone maps, prefix indexes)**

Append-only data fits this model perfectly.

---

✅ **Simple mental model**

```
DUPLICATE KEY = log storage (fast scans)
PRIMARY KEY = upsert storage (more logic)
```

---

💡 One very interesting thing many engineers miss:

A **badly chosen StarRocks key order can make queries 10–100× slower**, even if the table type is correct.

If you'd like, I can show a **real example where changing the key order makes a query 50× faster**.





