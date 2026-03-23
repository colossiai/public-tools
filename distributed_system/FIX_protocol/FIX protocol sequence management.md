# #Show Detail FIX protocol sequence management

In the **Financial Information eXchange (FIX) Protocol**, **sequence management** is critical to guarantee **exactly-once message ordering and recovery** between trading counterparties.
Every FIX session is **stateful** and uses **monotonic sequence numbers** to detect message loss.

Below is a **detailed breakdown of how FIX sequence management works in production trading systems.**

---

# 1. Core Concept: Sequence Numbers

Every FIX message contains:

* **34=MsgSeqNum** → Message sequence number
* **49=SenderCompID**
* **56=TargetCompID**
* **52=SendingTime**

Example:

```
8=FIX.4.4
9=112
35=D
34=215
49=BUY_SIDE
56=BROKER
52=20260323-05:10:22.123
...
10=128
```

Key rules:

| Rule                                        | Meaning               |
| ------------------------------------------- | --------------------- |
| Each side maintains **two counters**        | incoming and outgoing |
| Sequence starts at **1 after logon**        |                       |
| Each message increments by **+1**           |                       |
| Missing numbers trigger **resend recovery** |                       |

---

# 2. Normal Message Flow

Example session:

```
Client                    Exchange
---------------------------------------
Logon (34=1)   --------->
                <--------- Logon (34=1)

NewOrder (34=2) --------->
                <--------- ExecutionReport (34=2)

Cancel (34=3)  --------->
                <--------- CancelAck (34=3)
```

Both sides maintain:

```
expected incoming seq = last_received + 1
```

---

# 3. Detecting a Gap

If a sequence number is skipped:

Example:

```
Client sends:

34=10
34=11
34=12
```

But the exchange receives:

```
34=10
34=12
```

Now the exchange detects:

```
expected = 11
received = 12
```

This triggers **Gap Detection**.

---

# 4. Resend Request

Exchange sends:

```
35=2 (ResendRequest)

7=BeginSeqNo
16=EndSeqNo
```

Example:

```
8=FIX.4.4
35=2
34=25
7=11
16=11
```

Meaning:

```
Please resend message 11
```

---

# 5. Sender Response (Replay)

The sender must **replay stored messages**.

Two cases exist.

---

## Case A — Resend the Original Message

```
34=11
43=Y (PossDupFlag)
122=OrigSendingTime
```

Example:

```
35=D
34=11
43=Y
122=20260323-05:10:01.333
```

Fields added:

| Tag  | Meaning               |
| ---- | --------------------- |
| 43=Y | Possible duplicate    |
| 122  | Original sending time |

---

## Case B — Skip Messages (Sequence Reset Gap Fill)

Sometimes messages **cannot be resent** (e.g. admin messages).

Then send:

```
35=4 (SequenceReset)
123=Y (GapFillFlag)
36=NewSeqNo
```

Example:

```
35=4
123=Y
34=11
36=12
```

Meaning:

```
Skip message 11
Next message will be 12
```

---

# 6. Complete Gap Recovery Example

### Step 1 — Exchange detects gap

```
Received:
34=8
34=9
34=11   <-- gap
```

Expected:

```
10
```

---

### Step 2 — Resend Request

Exchange sends:

```
35=2
7=10
16=10
```

---

### Step 3 — Sender replay

Client sends:

```
34=10
43=Y
122=origTime
```

---

### Step 4 — Session continues

```
34=11
34=12
```

---

# 7. Sequence Reset (Hard Reset)

Sometimes a session must **reset sequence numbers**.

Example:

```
35=4
36=1
```

Meaning:

```
Reset sequence to 1
```

This usually happens during:

* **End-of-day resets**
* **disaster recovery**
* **session restart**

---

# 8. Logon Sequence Negotiation

During **Logon (35=A)**:

```
141=Y
```

means:

```
ResetSeqNumFlag = YES
```

Example:

```
35=A
34=1
141=Y
```

Meaning:

```
Both sides reset sequence numbers to 1
```

---

# 9. Production FIX Engine Requirements

A real FIX engine must implement:

### Persistent Message Store

Every message must be written to disk:

```
seq → raw FIX message
```

Used for replay.

Example DB:

```
1 -> logon
2 -> new order
3 -> cancel
```

Popular implementations:

* QuickFIX
* QuickFIX/J
* OnixS FIX Engine

---

### Replay Engine

Must support:

```
load messages
stream resend
mark possDup
```

---

### Gap Handling

Edge cases:

```
overlapping resend requests
large replay windows
infinite resend loops
```

---

# 10. High-Performance FIX Systems

Low-latency trading firms often optimize sequence management:

Example architecture:

```
NIC
 ↓
Kernel bypass (Solarflare / DPDK)
 ↓
TCP session
 ↓
FIX parser
 ↓
Sequence manager
 ↓
Order router
```

Sequence manager responsibilities:

```
- track incoming seq
- track outgoing seq
- detect gap
- issue resend request
- replay message store
```

Typical latency budget:

```
FIX decode:     200ns
seq check:      20ns
routing:        500ns
```

---

# 11. Common Failure Scenarios

### Network Packet Loss

```
seq: 100
seq: 102
```

→ resend request

---

### Session Restart

```
client restart
seq mismatch
```

→ resend entire history

---

### Large Gap

Example:

```
missing 10,000 messages
```

→ replay storm

Real exchanges may:

```
force session logout
```

---

# 12. Simplified FIX Sequence Manager Pseudocode

```cpp
void onMessage(msg) {
    if (msg.seq == expected) {
        process(msg);
        expected++;
    }
    else if (msg.seq > expected) {
        sendResendRequest(expected, msg.seq - 1);
    }
    else {
        // duplicate
        ignore();
    }
}
```

---

# 13. Real-World Message Volume

Large brokers handle:

```
1M+ FIX messages/sec
```

Which is why:

* FIX engines must be **lock-free**
* sequence tracking must be **O(1)**

---

✅ **Summary**

FIX sequence management guarantees:

```
1. ordered delivery
2. message loss detection
3. deterministic recovery
4. session reliability
```

Core mechanisms:

```
MsgSeqNum (34)
ResendRequest (35=2)
SequenceReset (35=4)
PossDupFlag (43)
```

---

If you'd like, I can also show:

1️⃣ **How FIX sequence management is implemented inside a real FIX engine (QuickFIX internal architecture)**
2️⃣ **How HFT firms bypass classic FIX engines for ultra-low latency**
3️⃣ **A production-grade FIX session state machine diagram** (used by exchanges).
