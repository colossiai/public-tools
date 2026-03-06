
API **幂等性（Idempotency）** 的目标是：**同一个请求被重复执行 1 次或 N 次，系统最终状态一致**。
在你目前关注的 **后端 API 设计 / 高并发 / Go + Gin** 场景下，下面给你一套**工程化、可落地的幂等处理方案**。

---

## 一、先明确：哪些 API 必须幂等？

### 天然幂等（不额外处理）

* `GET /resources/{id}`
* `PUT /users/{id}`（**全量覆盖**）
* `DELETE /orders/{id}`（允许重复删除）

### **必须额外处理的**

* `POST /orders`
* `POST /pay`
* `POST /withdraw`
* `POST /signup`
* 任何 **“创建 / 扣钱 / 发放奖励 / 推进状态机”** 的接口

---

## 二、幂等的 5 种主流实现方式（按推荐度）

---

## ① Idempotency-Key（最推荐，业界标准）

### 适用

* 外部 API
* 支付 / 下单 / 发奖
* 前端、SDK 可控

### 设计

#### 客户端

```
POST /orders
Idempotency-Key: 550e8400-e29b-41d4-a716-446655440000
```

#### 服务端逻辑

```
key = user_id + idempotency_key
```

| 步骤  | 行为            |
| --- | ------------- |
| 第一次 | 执行业务 + 保存结果   |
| 重复  | **直接返回之前的响应** |

### 数据表设计

```sql
CREATE TABLE idempotency_keys (
  id BIGINT PRIMARY KEY,
  user_id BIGINT,
  key VARCHAR(64),
  status VARCHAR(16),
  response JSON,
  created_at TIMESTAMP,
  UNIQUE(user_id, key)
);
```

### 优点

✅ 标准（Stripe / AWS / OpenAPI 推荐）
✅ 支持 **安全重试**
✅ 不依赖请求内容

### 注意点

* key **必须由客户端生成**
* key 需设置 **TTL（如 24h）**

---

## ② 业务唯一约束（最简单、最可靠）

### 适用

* 业务有**天然唯一性**
* 创建类接口

### 示例

```
POST /orders
{
  "biz_order_no": "ORDER-20260105-001"
}
```

### DB 保证

```sql
UNIQUE(biz_order_no)
```

### Go 处理

```go
if errors.Is(err, gorm.ErrDuplicatedKey) {
    return queryOrder(bizOrderNo)
}
```

### 优点

✅ 极简单
✅ 强一致
✅ 无额外存储

### 缺点

❌ 仅适用于**有唯一业务键**

---

## ③ 状态机 + 乐观锁（强业务推荐）

非常适合你之前提到的 **onboarding / task / reward** 场景 👌

### 核心思想

* **只允许合法状态跃迁**
* 重复请求 = no-op

### 示例

```sql
status ENUM(
  'INIT',
  'PROCESSING',
  'DONE',
  'FAILED'
)
```

```sql
UPDATE task
SET status = 'DONE'
WHERE id = ? AND status = 'PROCESSING';
```

### 返回判断

* affected_rows = 1 → 成功
* affected_rows = 0 → 已处理 / 非法重复

### 优点

✅ 无需缓存
✅ 并发安全
✅ 业务语义清晰

---

## ④ Redis 原子锁（不推荐作为唯一方案）

### 典型实现

```bash
SETNX idempotent:{key} 1 EX 60
```

### 问题

❌ 服务重启丢失
❌ 结果不可复用
❌ 不能返回原响应

### 正确用法

👉 **只作为 DB 幂等的加速器**

---

## ⑤ 请求内容 Hash（慎用）

```text
hash = SHA256(user_id + body)
```

问题：

* JSON 字段顺序
* 时间戳
* 浮点精度

👉 **不建议在生产环境使用**

---

## 三、推荐组合方案（生产级）

### 创建类接口（POST）

```
Idempotency-Key
+ DB 唯一约束
+ 事务
```

### 状态推进类接口

```
状态机
+ 条件更新
```

### 高并发场景

```
DB 幂等
+ Redis 快速失败
```

---

## 四、Gin 中的通用幂等中间件（示意）

```go
func IdempotencyMiddleware(store Store) gin.HandlerFunc {
    return func(c *gin.Context) {
        key := c.GetHeader("Idempotency-Key")
        if key == "" {
            c.Next()
            return
        }

        if resp, ok := store.Get(key); ok {
            c.JSON(resp.Status, resp.Body)
            c.Abort()
            return
        }

        c.Next()

        store.Save(key, CaptureResponse(c))
    }
}
```

> ⚠️ 实际生产要处理：

* 请求进行中（processing）
* panic / rollback
* TTL
* body size

---

## 五、常见坑（很重要）

❌ **只靠 Redis 锁**
❌ **幂等 = 不报错**（错，应返回相同结果）
❌ **PUT 当 PATCH 用**
❌ **状态机无条件 UPDATE**

---

## 六、一句话总结

> **幂等不是“防重复请求”，而是“允许安全重试”**

如果你愿意，我可以：

* 给你一套 **Gin + GORM + MySQL 的完整幂等模板**
* 或帮你 **针对 onboarding / reward / task 状态机设计幂等模型**
* 或帮你把 **RFC 7807 错误模型 + 幂等冲突** 一起设计好
