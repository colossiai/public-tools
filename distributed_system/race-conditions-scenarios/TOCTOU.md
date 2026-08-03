# TOCTOU

**TOCTOU** = **Time-of-Check to Time-of-Use**，中文通常叫 **“检查时刻到使用时刻”**，是一种典型的**竞态条件（Race Condition）**。

核心问题：

> **你检查的状态，在真正使用之前被别人改变了。**

### 经典例子：文件权限

```text
1. Check: 这个文件可以写吗？
           ↓
2.        ← 攻击者在这里替换文件
           ↓
3. Use:   打开文件并写入
```

代码逻辑可能类似：

```c
if (access("/tmp/file", W_OK) == 0) {
    // 这里以为 file 是安全可写的
    open("/tmp/file", O_WRONLY);
}
```

问题是 `access()` 检查和 `open()` 使用之间存在时间窗口。攻击者可以在这期间把 `file` 替换成另一个文件，例如通过 **symbolic link**，导致程序最终操作了错误的目标。MITRE 将这种问题归类为 CWE-367。([Common Weakness Enumeration][1])

### 用一句话理解

```text
Check → [状态可能发生变化] → Use
```

如果：

```text
Check 的结果 ≠ Use 时刻的真实状态
```

就可能产生 TOCTOU。

### 常见解决方案

* **Atomic operation**：把 check + use 合并成一个原子操作
* **Lock**：检查和使用期间加锁
* **避免先检查再操作**：直接执行操作，根据操作结果判断是否允许
* **Transaction / CAS**：数据库或并发场景使用事务、乐观锁、Compare-And-Swap
* **使用安全的 OS API**：避免 `access()` → `open()` 这种分离操作

例如数据库中：

```sql
-- ❌ TOCTOU 风险
SELECT balance FROM account WHERE id = 1;
-- 应用层判断 balance >= 100
UPDATE account SET balance = balance - 100 WHERE id = 1;
```

多个请求并发时，`SELECT` 和 `UPDATE` 之间状态可能变化。

更安全的方式：

```sql
-- ✅ check + use 合并
UPDATE account
SET balance = balance - 100
WHERE id = 1
  AND balance >= 100;
```

然后检查 `affected rows == 1`。

**所以你可以把 TOCTOU 理解成：**

> **“我检查的时候是这样，但我真正使用的时候已经不是这样了。”**

它本质上是 **Race Condition 的一种特殊形式**，重点在于 **Check 和 Use 之间存在状态变化窗口**。

[1]: https://cwe.mitre.org/data/definitions/367.html?utm_source=chatgpt.com "CWE - CWE-367: Time-of-check Time-of-use (TOCTOU) Race Condition (4.20)"
