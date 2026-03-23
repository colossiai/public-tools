# #Why crack() not used in fromAdmin()

In **QuickFIX/J**, `crack()` is designed **only for application-level messages**, not **session/admin messages**. The reason comes from how the **Financial Information eXchange protocol** separates message responsibilities.

---

# 1. Two message categories in FIX

FIX defines two fundamentally different message groups:

### 1️⃣ Session (Admin) messages

These manage the **FIX connection itself**.

Examples:

| MsgType | Message       |
| ------- | ------------- |
| A       | Logon         |
| 5       | Logout        |
| 0       | Heartbeat     |
| 1       | TestRequest   |
| 2       | ResendRequest |
| 4       | SequenceReset |

These control:

* session lifecycle
* heartbeat
* sequence numbers
* recovery/resend

---

### 2️⃣ Application messages

These carry **business trading data**.

Examples:

| MsgType | Message                   |
| ------- | ------------------------- |
| D       | NewOrderSingle            |
| 8       | ExecutionReport           |
| F       | OrderCancelRequest        |
| G       | OrderCancelReplaceRequest |
| W       | MarketDataSnapshot        |

These are **routed to business logic**.

---

# 2. How QuickFIX/J routes messages

QuickFIX/J already **separates the two layers before your code runs**.

Internal flow:

```
TCP
  │
  ▼
FIX Session
  │
  ├── Admin messages → fromAdmin()
  │
  └── App messages   → fromApp()
```

So by the time your code receives a message:

* `fromAdmin()` → only admin messages
* `fromApp()` → only application messages

---

# 3. Why `crack()` exists only for application messages

`MessageCracker` was designed to dispatch **business messages**:

```java
onMessage(NewOrderSingle msg, SessionID sessionID)
onMessage(ExecutionReport msg, SessionID sessionID)
onMessage(OrderCancelRequest msg, SessionID sessionID)
```

These handlers correspond to **application FIX messages only**.

Admin messages **do not follow this pattern**.

Instead, they are handled directly.

Example:

```java
public void fromAdmin(Message message, SessionID sessionID)
        throws FieldNotFound {

    String msgType = message.getHeader().getString(MsgType.FIELD);

    if (msgType.equals(MsgType.LOGON)) {
        System.out.println("Logon received");
    }
}
```

---

# 4. Another important reason: session safety

Admin messages affect **protocol state**.

Examples:

### ResendRequest

```
35=2
```

If mishandled you can break:

* sequence numbers
* gap fill
* recovery

### SequenceReset

```
35=4
```

If routed incorrectly you can corrupt the session.

So **QuickFIX handles most admin logic internally** inside the FIX engine.

Your application usually only **observes or validates** them.

---

# 5. Why `MessageCracker` is not used

Technically QuickFIX *could* support:

```java
onMessage(Logon msg)
onMessage(Heartbeat msg)
```

But it intentionally doesn't because:

1️⃣ Admin messages belong to the **FIX engine layer**
2️⃣ Application code **should not control session protocol**
3️⃣ It simplifies the API design

---

# 6. What professionals actually do

Typical real-world implementation:

```java
public void fromAdmin(Message message, SessionID sessionID)
        throws FieldNotFound {

    MsgType msgType = new MsgType();
    message.getHeader().getField(msgType);

    if (msgType.valueEquals(MsgType.LOGON)) {
        System.out.println("Logon received");
    }
}
```

Used for:

* authentication
* session monitoring
* logging

NOT business logic.

---

# 7. Summary

| Method        | Message Type              | Purpose                         |
| ------------- | ------------------------- | ------------------------------- |
| `fromAdmin()` | FIX session messages      | connection management           |
| `fromApp()`   | trading/business messages | business logic                  |
| `crack()`     | application messages only | route to `onMessage()` handlers |

So:

```
fromApp()
   └─ crack() → onMessage(...)
```

but

```
fromAdmin()
   └─ manual handling
```

---

✅ **Key idea**

`crack()` is not used in `fromAdmin()` because **admin messages belong to the FIX session protocol layer, not the application message layer that `MessageCracker` was designed to dispatch.**

---

If you're building a **serious FIX engine / trading gateway**, I can also show you something very useful:

**The real FIX message flow used in trading systems (with sequence recovery, resend logic, and message queues).**

It explains why **FIX engines internally have a 3-layer architecture** used by trading firms.
