这是一个**非常实战型**的问题。WebSocket 在行情系统里**能不能跑得住**，完全取决于设计方式——用对了是“能用”，用错了就是“延迟炸弹”。

我按 **架构 → 并发模型 → 数据结构 → 推送策略 → 性能优化 → 常见坑** 的顺序来讲，直接给你一套可上线方案。

## **一、先给结论（避免走弯路）**

> **WebSocket 只负责“最后一跳广播”  
> 不参与行情计算、不参与顺序控制、不参与存储**

它的定位是：

- fan-out

- session 管理

- 网络 IO

**不是**行情引擎。

## **二、整体架构（推荐形态）**

行情核心（内存 / TCP / UDP）

│

▼

WS Push Gateway ←—— 只干推送

│

▼

WebSocket Clients

### **关键原则**

- WebSocket 层 **无状态（或弱状态）**

- 可水平扩展

- 随时可重启

## **三、并发模型（成败关键）**

### **❌ 错误模型（非常常见）**

- 一个连接一个线程

- 推送时直接 send()

- 行情线程直接写 socket

→ **必死**

### **✅ 正确模型：Event Loop + Channel**

N 个 IO 线程（EventLoop）

├─ 负责 WS 连接

├─ 负责编码

└─ 负责发送

行情线程

└─ 只往无锁队列写

**要点**

- 行情线程永不阻塞

- IO 线程只做 IO

- 线程间用 lock-free queue

## **四、连接与订阅模型设计**

### **1️⃣ 连接结构**

class WsSession {

int sessionId;

SendQueue queue;

SubscriptionSet subs;

long lastActiveTs;

}

- 每个 session 一个发送队列

- 严格限长（非常重要）

### **2️⃣ 订阅表（广播效率的核心）**

#### **双向索引**

instrument → sessions\[\]

session → instruments\[\]

- instrument 推送是 O(订阅者数)

- 不全量扫描

#### **优化点**

- instrumentId 用 int

- sessions 用 array / bitmap / int list

- 不用 Map\<String, List\>

## **五、推送模型（别把消息直接发给客户端）**

### **1️⃣ 行情进入 WS 的方式**

行情线程

→ fanout

→ enqueue(session.queue, message)

### **2️⃣ IO 线程发送**

EventLoop tick:

for session in activeSessions:

while session.queue not empty:

socket.write(frame)

**绝对禁止**

- 在行情线程调用 send

- 在 WS 回调里做计算

## **六、消息格式设计（影响 50% 性能）**

### **❌ 不推荐**

- JSON

- 文本字段

- 重复字段名

### **✅ 推荐**

- 二进制

- schema 固定

- 数字编码

\| type \| instrumentId \| ts \| px \| qty \| flags \|

如果一定要 JSON：

- 预生成模板

- 字段名极短

- 不做 stringify on hot path

## **七、Backpressure（WS 必须“冷酷无情”）**

### **核心规则**

> **慢客户端 = 风险源**

### **每个 session 必须有：**

- 发送队列最大长度

- 阈值策略

#### **队列满了怎么办？**

1.  丢增量

2.  只保留最新一条

3.  强制下发 snapshot

4.  直接断开

**行情系统里：断开是合理选择**

## **八、广播优化技巧（高并发必备）**

### **1️⃣ 批量推送**

- 同 instrument 的多条行情合并

- 一帧多个 message

### **2️⃣ 写合并**

- gather write

- 减少 syscall

### **3️⃣ 订阅分组**

- 相同订阅组合 → 共享编码结果

- 减少序列化次数

## **九、延迟与资源优化 checklist**

### **网络层**

- TCP_NODELAY

- SO_SNDBUF 调大

- 禁用压缩（压缩 = 延迟）

### **应用层**

- 对象池

- ByteBuffer 复用

- cache line padding

### **JVM（如果用 Java）**

- ZGC / Shenandoah

- off-heap buffer

- Netty 原生 epoll

## **十、可扩展性设计（多节点）**

### **WS 集群模型**

LB

├─ WS-1

├─ WS-2

└─ WS-3

#### **要点**

- session 粘性（instrument 粘性不需要）

- 行情源 → 广播给所有 WS 节点

- WS 之间 **不通信**

## **十一、常见致命坑（血泪总结）**

❌ 用 Redis Pub/Sub 推 WS  
❌ 用 Kafka 直连 WS  
❌ 所有客户端一个广播 channel  
❌ 客户端断线不清理订阅  
❌ 在 WS 层做行情聚合

## **十二、一句话总结（可以当面试答案）**

> **高效的 WebSocket 行情广播 =  
> EventLoop IO + 无锁队列 + 严格背压 + 二进制协议 + 只做最后一跳**

如果你愿意，下一步我可以：

- 给你一个 **Netty WS 推送线程模型示例**

- 对比 **WebSocket vs TCP 私有协议**

- 讲 **如何从 WS 平滑升级到 TCP / UDP**

- 或设计 **百万连接 WS 集群**

你想往哪一层继续深挖？
