# Explain InnoDB db SKIP LOCKED

`SKIP LOCKED` 是 InnoDB（MySQL 8.0+）的一种行锁行为，用在 `SELECT ... FOR UPDATE` 或 `SELECT ... FOR SHARE` 语句中，用来 **跳过已经被其它事务锁住的记录**，让查询立即返回其它未锁记录，而不是等待锁释放。

非常适合做 **task queue / job worker** 场景。

---

# ✅ **SKIP LOCKED 是什么？**

当你执行：

```sql
SELECT * FROM t_task
WHERE done = 0
FOR UPDATE SKIP LOCKED;
```

行为如下：

* 对查询到的行加 **排他锁（X Lock）**
* 如果某一行已经被其它事务锁住（比如另一个 worker 正在处理），InnoDB **直接跳过这一行，不等，不阻塞**
* 返回所有可锁的行

---

# 🔥 **为什么要用 SKIP LOCKED？**

在传统的 `SELECT ... FOR UPDATE` 下，锁被占用 -> 查询会 **等待**，会造成 worker 派发不均衡。

使用 `SKIP LOCKED` 可以：

### ✔ 实现多 worker 并发抢任务

每个 worker 都执行相同 SQL，只会抢到未被其它 worker 锁住的任务。

### ✔ 避免死锁

因为跳过锁定行，不会出现 "互相等待"。

### ✔ 性能更高

实现 **高性能、分布式、安全** 的任务调度。

---

# 🧩 示例：安全领取任务

### **事务 A：**

```sql
BEGIN;
SELECT id FROM t_task
WHERE done = 0
ORDER BY id
LIMIT 1
FOR UPDATE SKIP LOCKED;
```

假设拿到了 task_id = 100 并开始处理。

### **事务 B：**

执行完全相同的 SQL，不会等事务 A：

* 如果 100 已被锁，跳过
* 拿到下一个 task → 101

---

# 🤖 Golang Worker 场景

你可以这样构建：

```go
func fetchTask(db *sql.DB) (*Task, error) {
    tx, err := db.Begin()
    if err != nil {
        return nil, err
    }

    row := tx.QueryRow(`
        SELECT id, user_id
        FROM t_task
        WHERE done = 0
        ORDER BY id
        LIMIT 1
        FOR UPDATE SKIP LOCKED`)

    var t Task
    if err := row.Scan(&t.ID, &t.UserID); err != nil {
        tx.Rollback()
        return nil, err
    }

    return &t, nil
}
```

然后 worker 在同一个事务中：

* 处理任务
* `UPDATE t_task SET done=1 WHERE id = ?`
* `COMMIT`

---

# 🛑 注意点

### 1. `SKIP LOCKED` 不保证公平（非 FIFO）

可能造成某些 rows 一直被跳过 → 需要配合 ORDER BY 或重试机制。

### 2. 必须在事务中使用

否则锁无意义。

### 3. MySQL 5.7 不支持

Must MySQL ≥ 8.0.

---

# 📌 总结（一句话）

> **InnoDB 的 `SKIP LOCKED` 是用来做高并发安全抢任务的，跳过已锁行，不等待，避免阻塞，非常适合 task queue。**

如果你需要我帮你写一份 **完整的 Go + MySQL "并发 worker 抢任务" 模板代码**，告诉我即可！
