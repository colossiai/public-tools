游标分页（Cursor-based Pagination）非常适合 **API 查询** 场景，尤其是你这种偏 **高性能 / 后端 API 设计** 的使用习惯。下面我从 **设计原则 → 接口定义 → SQL / NoSQL 实现 → 边界与坑** 系统讲一遍。

---

## 一、为什么用游标分页（而不是 offset）

### offset 分页的问题

```sql
SELECT * FROM orders ORDER BY created_at DESC LIMIT 20 OFFSET 100000;
```

❌ 缺点：

* `OFFSET` 越大，数据库扫描越慢（O(n)）
* 数据变动会导致 **重复 / 丢失**
* 在分布式 & 高并发场景不可控

### 游标分页的优势

* 时间复杂度 **O(page_size)**
* **稳定分页**（不会跳页）
* 非常适合：

  * 时间线 / 日志 / feed
  * 大表
  * 分布式数据库
  * 无总页数需求的 API

---

## 二、游标分页核心思想

> **用“最后一条记录的位置”作为下一页的起点**

通常基于：

* `id`（自增 / snowflake）
* `created_at`
* **复合游标（推荐）**

---

## 三、API 设计（推荐标准）

### 请求参数

```http
GET /api/orders?limit=20&cursor=eyJpZCI6MTAwMCwiY3JlYXRlZF9hdCI6IjIwMjYtMDEtMDFUMDA6MDA6MDAifQ==
```

| 参数     | 说明                         |
| ------ | -------------------------- |
| limit  | 页大小（建议 max 限制）             |
| cursor | 不透明游标（base64 / jwt / json） |

---

### 响应结构（推荐）

```json
{
  "items": [...],
  "page": {
    "next_cursor": "eyJpZCI6OTgwLCJjcmVhdGVkX2F0IjoiMjAyNi0wMS0wNFQxMDozMDowMCJ9",
    "has_more": true
  }
}
```

✔ 前端**不关心字段含义**
✔ 后端可随时变更游标结构

---

## 四、SQL 实现（重点）

### 1️⃣ 单字段游标（ID）

```sql
SELECT *
FROM orders
WHERE id < :last_id
ORDER BY id DESC
LIMIT :limit;
```

游标：

```json
{ "id": 1000 }
```

⚠️ 只适合：

* 单调递增 ID
* 不关心时间排序

---

### 2️⃣ 时间 + ID（强烈推荐）

避免 `created_at` 相同导致重复 / 丢失。

```sql
SELECT *
FROM orders
WHERE
  (created_at < :created_at)
  OR (created_at = :created_at AND id < :id)
ORDER BY created_at DESC, id DESC
LIMIT :limit;
```

游标内容：

```json
{
  "created_at": "2026-01-01T10:00:00Z",
  "id": 123456
}
```

✅ **稳定**
✅ **可回放**
✅ **支持时间排序**

---

### 索引（非常重要）

```sql
CREATE INDEX idx_orders_created_at_id
ON orders (created_at DESC, id DESC);
```

---

## 五、Gin + Go 示例（贴近你风格）

### Cursor 定义

```go
type OrderCursor struct {
	CreatedAt time.Time `json:"created_at"`
	ID        int64     `json:"id"`
}
```

### 编码 / 解码（不透明）

```go
func EncodeCursor(c OrderCursor) string {
	b, _ := json.Marshal(c)
	return base64.RawURLEncoding.EncodeToString(b)
}

func DecodeCursor(s string) (*OrderCursor, error) {
	b, err := base64.RawURLEncoding.DecodeString(s)
	if err != nil {
		return nil, err
	}
	var c OrderCursor
	return &c, json.Unmarshal(b, &c)
}
```

### 查询构造

```go
if cursor != nil {
	db = db.Where(
		"(created_at < ?) OR (created_at = ? AND id < ?)",
		cursor.CreatedAt, cursor.CreatedAt, cursor.ID,
	)
}

db = db.
	Order("created_at DESC").
	Order("id DESC").
	Limit(limit + 1)
```

`limit + 1` 用于判断 `has_more`

---

## 六、has_more 计算技巧

```go
items := results
hasMore := false

if len(items) > limit {
	hasMore = true
	items = items[:limit]
}
```

下一页游标 = `items[len(items)-1]`

---

## 七、前向 / 后向分页（进阶）

### 前向（默认）

```sql
id < cursor_id ORDER BY id DESC
```

### 后向（少用）

```sql
id > cursor_id ORDER BY id ASC
```

⚠️ 后向分页容易复杂化，建议：

* **只支持 forward**
* 或暴露 `direction=next|prev`

---

## 八、常见坑 & 设计建议

### ❌ 不要做的事

* 把 cursor 设计成 `page=3`
* 暴露 cursor 里的字段含义
* 没有稳定排序就用游标

### ✅ 最佳实践

* cursor **必须包含所有排序字段**
* 排序字段 **不可变 / 单调**
* cursor **不可猜测（base64 / jwt）**
* limit 有上限（如 100）

---

## 九、什么时候不适合游标分页？

| 场景         | 建议     |
| ---------- | ------ |
| 需要跳页       | offset |
| 需要总页数      | offset |
| 管理后台       | offset |
| feed / 时间线 | cursor |
| 大表 API     | cursor |

---

如果你愿意，我可以帮你：

* 直接**改你现有的 Gin/GORM 查询**
* 设计 **统一 Pagination middleware**
* 把它和 **字段掩码 / RFC7807 错误模型** 结合成一套 API 规范

你现在的表是按什么字段排序的？
