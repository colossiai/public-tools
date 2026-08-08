# SQL 半连接



**SQL 半连接（Semi Join）** 可以理解为：

> **只关心左表中“是否存在”匹配记录，但不把右表的数据连接出来。**

它最典型的 SQL 写法就是 `EXISTS`。

### 例子

假设：

```text
orders
+----+----------+
| id | user_id  |
+----+----------+
| 1  | 100      |
| 2  | 101      |
| 3  | 102      |
+----+----------+

vip_users
+---------+
| user_id |
+---------+
| 100     |
| 102     |
+---------+
```

想找出**有 VIP 用户下的订单**：

```sql
SELECT *
FROM orders o
WHERE EXISTS (
    SELECT 1
    FROM vip_users v
    WHERE v.user_id = o.user_id
);
```

结果：

```text
order 1  user 100
order 3  user 102
```

这里就是 **Semi Join**：

```text
orders ──────┐
             ├── Semi Join ──> orders
vip_users ───┘
```

右边 `vip_users` 的作用只是：

> **告诉我这个 user_id 有没有匹配。**

而不是把 `vip_users` 的行也输出出来。

genui{"data_networks_databases_learning_block":{"type_id":"SQL_JOIN","locale_override":"zh-CN"}}

### Semi Join vs INNER JOIN

容易混淆的是：

```sql
-- INNER JOIN
SELECT o.*
FROM orders o
JOIN vip_users v ON v.user_id = o.user_id;
```

和：

```sql
-- Semi Join
SELECT o.*
FROM orders o
WHERE EXISTS (
    SELECT 1
    FROM vip_users v
    WHERE v.user_id = o.user_id
);
```

如果 `vip_users.user_id` **唯一**，两者结果通常一样。

但如果：

```text
vip_users
100
100
102
```

`INNER JOIN` 会产生：

```text
order 1 / 100
order 1 / 100
order 3 / 102
```

而 Semi Join 仍然只返回：

```text
order 1 / 100
order 3 / 102
```

因为它只关心：

```text
EXISTS ?  → YES
```

而不关心右表到底有几条匹配记录。

### 反半连接（Anti Join）

与 Semi Join 对应的是 **Anti Join**：

> 找出左表中**不存在**匹配记录的行。

SQL 通常写：

```sql
SELECT *
FROM orders o
WHERE NOT EXISTS (
    SELECT 1
    FROM vip_users v
    WHERE v.user_id = o.user_id
);
```

所以可以记成：

```text
Semi Join      → EXISTS
Anti Join      → NOT EXISTS
```

这两个概念在数据库执行计划里也很常见，例如 MySQL / PostgreSQL 优化器可能会把 `EXISTS` 子查询转换成 **Semi Join** 执行。
