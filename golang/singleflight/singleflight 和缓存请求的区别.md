# singleflight 和缓存请求的区别


如果你说的“缓存请求”是 **请求结果缓存（request/result cache）**，那么 `singleflight` 和缓存解决的是两个不同的问题：

|          | singleflight    | 请求结果缓存             |
| -------- | --------------- | ------------------ |
| 核心目的     | **合并并发请求**      | **避免重复执行**         |
| 保存结果     | ❌ 不保存           | ✅ 保存               |
| 生命周期     | 一次执行期间          | TTL / 持久时间         |
| 第一个请求结束后 | 结果消失            | 结果继续存在             |
| 防缓存击穿    | 部分可以            | 本身容易出现击穿           |
| 典型场景     | 100 个并发请求同时查 DB | 10 秒内 10 万请求读同一个数据 |

### 举个例子

假设：

```go
func loadUser(id int64) User {
    return db.Query(id)
}
```

#### 1. 只有缓存

```text
              Cache
                │
        ┌───────┴───────┐
        │               │
       miss            miss
        │               │
        ▼               ▼
      DB query        DB query
```

100 个请求同时过来，而 cache 还没有数据：

```text
Request 1 ── miss ── DB
Request 2 ── miss ── DB
Request 3 ── miss ── DB
...
Request 100 ─ miss ─ DB
```

可能产生 **100 次 DB 查询**。

这就是典型的 **cache stampede / cache breakdown**。

---

### 2. singleflight

```text
Request 1 ──┐
Request 2 ──┤
Request 3 ──┤
...         ├── singleflight ── DB
Request 100 ┘
```

只有一个请求真正执行：

```text
DB query × 1
```

其他请求等待结果。

但是 DB 查询结束之后：

```text
singleflight
    ↓
结果消失
```

下一批请求来了，还是要重新查 DB。

---

### 3. 实际生产中通常两者一起用

这是最常见的模式：

```text
Request
   │
   ▼
┌─────────┐
│  Cache  │
└────┬────┘
     │ miss
     ▼
┌──────────────┐
│ singleflight │
└──────┬───────┘
       │
       ▼
      DB
       │
       ▼
    Set Cache
       │
       ▼
    Response
```

Go 代码大概是：

```go
func GetUser(id int64) (*User, error) {
    key := fmt.Sprintf("user:%d", id)

    // 1. cache
    if user := cache.Get(key); user != nil {
        return user, nil
    }

    // 2. singleflight
    v, err, _ := group.Do(key, func() (any, error) {
        // double check cache
        if user := cache.Get(key); user != nil {
            return user, nil
        }

        // 3. 真正访问 DB
        user, err := loadFromDB(id)
        if err != nil {
            return nil, err
        }

        // 4. 写 cache
        cache.Set(key, user, 10*time.Second)

        return user, nil
    })

    if err != nil {
        return nil, err
    }

    return v.(*User), nil
}
```

这里有一个非常重要的点：

> **Cache 负责“跨请求记住结果”，singleflight 负责“同一时刻只做一次”。**

所以可以简单记成：

```text
Cache       = 记住答案
singleflight = 正在算答案的时候，大家一起等
```

两者并不冲突，反而经常配合使用。
