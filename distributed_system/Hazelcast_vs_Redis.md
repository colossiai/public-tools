# Performance comparison between hazelcast and redis


Here’s a **performance-focused comparison between Hazelcast and Redis** — covering architectural differences, scalability, throughput/latency behavior, and where each shines.

---

## 🚀 Architecture & Concurrency

**Redis**

* Single-threaded core per instance (even in clustered/enterprise setups, Redis processes are single-threaded).
* Excellent low-latency, high-throughput for single-server workloads.
* Can scale horizontally via **Redis Cluster sharding** but each shard remains single-threaded. ([Redis][1])

**Hazelcast**

* True **multi-threaded distributed in-memory data grid (IMDG)**: both client and cluster nodes use multiple threads and async I/O.
* Native **data partitioning and replication** across nodes, automatic discovery and rebalancing.
* Has rich distributed structures beyond simple key-value. ([Hazelcast][2])

**Implication**

* Redis tends to have **lower per-operation latency** on a single thread.
* Hazelcast can **better utilize multi-core CPUs and scale linearly** with more threads and nodes.

---

## 📊 Throughput & Latency (General Patterns)

**Low Concurrency / Simple Ops**

* Redis usually shows **faster raw get/set operations** with lower latency and excellent throughput in single-threaded tests. ([Hazelcast][3])

**High Concurrency / Multi-Threaded Clients**

* Hazelcast often **outperforms Redis as concurrent threads increase**:

  * Benchmarks have shown Hazelcast throughput surpasses Redis as threads grow (e.g., ~1.1M get ops/sec at high concurrency vs ~0.7M for Redis).
  * Latency of Hazelcast grows more *steadily* under heavy load, while Redis latency can increase sharply when its single thread is saturated. ([Hazelcast][3])

**Notes on Benchmarks**

* Many published benchmarks are **vendor-biased or configuration-dependent**. For example, Redis’s own benchmark against Hazelcast found Redis Enterprise significantly faster (~3.5× throughput, ~3× latency) when properly configured with pipelining and clustering. ([Redis][4])
* Real-world performance depends heavily on workload, data sizes, client libraries, network, and cluster config.

**Summary Pattern**

| Scenario                        | Redis                              | Hazelcast                            |
| ------------------------------- | ---------------------------------- | ------------------------------------ |
| Single thread                   | 🥇 Very fast                       | Good but less optimized              |
| High concurrency                | Limited by single thread per shard | Scales well with threads             |
| Distributed cluster             | Requires sharding + manual config  | Built-in automatic clustering        |
| Data processing + compute tasks | Not a focus                        | Designed for distributed computation |

---

## 🧠 Additional Performance Behaviors

**Near Cache / Client-Side Caching**

* Hazelcast supports **near caching** — local cache on clients with eventual consistency, greatly reducing latency on hot keys. ([Hazelcast][2])
* Redis doesn’t inherently offer this (though some clients/pro versions add local caching).

**Persistence Impact**

* Redis often turns persistence off for speed (pure in-memory), whereas enabling AOF/RDB adds I/O cost. Hazelcast also has persistence options (Hot Restart), but these influence performance in different ways. ([Svix][5])

**Distributed Compute**

* Hazelcast’s design allows **in-grid compute and event streaming**, meaning performance can cover both data access *and* compute tasks efficiently. Redis focuses on data store and simple pub/sub features. ([Hazelcast][6])

---

## 🧪 Practical Guidance: When Each Performs Best

### 🧠 Redis — Best Fit When

* You need **blazing low-latency key/value access** (cache, real-time, session state).
* Workloads are mostly single-shard or you can shard manually.
* You want simple deployment and a huge ecosystem of clients. ([Redis][1])

**Typical strengths**

* Sub-millisecond reads/writes
* Easy caching patterns
* Rich data structures (sorted sets, streams, hyperloglogs)

---

### 🏗️ Hazelcast — Best Fit When

* You need **true horizontal scalability** and high throughput across many cores/nodes.
* Your system involves distributed computing, event processing, or large in-grid data structures.
* You benefit from automatic clustering and data partitioning. ([Hazelcast][2])

**Typical strengths**

* Scale-out in multi-threaded environments
* Distributed compute + caching
* Automatic cluster rebalance

---

## 📌 Bottom Line

* **For simple, latency-critical caches and small clusters:** *Redis often gives best performance per operation.*
* **For large distributed systems with heavy concurrency or compute:** *Hazelcast scales better and may outperform Redis under load.*

**Important:** Always benchmark with your own workload — real performance is highly context dependent (data size, network, client concurrency, configs). ([Hazelcast][2])

---

If you want, I can tailor this comparison to specific use cases like **caching**, **session store**, or **stream processing** (e.g., Redis Streams vs Hazelcast Jet).

[1]: https://redis.io/compare/hazelcast/?utm_source=chatgpt.com "Redis vs Hazelcast | Redis"
[2]: https://hazelcast.com/blog/hazelcast-responds-to-redis-labs-benchmark/?utm_source=chatgpt.com "Hazelcast Responds to Redis Labs' Benchmark | Hazelcast"
[3]: https://hazelcast.com/blog/hazelcast-radargun/?utm_source=chatgpt.com "Redis vs. Hazelcast - RadarGun Puts Them To A Challenge | Hazelcast"
[4]: https://redis.io/blog/benchmarking-redis-enterprise-5-2-0-vs-hazelcast-3-9?utm_source=chatgpt.com "Benchmarking Redis Enterprise 5.2.0 vs. Hazelcast 3.9 | Redis"
[5]: https://www.svix.com/resources/faq/redis-vs-hazelcast/?utm_source=chatgpt.com "Redis vs Hazelcast | Svix Resources"
[6]: https://hazelcast.com/resources/hazelcast-vs-redis-practical-comparison/?utm_source=chatgpt.com "Hazelcast Versus Redis: A Practical Comparison | Hazelcast"
