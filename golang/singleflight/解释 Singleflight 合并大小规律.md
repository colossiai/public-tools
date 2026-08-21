Go 的 `singleflight` **不是按“请求时间窗口”自动判断同一批请求**，而是通过一个 **key** 来界定。

核心规则：

> **同一时刻，对同一个 key 的请求，会被合并成一次执行。**

例如：

```go
var g singleflight.Group

v, err, shared := g.Do("user:123", func() (any, error) {
    return loadUserFromDB(123)
})
```

如果同时来了 100 个请求：

```text
Request A ── Do("user:123") ──┐
Request B ── Do("user:123") ──┤
Request C ── Do("user:123") ──┤──> loadUserFromDB() 一次
...                            │
Request Z ── Do("user:123") ──┘
```

最终：

```text
loadUserFromDB() 执行 1 次
100 个请求拿到同一个结果
```

### 关键是 key

比如：

```go
g.Do("user:123", fn)
g.Do("user:123", fn)
```

会合并。

但：

```go
g.Do("user:123", fn)
g.Do("user:456", fn)
```

不会合并。

---

### 那“同一批”到底怎么定义？

可以理解成：

```text
key 相同
+
前一个 fn 还没有执行完
```

两个条件同时满足，就属于同一批。

例如：

```text
             fn 开始                    fn 结束
                │                         │
time ──────────┼─────────────────────────┼────────>

Request A      ├────── Do("A") ──────────┤
Request B          ├── Do("A") ──────────┤  ← 合并
Request C               ├─ Do("A") ──────┤  ← 合并

Request D                                      ├── Do("A")
                                               ↑
                                         不再合并
```

**Request D 虽然 key 一样，但前一批已经结束，所以会重新执行 fn。**

因此它不是：

> “100ms 内来的请求算一批”

而是：

> **“第一个请求启动了这个 key 的执行，在它执行完成之前加入的相同 key 请求，都属于这一批。”**

---

### 一个很重要的细节

假设：

```go
g.Do("user:123", func() {
    time.Sleep(time.Second)
    return loadUser()
})
```

那么：

```text
t=0ms    Request A → 开始执行
t=10ms   Request B → 等待 A
t=20ms   Request C → 等待 A
t=500ms  Request D → 等待 A
t=1000ms A 完成
```

A/B/C/D 都拿到 A 的结果。

但是：

```text
t=1100ms Request E → 新的一次执行
```

因为上一轮已经结束。

---

### `shared` 可以用来观察是否发生了合并

```go
v, err, shared := g.Do(key, fn)

if shared {
    // 这个结果被多个请求共享
}
```

例如：

```text
A: shared = false
B: shared = true
C: shared = true
```

通常可以把 `singleflight` 理解成：

```text
             same key
                │
                ▼
        ┌─────────────────┐
        │ 是否已有执行中？ │
        └────────┬────────┘
                 │
          ┌──────┴──────┐
          │             │
         No            Yes
          │             │
          ▼             ▼
      自己执行       等待已有执行
          │             │
          └──────┬──────┘
                 ▼
            共享结果
```

所以 `singleflight` 特别适合 **cache miss / 防击穿**：

```go
value, err, _ := g.Do(cacheKey, func() (any, error) {
    // 只有一个请求真正访问 DB
    return loadFromDB(cacheKey)
})
```

如果你想问的是 **“比如 1 秒内 100 个请求算一批，不管第一个请求有没有完成”**，那就不是 `singleflight` 的语义了，需要用 **debounce / batching / request coalescing** 之类的机制。
