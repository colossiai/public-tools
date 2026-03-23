# #The real QuickFIX session.cpp state machine walkthrough


The **QuickFIX session engine** is driven by a fairly strict **session state machine** implemented mainly in **`Session.cpp`** and **`SessionState.h`**.
Understanding it is critical if you want to build a **real FIX client or exchange gateway**.

Below is a **realistic walkthrough of the QuickFIX session state machine**, focusing on what actually happens inside **`Session::next()`**, which processes every incoming/outgoing message.

---

# 1. Core QuickFIX Session State

Inside QuickFIX there is a **SessionState** object that stores the runtime session status.

Important fields:

| Field                 | Meaning                            |
| --------------------- | ---------------------------------- |
| `logonSent`           | client sent Logon                  |
| `logonReceived`       | counterparty sent Logon            |
| `logoutSent`          | logout initiated                   |
| `logoutReceived`      | logout received                    |
| `resetReceived`       | sequence reset happened            |
| `heartbeatInterval`   | heartbeat interval                 |
| `testRequestCounter`  | number of unanswered test requests |
| `nextSenderMsgSeqNum` | outgoing sequence                  |
| `nextTargetMsgSeqNum` | incoming sequence                  |

Conceptually the state is:

```
DISCONNECTED
      |
      v
LOGON_SENT
      |
      v
LOGGED_ON
      |
      v
LOGOUT
      |
      v
DISCONNECTED
```

But the **real QuickFIX logic is message-driven**, not pure FSM.

---

# 2. The Heart: Session::next()

Every received message enters:

```
Session::next(const Message& message)
```

High level flow:

```
receive message
     |
     v
verify header
     |
     v
check sequence number
     |
     +---- gap -> ResendRequest
     |
     v
dispatch by MsgType
```

Pseudocode equivalent:

```
void Session::next(Message msg)
{
    verifyCompIDs(msg);
    verifySendingTime(msg);

    if (!validSeqNum(msg))
        handleSeqNumMismatch();

    switch(msgType)
    {
        case LOGON:
            nextLogon();
        case HEARTBEAT:
            nextHeartbeat();
        case TEST_REQUEST:
            nextTestRequest();
        case RESEND_REQUEST:
            nextResendRequest();
        case SEQUENCE_RESET:
            nextSequenceReset();
        case LOGOUT:
            nextLogout();
        default:
            nextApplicationMessage();
    }
}
```

---

# 3. Logon Flow (Very Important)

### Initiator (client)

```
connect TCP
     |
     v
send Logon
     |
     v
wait for Logon response
```

### Acceptor (server)

```
receive Logon
     |
validate
     |
send Logon
```

QuickFIX implementation:

```
Session::nextLogon()
```

Key operations:

```
if (!state.logonReceived)
{
    state.logonReceived = true
}

if (initiator && !state.logonSent)
{
    sendLogon()
}

if (logonSent && logonReceived)
{
    state.loggedOn = true
}
```

After success:

```
Application::onLogon(sessionID)
```

---

# 4. Sequence Number Handling

One of the **most critical parts** of FIX.

When message arrives:

```
incomingSeqNum = msg.getSeqNum()
expectedSeqNum = state.nextTargetMsgSeqNum
```

### Case 1 — Correct

```
incoming == expected
```

Process message normally.

Then:

```
state.nextTargetMsgSeqNum++
```

---

### Case 2 — Gap detected

```
incoming > expected
```

Example:

```
expected = 100
incoming = 105
```

QuickFIX does:

```
send ResendRequest
BeginSeqNo = 100
EndSeqNo = 0
```

Implementation:

```
generateResendRequest(expected, incoming-1)
```

---

### Case 3 — Duplicate message

```
incoming < expected
```

Check flag:

```
PossDupFlag=Y
```

If duplicate → ignore.

Otherwise → protocol error.

---

# 5. ResendRequest Processing

When counterparty asks for resend:

```
MsgType=2 (ResendRequest)
```

QuickFIX:

```
Session::nextResendRequest()
```

Flow:

```
for seq in BeginSeqNo..EndSeqNo
    if message exists in store
        resend message
    else
        send SequenceReset GapFill
```

Example resend:

```
35=4
123=Y
34=105
36=110
```

Meaning:

```
skip messages 105–109
```

---

# 6. SequenceReset Handling

Two modes exist.

### Gap Fill

```
35=4
123=Y
```

Meaning:

```
skip sequence numbers
```

QuickFIX logic:

```
if GapFillFlag=Y
    nextTargetSeqNum = NewSeqNo
```

---

### Hard Reset

```
123=N
```

Meaning:

```
force sequence number reset
```

QuickFIX:

```
state.nextTargetSeqNum = NewSeqNo
```

Usually only allowed during **logon**.

---

# 7. Heartbeat + Liveness Detection

FIX sessions must detect dead connections.

Timer logic:

```
heartbeatInterval = 30s
```

If no message received:

```
send TestRequest
```

Implementation:

```
Session::generateTestRequest()
```

Flow:

```
no message for heartbeat interval
        |
        v
send TestRequest
        |
        v
wait for Heartbeat(TestReqID)
```

If still nothing:

```
disconnect session
```

---

# 8. Logout Flow

Logout can start from either side.

```
send Logout
      |
      v
wait for Logout response
      |
      v
disconnect
```

QuickFIX:

```
Session::nextLogout()
```

Logic:

```
state.logoutReceived = true

if (!state.logoutSent)
    sendLogout()

disconnect()
```

---

# 9. Application Message Dispatch

Non-session messages are passed to the application.

```
Session::nextApplicationMessage()
```

Which calls:

```
Application::fromApp(message, sessionID)
```

Typical message types:

```
D  NewOrderSingle
8  ExecutionReport
F  OrderCancelRequest
```

QuickFIX ensures **sequence correctness first**, then dispatch.

---

# 10. Real Production Session Loop

The real runtime loop looks like:

```
TCP socket read
      |
      v
FIX message parsed
      |
      v
Session::next()
      |
      +--- session logic
      |
      +--- resend logic
      |
      +--- heartbeat logic
      |
      v
Application callbacks
```

---

# 11. The Real QuickFIX State Diagram

Simplified internal state transitions:

```
               TCP CONNECT
                    |
                    v
              SEND LOGON
                    |
                    v
           WAIT LOGON RESPONSE
                    |
             +------+------+
             |             |
             v             v
        LOGGED ON      DISCONNECT
             |
             v
        NORMAL FLOW
             |
     +-------+--------+
     |                |
 RESEND           HEARTBEAT
     |                |
     +-------+--------+
             |
             v
           LOGOUT
             |
             v
         DISCONNECT
```

---

# 12. The 5 Functions That Control Everything

Inside **Session.cpp**, almost everything funnels through:

```
Session::next()

Session::nextLogon()
Session::nextHeartbeat()
Session::nextResendRequest()
Session::nextSequenceReset()
Session::nextLogout()
```

Plus sequence logic:

```
Session::verify()
Session::doTargetTooHigh()
Session::doTargetTooLow()
```

---

# 13. The Most Important Production Detail

Professional trading systems **almost always modify QuickFIX behaviour** because:

| Issue              | Why                    |
| ------------------ | ---------------------- |
| disk persistence   | too slow               |
| resend performance | inefficient            |
| threading model    | blocking               |
| gap fill logic     | not exchange-optimized |

Real trading firms often implement:

```
custom message store
custom resend engine
lock-free IO
batch resend
```

---

✅ If you'd like, I can also show:

**1️⃣ The actual QuickFIX `Session.cpp` call graph** (the real internal flow)
**2️⃣ The FIX sequence number recovery algorithm used by exchanges**
**3️⃣ Why most HFT firms eventually replace the QuickFIX session engine** (very interesting architecture).

