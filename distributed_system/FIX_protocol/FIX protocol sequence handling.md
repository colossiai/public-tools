# #To build a FIX protocol client, how to properly handle sequence resend/reset and other cases?

When building a **production-grade FIX Protocol client**, handling **sequence numbers, resend, and reset** correctly is critical.
Most connectivity failures between brokers and trading systems come from **incorrect sequence management**.

Below is the **practical design used in real trading systems** (banks, exchanges, HFT gateways).

---

# 1. Core FIX Sequence Rules

Each session has **two independent sequences**:

| Direction | Field            | Meaning                           |
| --------- | ---------------- | --------------------------------- |
| Outgoing  | `MsgSeqNum (34)` | Increment every message you send  |
| Incoming  | `MsgSeqNum (34)` | Must be exactly expected sequence |

The session maintains:

```
nextOutgoingSeq
nextExpectedIncomingSeq
```

Example

```
Client -> Broker   MsgSeqNum=1
Client -> Broker   MsgSeqNum=2
Broker -> Client   MsgSeqNum=1
Broker -> Client   MsgSeqNum=2
```

---

# 2. Core Message Types for Sequence Control

Important session messages:

| MsgType | Name          | Purpose                  |
| ------- | ------------- | ------------------------ |
| 0       | Heartbeat     | keep connection alive    |
| 1       | TestRequest   | check if peer alive      |
| 2       | ResendRequest | request missing messages |
| 3       | Reject        | message error            |
| 4       | SequenceReset | reset or gap fill        |
| 5       | Logout        | session end              |
| A       | Logon         | start session            |

---

# 3. Handling Incoming Sequence Numbers

When receiving a message:

```
incomingSeq = msg.MsgSeqNum
expectedSeq = nextExpectedIncomingSeq
```

### Case 1 — Normal

```
incomingSeq == expectedSeq
```

Accept message.

```
nextExpectedIncomingSeq++
```

---

### Case 2 — Message Missing

```
incomingSeq > expectedSeq
```

Example

```
Expected: 10
Received: 15
```

Messages **10–14 missing**

Send:

```
ResendRequest
BeginSeqNo = 10
EndSeqNo   = 0 (infinite)
```

Then:

```
queue message 15
```

Wait for resend.

---

### Case 3 — Duplicate Message

```
incomingSeq < expectedSeq
```

Check flag:

```
PossDupFlag (43) = Y
```

If **duplicate**

```
ignore message
```

If **not duplicate**

```
send Reject
```

---

# 4. Handling ResendRequest

When peer sends:

```
ResendRequest
BeginSeqNo
EndSeqNo
```

You must resend stored messages.

### Proper implementation

```
for seq in range(begin, end):
    msg = messageStore.get(seq)

    if msg is admin:
        resend(msg)
    else:
        send GapFill
```

Why?

Trading systems often **do not resend application messages** (orders) to avoid duplicate business logic.

Instead they send:

```
SequenceReset
GapFillFlag=Y
NewSeqNo=X
```

---

# 5. Gap Fill (Most Important)

Example:

Missing messages:

```
5 6 7 8
```

Send:

```
MsgType=4 (SequenceReset)
GapFillFlag=Y
MsgSeqNum=5
NewSeqNo=9
```

Meaning:

```
skip 5-8
next expected = 9
```

---

# 6. Sequence Reset (Hard Reset)

Two types exist.

### Gap Fill (normal)

```
GapFillFlag=Y
```

Just skipping messages.

---

### Hard Reset

```
GapFillFlag=N
```

Example:

```
MsgSeqNum=10
NewSeqNo=1
```

Used when:

* manual session reset
* disaster recovery

Many exchanges **do not allow this intraday**.

---

# 7. Logon Sequence Handling

On logon:

Fields:

```
34 = MsgSeqNum
141 = ResetSeqNumFlag
```

Cases:

---

### Normal reconnect

```
ResetSeqNumFlag=N
```

Continue previous sequences.

---

### Full reset

```
ResetSeqNumFlag=Y
```

Both sides reset to:

```
MsgSeqNum=1
```

---

# 8. Message Persistence (Critical)

A real FIX client must store messages.

Typical design:

```
+--------------------+
| FIX Session        |
| nextOutSeq         |
| nextInSeq          |
+--------------------+
         |
         v
+--------------------+
| Message Store      |
| seq -> raw message |
+--------------------+
         |
         v
Disk / DB
```

Example implementations:

* file store
* embedded DB
* memory + WAL

---

# 9. Handling PossDupFlag

When resending messages:

```
43=Y (PossDupFlag)
122=OrigSendingTime
```

Example:

```
35=D
34=10
43=Y
122=20260323-07:00:00
```

This prevents duplicate order execution.

---

# 10. Handling Heartbeat Timeout

Session logic:

```
HeartbeatInterval = 30
```

Rules:

| Condition          | Action           |
| ------------------ | ---------------- |
| no message for 30s | send Heartbeat   |
| no response        | send TestRequest |
| still no response  | disconnect       |

---

# 11. Production FIX Client Architecture

Real systems separate layers:

```
+-------------------------+
| Order Engine            |
+-------------------------+
            |
+-------------------------+
| FIX Application Layer   |
| order routing           |
+-------------------------+
            |
+-------------------------+
| FIX Session Layer       |
| seq / resend / hb       |
+-------------------------+
            |
+-------------------------+
| TCP / TLS               |
+-------------------------+
```

---

# 12. Minimal Sequence Engine Pseudocode

```go
func onMessage(msg FIXMessage) {

    seq := msg.SeqNum

    if seq == expectedSeq {
        process(msg)
        expectedSeq++
        return
    }

    if seq > expectedSeq {
        sendResendRequest(expectedSeq, 0)
        queue(msg)
        return
    }

    if seq < expectedSeq {
        if msg.PossDupFlag {
            return
        }
        reject(msg)
    }
}
```

---

# 13. Common Production Bugs

Most FIX engines fail because of:

### 1️⃣ Not persisting messages

Breaks resend.

---

### 2️⃣ Incorrect gap fill logic

Can cause **infinite resend loops**.

---

### 3️⃣ Wrong PossDup handling

Can cause **duplicate orders**.

---

### 4️⃣ ResetSeqNum misuse

Can break sessions with brokers.

---

# 14. Real FIX Engines to Study

Production implementations:

* QuickFIX
* QuickFIX/J
* Fix8
* OnixS FIX Engine

These engines contain **battle-tested resend logic**.

---

💡 **Reality in trading systems**

At high performance firms:

* FIX is **only edge connectivity**
* internally they use:

  * binary protocols
  * shared memory
  * Aeron

FIX latency is usually **milliseconds**, not microseconds.

---

✅ If you want, I can also show:

* **The full FIX session state machine used by exchanges**
* **The exact resend algorithm used in production FIX engines**
* **How HFT firms build ultra-low latency FIX gateways** (much more interesting).
