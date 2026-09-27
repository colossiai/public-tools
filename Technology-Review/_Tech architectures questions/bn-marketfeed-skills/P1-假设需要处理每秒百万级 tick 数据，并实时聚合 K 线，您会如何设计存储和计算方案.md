这是一个**典型但难度很高**的行情系统问题，我直接按「**真实可落地的工程方案**」来讲，假设目标是：

> **百万级 tick / 秒 → 实时 K 线（1s / 1m / 5m / …）  
> 延迟稳定、可扩展、可回放**

## **一、先定几个关键前提（否则设计会跑偏）**

### **1️⃣ 不要用通用 OLAP / 大数据框架做实时核心**

- Spark / Flink：**延迟不可控**

- Kafka Streams：**batch + commit 模型不适合 µs 级**

👉 **实时 K 线 = 内存计算为主，存储为辅**

### **2️⃣ K 线是“状态型计算”，不是流式 SQL**

每根 K 线本质是一个状态：

Open / High / Low / Close / Volume

状态必须：

- 可并发

- 可恢复

- 可快照

## **二、整体架构（核心图）**

Tick Ingress

│

▼

Partition Router (按 instrument)

│

▼

In-Memory Kline Engine ←—— 实时计算核心

│ │

│ ├─ Push (WebSocket / TCP)

│ │

▼ ▼

Snapshot Writer Time-Series Storage

## **三、Tick 数据接入与分片（第一道关键）**

### **设计目标**

- 1,000,000+ ticks/s

- 不加锁

- 不乱序

### **分片策略（非常重要）**

shard = hash(instrumentId) % N

- 同一个 instrument **永远落在同一个 shard**

- 一个 shard = 一个线程 / 一个 core

- 单写者模型（Single Writer）

👉 **顺序、性能、正确性一次解决**

## **四、K 线实时计算（核心）**

### **1️⃣ 数据结构设计**

#### **每个 instrument × 每个周期 = 一个状态对象**

struct Kline {

long startTs;

double open;

double high;

double low;

double close;

long volume;

}

- **完全在内存**

- 不做任何对象分配（对象池 or struct）

### **2️⃣ Tick → K 线更新逻辑（O(1)）**

bucketStart = tick.ts / interval \* interval

#### **情况 A：当前 bucket**

- 更新 high / low / close / volume

#### **情况 B：跨 bucket**

- finalize 上一根 K

- emit（推送 + 存储）

- 初始化新 K

**⚠️ 永远不回看历史 tick**

### **3️⃣ 并发模型（决定上限）**

1 shard thread

├─ 接收 tick

├─ 更新 K 线

├─ 推送订阅

└─ 写 snapshot buffer

- **无锁**

- **无共享状态**

- cache 命中率极高

百万 tick 在几十核机器上是轻松的。

## **五、K 线推送设计（不要拖慢计算）**

### **原则**

> **计算线程永远不能被 IO 阻塞**

### **正确做法**

- 计算线程 → lock-free queue

- IO 线程异步推送

- 客户端慢 → 丢 / 降级

推送内容：

- 实时更新（未收盘）

- 收盘确认（final）

## **六、存储设计（分两类）**

### **🟢 1️⃣ 实时 / 热存储（秒级恢复）**

**目的**

- 服务重启快速恢复

- 不追求永久性

**方案**

- mmap 文件

- 本地 append log

- 顺序写

\[kline\]\[kline\]\[kline\]...

### **🔵 2️⃣ 历史 / 冷存储（分析 & 回放）**

#### **推荐模型：列式 + 时间序**

| **方案**          | **用途**       |
|-------------------|----------------|
| ClickHouse        | 秒/分钟 K 线   |
| Parquet + S3      | 离线分析       |
| InfluxDB          | 可视化         |
| HBase / Cassandra | Key-Range 查询 |

**⚠️ 不直接存 tick（太大）**

## **七、Tick 是否需要存？**

### **真实答案：只存“必要 tick”**

#### **常见策略**

- 全 tick 存 **最后 1–5 分钟**

- 长期只存：

  - K 线

  - VWAP

  - 成交统计

否则：

- IO 撑爆

- 成本爆炸

- 没人真的用

## **八、时间一致性问题（非常容易踩坑）**

### **使用哪种时间？**

- **交易所时间**

- 本地时间只用于 fallback

### **乱序 tick 怎么办？**

- 小乱序（\<1s）：允许

- 大乱序：

  - 丢弃

  - 或只影响当前 bucket

> 行情系统不追求“完美历史”，追求“实时正确性”

## **九、容错与恢复（决定是否可上线）**

### **1️⃣ 服务重启**

- 加载最近 snapshot

- 从最新 bucket 继续

### **2️⃣ 客户端重连**

- 下发：

  - 当前未完成 K

  - 最近 N 根已完成 K

## **十、性能估算（让方案可信）**

假设：

- 100 万 tick / 秒

- 10 万 instrument

- 平均 10 tick / instrument / 秒

在 32 核机器上：

- 每核 ~30k tick/s

- 单线程 O(1) 更新

- CPU 占用 \< 60%

**完全可行**

## **十一、关键反模式（一定要避开）**

❌ 用 Redis 聚合 K 线  
❌ 用数据库算 K 线  
❌ 用分布式事务  
❌ 每个 tick 写磁盘  
❌ 多线程更新同一 instrument

## **十二、一句话总结（这是精髓）**

> **百万级 tick 实时 K 线的本质是：  
> 按 instrument 分片 → 单线程内存状态机 → 异步 IO → 分层存储**

如果你愿意，下一步我可以继续：

- 设计 **多周期 K 线的最优计算方式**

- 讲 **撮合级别 K 线 vs 行情级 K 线差异**

- 对比 **Flink vs 内存引擎的真实延迟差距**

- 讲 **如何做 K 线回放 & 校验**

你想继续拆哪一块？
