# 支付的先冻结再扣款，属于2阶段提交吗


严格来说，**支付中的"先冻结（预授权）再扣款（Capture）"和数据库里的两阶段提交（2PC）不是同一个概念**，但它们的思想非常相似：**都是把"提交"拆成两个阶段，以降低失败带来的风险。**

## 两者对比

| 支付流程            | 数据库 2PC  |
| --------------- | -------- |
| 冻结（Authorize）   | Prepare  |
| 扣款（Capture）     | Commit   |
| 解冻（Void/Cancel） | Rollback |

可以看到：

```
支付:
    Authorize
        ↓
    Capture
        ↓
     完成支付

或者

    Authorize
        ↓
      Void
        ↓
      资金释放
```

对应数据库：

```
Prepare
    ↓
Commit

或者

Prepare
    ↓
Rollback
```

所以很多人会说：

> **支付预授权就是现实世界里的 Prepare。**

---

## 为什么支付要这样设计？

假设你买酒店：

1. 酒店先确认有房
2. 信用卡冻结 1000 美元
3. 酒店真正入住时才扣款

如果直接扣：

```
扣款
 ↓
酒店没房
 ↓
退款
```

退款可能需要几天。

如果先冻结：

```
冻结1000
 ↓
酒店确认
 ↓
扣款
```

失败：

```
冻结1000
 ↓
酒店没房
 ↓
解冻
```

用户的钱没有真正离开账户。

---

## 为什么它又不是真正的 2PC？

真正的数据库 2PC 有几个特点：

1. 所有参与者必须同时进入 Prepare
2. Coordinator 统一决定 Commit
3. Commit 后不可撤销
4. 所有参与者保证最终一致

例如：

```
DB1 Prepare OK
DB2 Prepare OK

Coordinator:
Commit

DB1 Commit
DB2 Commit
```

而支付：

```
银行 Freeze OK

......
几个小时以后

商户决定 Capture
```

这里：

* 两个阶段可能间隔几小时甚至几天
* 中间允许人工审核
* Capture 甚至可以部分扣款
* Freeze 会自动过期

因此它不是严格意义上的 2PC。

---

## 更准确地说，它属于什么？

支付系统通常称为：

* **Authorization + Capture（预授权 + 扣款）**
* **Reservation Pattern（资源预留模式）**
* **Try-Confirm/Cancel（TCC）模式**（分布式事务中的一种）

其实它和 **TCC** 更接近。

例如：

```
Try
    冻结余额

Confirm
    真正扣钱

Cancel
    解冻余额
```

对应支付：

```
Authorize
    ↓
Capture
    ↓
完成

Authorize
    ↓
Void
    ↓
取消
```

所以很多分布式事务框架（如 Seata TCC）就是借鉴了支付系统的思想。

---

## 一个电商的完整例子

下单时：

```
库存：
    Try
    锁库存

余额：
    Try
    冻结余额
```

全部成功：

```
库存 Confirm
余额 Confirm
```

如果失败：

```
库存 Cancel
余额 Cancel
```

这就是 TCC。

而如果使用信用卡支付：

```
银行：
Authorize（冻结额度）

商户：
等待发货

发货后：
Capture（扣款）

如果取消订单：
Void（释放额度）
```

可以发现，这个流程几乎就是 TCC 在金融支付中的体现。

## 总结

* **不是严格意义上的数据库 2PC**，因为没有统一协调器驱动所有参与者同步完成 Prepare 和 Commit，也不具备 2PC 的阻塞和原子性语义。
* **思想上非常接近 2PC**：先确保资源可用，再决定是否最终提交。
* **从分布式系统的角度看，更接近 TCC（Try-Confirm-Cancel）或资源预留（Reservation）模式**：

  * **Try** → 冻结资金（Authorize）
  * **Confirm** → 扣款（Capture）
  * **Cancel** → 解冻（Void）

因此，在设计支付、库存、优惠券等需要"先占资源、后确认"的业务时，TCC 往往比数据库 2PC 更符合实际业务需求，因为它允许较长时间的业务处理、支持业务补偿，并且不要求所有参与方长期持有事务锁。
