# 解释 go-redis/redis_rate Burst

在 [go-redis/redis_rate](https://github.com/go-redis/redis_rate?utm_source=chatgpt.com) 中，`Burst` 表示：

> **令牌桶（Token Bucket）中允许积累的最大令牌数，也就是允许的瞬时突发流量（burst traffic）上限。**

例如：

```go
limiter := redis_rate.NewLimiter(rdb)

res, err := limiter.Allow(ctx, "user:123",
    redis_rate.Limit{
        Rate:   10,
        Period: time.Second,
        Burst:  20,
    },
)
```

含义：

* `Rate = 10`

  * 每秒生成 10 个 token
* `Burst = 20`

  * 桶最大容量为 20 个 token
  * 最多可以一次性消费 20 个请求

---

## 没有 Burst 时

假设：

```go
Rate: 10/s
Burst: 10
```

初始：

```text
桶里有 10 个 token
```

用户瞬间发：

```text
10 个请求
```

全部通过。

第 11 个请求：

```text
token = 0
```

被限流。

然后：

```text
100ms 后
```

恢复：

```text
1 token
```

只能再通过 1 个请求。

---

## Burst > Rate

假设：

```go
Rate: 10/s
Burst: 50
```

系统空闲了 5 秒：

```text
10 * 5 = 50 token
```

桶被填满：

```text
50 token
```

此时用户突然发：

```text
50 个请求
```

全部通过。

第 51 个请求：

```text
被拒绝
```

之后恢复速度仍然是：

```text
10 token/s
```

---

## 为什么需要 Burst

现实系统经常出现：

```text
平均 QPS 很低
但是偶尔瞬间爆发
```

例如：

### Web API

用户点击按钮：

```text
同时触发
10 个 Ajax 请求
```

如果：

```text
Rate=5/s
Burst=5
```

可能失败。

更合理：

```text
Rate=5/s
Burst=20
```

允许短时间爆发。

---

### Market Making / Trading

你的系统可能：

```text
平时：
2 order/s

行情剧烈波动：
100 orders 在 50ms 内产生
```

配置：

```go
Rate: 20/s
Burst: 100
```

表示：

```text
长期平均：
20 order/s

允许短时间：
100 order burst
```

防止策略被限流影响。

---

## Burst = 0 ?

在 `redis_rate` 里：

```go
redis_rate.PerSecond(10)
```

实际上等价于：

```go
Limit{
    Rate:   10,
    Period: time.Second,
    Burst:  10,
}
```

即：

```text
Burst 默认 = Rate
```

所以：

```go
redis_rate.PerMinute(60)
```

等价：

```go
Rate: 60
Period: 1m
Burst: 60
```

---

## 直觉理解

把令牌桶想象成一个水桶：

```text
Rate  = 水龙头流速
Burst = 水桶容量
```

例如：

```text
Rate  = 每秒加 10 升水
Burst = 桶最大 50 升
```

那么：

```text
平时没人取水
↓
桶慢慢装满 50 升

突然来了人
↓
一次拿走 50 升
↓
允许

再来一个人
↓
没水了
↓
拒绝
```

因此：

```text
Rate  控制长期平均流量
Burst 控制短期突发流量
```

这是令牌桶算法最核心的两个参数。


# 如果 Burst=1, Rate=10/s, 那么就是不允许同时接受多于1个请求？只能分开请求？

不完全是。

如果：

```go
Rate  = 10/s
Burst = 1
```

实际含义是：

```text
桶容量 = 1 个 token
补充速度 = 每 100ms 补充 1 个 token
```

所以：

* 任意时刻最多只能积累 1 个 token
* 不允许 token 存起来形成突发流量
* 请求必须基本均匀地到达

---

例如：

初始状态：

```text
token = 1
```

### 情况1：同时来 3 个请求

```text
t=0

req1 -> 消耗 token -> PASS
req2 -> token=0 -> REJECT
req3 -> token=0 -> REJECT
```

结果：

```text
✓
✗
✗
```

因为桶里最多只有 1 个 token。

---

### 情况2：每 100ms 一个请求

```text
t=0ms    req1
t=100ms  req2
t=200ms  req3
...
```

因为：

```text
每100ms生成1个token
```

所以：

```text
req1 ✓
req2 ✓
req3 ✓
...
```

都能通过。

---

### 情况3：10个请求在 50ms 内到达

虽然：

```text
Rate = 10/s
```

但：

```text
Burst = 1
```

意味着：

```text
桶里永远不会超过1个token
```

因此：

```text
第1个请求 ✓
后面9个请求 ✗
```

不会因为 Rate=10/s 就允许一次通过 10 个请求。

---

很多人第一次看到会误解成：

```text
Rate=10/s
⇒ 一秒允许10个请求
```

实际上 Token Bucket 更准确的理解是：

```text
Rate = token生成速度
Burst = token最大库存
```

所以：

| 配置                 | 效果                         |
| ------------------ | -------------------------- |
| Rate=10, Burst=10  | 最常见，允许瞬时10个请求              |
| Rate=10, Burst=100 | 长期10/s，但允许瞬时100个请求         |
| Rate=10, Burst=1   | 长期10/s，但几乎不允许任何突发          |
| Rate=1, Burst=100  | 长期1/s，但允许一次性消费100个积累的token |

---

从流量曲线看：

```text
Rate=10/s Burst=10

██████████
          ██████████
```

允许“成批”通过。

而：

```text
Rate=10/s Burst=1

█ █ █ █ █ █ █ █ █ █
```

强制请求均匀分布，每次最多放行 1 个。

因此你的理解：

> 不允许同时接受多于1个请求？

基本正确。

更精确地说：

> **任何时刻最多只有 1 个可用 token，因此几乎只能放行一个请求，后续请求必须等待下一次 token 补充（100ms 后）才能通过。**
