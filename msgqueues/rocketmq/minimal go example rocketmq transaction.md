# Give me a minimal code sample of RocketMQ transaction message using golang


⏺ Minimal example using the official github.com/apache/rocketmq-client-go/v2 client. Models the same pattern as ChargeOrderPaymentTranProducer.

```go
package main

import (
    "context"
    "fmt"
    "os"
    "time"

    "github.com/apache/rocketmq-client-go/v2"
    "github.com/apache/rocketmq-client-go/v2/primitive"
    "github.com/apache/rocketmq-client-go/v2/producer"
)

// listener implements both halves of the 2PC protocol.
type listener struct{}

// Phase ②: called right after the half message is stored on the broker.
// Do your local DB write here; return COMMIT / ROLLBACK / UNKNOWN.
func (l *listener) ExecuteLocalTransaction(msg *primitive.Message) primitive.LocalTransactionState {
    orderID := msg.GetProperty("orderId")

    if err := insertOrder(orderID, msg.Body); err != nil {
            fmt.Println("local tx failed, will be checked back:", err)
            return primitive.UnknowState // broker will call CheckLocalTransaction later
    }
    return primitive.CommitMessageState
}

// Phase ④: broker calls this when it didn't get a definitive answer.
// Query your DB to figure out what actually happened.
func (l *listener) CheckLocalTransaction(msg *primitive.MessageExt) primitive.LocalTransactionState {
    orderID := msg.GetProperty("orderId")

    exists, err := orderExists(orderID)
    if err != nil {
            return primitive.UnknowState // try again later
    }
    if exists {
            return primitive.CommitMessageState
    }
    return primitive.RollbackMessageState
}

func main() {
    p, err := rocketmq.NewTransactionProducer(
            &listener{},
            producer.WithNameServer([]string{"127.0.0.1:9876"}),
            producer.WithGroupName("PID_WALLET_PAYMENT"),
            producer.WithRetry(2),
    )
    if err != nil {
            fmt.Println(err)
            os.Exit(1)
    }
    if err := p.Start(); err != nil {
            fmt.Println(err)
            os.Exit(1)
    }
    defer p.Shutdown()

    msg := &primitive.Message{
            Topic: "WALLET_PAYMENT_TOPIC",
            Body:  []byte(`{"orderId":"a2b3c4d5","chargeMoney":"100.50"}`),
    }
    msg.WithProperty("orderId", "a2b3c4d5") // used by the check-back to look up the row

    // Phase ①: send the half message. SDK then invokes ExecuteLocalTransaction.
    res, err := p.SendMessageInTransaction(context.Background(), msg)
    if err != nil {
            fmt.Println("send half failed:", err)
            return
    }
    fmt.Printf("result=%s msgId=%s\n", res.State, res.MsgID)

    time.Sleep(30 * time.Second) // keep the process alive so check-backs can land
}

// --- stubs ---
func insertOrder(id string, body []byte) error { return nil }
func orderExists(id string) (bool, error)      { return true, nil }

```

##  What's happening, mapped to the protocol

```
  ┌─────────────────────┬────────────────────────────────────────────┐
  │        Phase        │                    Code                    │
  ├─────────────────────┼────────────────────────────────────────────┤
  │ ① send half message │ p.SendMessageInTransaction(ctx, msg)       │
  ├─────────────────────┼────────────────────────────────────────────┤
  │ ② execute local tx  │ ExecuteLocalTransaction → insertOrder(...) │
  ├─────────────────────┼────────────────────────────────────────────┤
  │ ③ commit / rollback │ return value of ExecuteLocalTransaction    │
  ├─────────────────────┼────────────────────────────────────────────┤
  │ ④ check-back        │ CheckLocalTransaction → orderExists(...)   │
  └─────────────────────┴────────────────────────────────────────────┘

```
  Things to get right

  - Carry a business key as a message property (here orderId). The check-back has no transactional context — it can only look at the message itself plus your DB.
  - Producer group must be stable across restarts. When the original producer dies, the broker calls any producer in the same group for check-back. A unique-per-process group
  breaks the protocol.
  - Keep the process alive after sending. Check-backs default to ~60s after the half message; if you exit immediately after SendMessageInTransaction, no one answers them.
  - Return UnknowState, not an error, when you genuinely don't know — that's the signal to retry later. Returning RollbackMessageState on a transient DB blip permanently discards
   the message.
  - Consumer side still needs idempotency. Transaction messages guarantee "at least once after commit" — same as normal messages.


* Dependency

```
  go get github.com/apache/rocketmq-client-go/v2
```  