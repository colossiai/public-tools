# Show The full FIX protocol session state machine used by exchanges

The **Financial Information eXchange (FIX) Protocol session layer** defines a strict **state machine** to manage connectivity, sequencing, and recovery between counterparties (buy-side ↔ sell-side or client ↔ exchange).

Real exchanges (e.g., Nasdaq, CME Group, Intercontinental Exchange) implement a variation of this session state machine.

Below is the **full production-grade FIX session state machine** used in most trading systems.

---

# FIX Session State Machine

```
               +-------------------+
               |      DISCONNECTED |
               +-------------------+
                         |
                         | TCP Connect
                         v
               +-------------------+
               |   TCP CONNECTED   |
               +-------------------+
                         |
                         | Send Logon (35=A)
                         v
               +-------------------+
               |   LOGON SENT      |
               +-------------------+
                         |
        +----------------+----------------+
        |                                 |
Receive Logon                      Logon Reject /
(35=A)                              Timeout
        |                                 |
        v                                 v
+-------------------+            +-------------------+
|   ESTABLISHED     |<-----------|   DISCONNECTED    |
| (SESSION ACTIVE)  |            +-------------------+
+-------------------+
        |
        | Heartbeats / Application Messages
        |
        +--------------------------------------------------+
        |                                                  |
        v                                                  v
+-------------------+                          +--------------------+
|   RESEND REQUEST  |                          |   TEST REQUEST     |
| (35=2 received)   |                          | (35=1 sent)        |
+-------------------+                          +--------------------+
        |                                                  |
        v                                                  v
Send Sequence Reset / Gap Fill                    Receive Heartbeat
(35=4)                                            (35=0)
        |                                                  |
        +----------------------+---------------------------+
                               |
                               v
                     +-------------------+
                     |   ESTABLISHED     |
                     +-------------------+

        |
        | Logout (35=5)
        v

+-------------------+
| LOGOUT PENDING    |
+-------------------+
        |
Receive Logout
        |
        v
+-------------------+
| DISCONNECTED      |
+-------------------+
```

---

# Core FIX Session States

### 1️⃣ DISCONNECTED

No TCP connection exists.

Possible transitions:

```
DISCONNECTED → TCP CONNECTED
```

Triggers:

* Initiator opens TCP socket
* Acceptor listens for connections

---

### 2️⃣ TCP CONNECTED

Transport layer connected, but FIX session not established.

Expected message:

```
Logon (35=A)
```

If not received:

```
timeout → disconnect
```

---

### 3️⃣ LOGON SENT

Initiator sent:

```
35=A Logon
```

Contains:

```
98=0      (Encryption)
108=30    (Heartbeat interval)
553=user
554=password
34=1      (Sequence number)
```

Possible outcomes:

```
Receive Logon → ESTABLISHED
Reject / timeout → DISCONNECTED
```

---

### 4️⃣ ESTABLISHED (SESSION ACTIVE)

Normal trading state.

Allowed messages:

```
Application:
35=D NewOrderSingle
35=F OrderCancel
35=G CancelReplace
35=8 ExecutionReport

Session:
35=0 Heartbeat
35=1 TestRequest
35=2 ResendRequest
35=4 SequenceReset
35=5 Logout
```

Heartbeat loop:

```
HeartbeatInterval = 30 sec

If no message received:
    send TestRequest
```

---

# Heartbeat / Liveness Flow

```
Client                     Exchange

--- idle ---

Client -> TestRequest (35=1)

Exchange -> Heartbeat (35=0)
112=<TestReqID>
```

If still silent:

```
disconnect session
```

---

# Sequence Recovery (Critical for Exchanges)

FIX is **strictly ordered**.

Example:

```
Expected Seq = 105
Received Seq = 110
```

Client sends:

```
ResendRequest
35=2
7=105
16=109
```

Exchange replies with:

```
Resent messages
OR

SequenceReset (GapFill)
35=4
```

Example GapFill:

```
35=4
123=Y
36=110
```

Meaning:

```
skip messages 105–109
next seq = 110
```

---

# Logout State

Logout flow:

```
Client -> Logout (35=5)
Exchange -> Logout (35=5)
TCP close
```

State:

```
ESTABLISHED → LOGOUT_PENDING → DISCONNECTED
```

---

# Edge Cases Real Exchanges Handle

Production FIX engines must handle many abnormal states.

### 1️⃣ Sequence Too Low

Example:

```
Expected: 100
Received: 95
```

Action:

```
Logout
Session rejected
```

Reason:

```
PossDup / replay attack risk
```

---

### 2️⃣ Sequence Too High

Example:

```
Expected: 100
Received: 105
```

Action:

```
Send ResendRequest
```

---

### 3️⃣ Duplicate Messages

Handled using:

```
43=Y (PossDupFlag)
122=OrigSendingTime
```

---

### 4️⃣ TCP Drop

Common in trading networks.

Recovery:

```
Reconnect
Send Logon with ResetSeqNumFlag
```

or

```
Resume sequence numbers
```

---

# Real Production FIX Engine Internal State Machine

Most engines (e.g., QuickFIX, QuickFIX/J) internally implement something like:

```
STATE_START
STATE_SOCKET_CONNECTED
STATE_LOGON_SENT
STATE_LOGON_RECEIVED
STATE_ACTIVE
STATE_RESEND
STATE_TEST_REQUEST
STATE_LOGOUT_SENT
STATE_LOGOUT_RECEIVED
STATE_DISCONNECTED
```

---

# Production Exchange Extensions

Large exchanges extend FIX session logic with:

### Cancel-on-disconnect

```
Disconnect → cancel all open orders
```

Example exchanges:

* Nasdaq
* Cboe Global Markets

---

### Drop Copy Sessions

Separate FIX session for fills:

```
ExecutionReports only
```

---

### Throttling

Session layer checks:

```
messages / second
```

Too fast:

```
Logout
```

---

# Full Message Flow Example (Real Trading Session)

```
TCP Connect

C → E  Logon (34=1)
E → C  Logon (34=1)

C → E  NewOrderSingle (34=2)
E → C  ExecutionReport Ack (34=2)

C → E  NewOrderSingle (34=3)
E → C  ExecutionReport Fill (34=3)

--- network drop ---

Reconnect

C → E  Logon (34=4)
E → C  ResendRequest (7=3,16=0)

C → E  resend msg 3
```

---

# What HFT Firms Actually Optimize

The FIX session layer becomes a **major latency bottleneck**.

HFT firms:

* bypass FIX internally
* convert FIX → binary protocol
* use multicast for market data

Examples:

* Citadel
* Jump Trading
* DRW Trading Group

---

# If you're building a FIX engine

You must implement:

### 8 critical components

```
1. TCP connection manager
2. FIX parser
3. Session state machine
4. Sequence number manager
5. Resend / gap fill logic
6. Heartbeat watchdog
7. Message persistence store
8. Application message router
```

---

If you'd like, I can also show:

* **The real QuickFIX session.cpp state machine walkthrough** (very educational)
* **The ultra-low-latency FIX engine architecture used by HFT firms**
* **How exchanges implement FIX gateways internally (Nasdaq / CME architecture)**.
