# #in MessageCracker, what does crack(message, sessionID) do

In the **QuickFIX/J** library, `MessageCracker` is a helper class used to **dispatch incoming FIX messages to the correct handler method based on message type**.

When you see this line:

```java
crack(message, sessionID);
```

inside something like:

```java
public void fromApp(Message message, SessionID sessionID)
        throws FieldNotFound, UnsupportedMessageType, IncorrectTagValue {
    crack(message, sessionID);
}
```

it performs **automatic message routing**.

---

## 1. What `crack()` actually does

`crack()`:

1. **Reads the FIX message type** (`MsgType`, tag **35**).
2. **Determines the specific FIX message class** (e.g., `NewOrderSingle`, `ExecutionReport`).
3. **Invokes the corresponding `onMessage()` handler** implemented in your class.

Conceptually:

```
Incoming FIX message
        │
        ▼
MessageCracker.crack()
        │
        ▼
Detect MsgType (tag 35)
        │
        ▼
Call the matching handler:
onMessage(NewOrderSingle msg, SessionID)
onMessage(ExecutionReport msg, SessionID)
onMessage(OrderCancelRequest msg, SessionID)
```

---

## 2. Example

### Your application

```java
public class MyFixApp extends MessageCracker implements Application {

    @Override
    public void fromApp(Message message, SessionID sessionID)
            throws FieldNotFound, UnsupportedMessageType, IncorrectTagValue {
        crack(message, sessionID);
    }

    public void onMessage(NewOrderSingle order, SessionID sessionID) {
        System.out.println("Received order: " + order);
    }

    public void onMessage(OrderCancelRequest cancel, SessionID sessionID) {
        System.out.println("Cancel order");
    }
}
```

---

### Incoming FIX message

Example FIX message:

```
8=FIX.4.4
35=D
55=AAPL
54=1
38=100
```

`35=D` means:

```
MsgType = D → NewOrderSingle
```

`crack()` will call:

```java
onMessage(NewOrderSingle order, SessionID sessionID)
```

---

## 3. What happens internally (simplified)

Internally `MessageCracker` uses **reflection**:

```java
String msgType = message.getHeader().getString(MsgType.FIELD);

switch(msgType) {
    case "D":
        onMessage((NewOrderSingle)message, sessionID);
        break;
    case "8":
        onMessage((ExecutionReport)message, sessionID);
        break;
}
```

But QuickFIX generates this automatically for **every FIX version**.

---

## 4. Why this exists

Without `MessageCracker`, you must manually do this:

```java
public void fromApp(Message message, SessionID sessionID) {

    String msgType = message.getHeader().getString(MsgType.FIELD);

    if (msgType.equals(MsgType.NEW_ORDER_SINGLE)) {
        NewOrderSingle order = (NewOrderSingle) message;
        ...
    }
}
```

Which is messy and unsafe.

`MessageCracker` gives:

* **type-safe handlers**
* **clean routing**
* **FIX-version-aware message classes**

---

## 5. Where `crack()` is usually used

Typical **QuickFIX/J Application flow**:

```
FIX session
    │
    ▼
fromAdmin()  ← admin messages (Logon, Heartbeat)
fromApp()    ← application messages
    │
    ▼
crack(message, sessionID)
    │
    ▼
onMessage(...)
```

---

## 6. Important detail many people miss

`crack()` **only routes application messages**, so it's normally used in:

```java
fromApp()
```

NOT:

```java
fromAdmin()
```

because admin messages (Logon, Heartbeat, TestRequest) are handled differently.

---

✅ **One sentence summary**

`crack(message, sessionID)` in QuickFIX/J **inspects the FIX MsgType and dispatches the message to the correct `onMessage()` handler method automatically.**

---

If you'd like, I can also show:

* **How `MessageCracker` is implemented internally (actual QuickFIX/J code)**
* **Why many HFT systems avoid `MessageCracker` for performance reasons** (very interesting microsecond-level design tradeoff).
