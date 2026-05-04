# Give me minimal golang example of outbox pattern to send msg to mq

⏺ Minimal outbox pattern in Go. Same effect as a RocketMQ transaction message but works with any broker — the local DB is the source of truth, and a separate relay drains it.

- Schema

```sql
CREATE TABLE orders (
id          VARCHAR(64) PRIMARY KEY,
amount      DECIMAL(10,2) NOT NULL,
created_at  DATETIME NOT NULL
);

CREATE TABLE outbox (
id          BIGINT AUTO_INCREMENT PRIMARY KEY,
topic       VARCHAR(128) NOT NULL,
payload     BLOB NOT NULL,
created_at  DATETIME NOT NULL,
sent_at     DATETIME NULL,
INDEX idx_unsent (sent_at, id)
);
```

- Code

```go
package main

import (
    "context"
    "database/sql"
    "encoding/json"
    "fmt"
    "time"

    _ "github.com/go-sql-driver/mysql"
)

type Publisher interface {
    Publish(ctx context.Context, topic string, payload []byte) error
}

// ---------- 1. Business write: order + outbox in ONE local transaction ----------

func CreateOrder(ctx context.Context, db *sql.DB, id string, amount float64) error {
    tx, err := db.BeginTx(ctx, nil)
    if err != nil {
            return err
    }
    defer tx.Rollback()

    if _, err := tx.ExecContext(ctx,
            `INSERT INTO orders (id, amount, created_at) VALUES (?, ?, ?)`,
            id, amount, time.Now()); err != nil {
            return err
    }

    payload, _ := json.Marshal(map[string]any{"orderId": id, "amount": amount})
    if _, err := tx.ExecContext(ctx,
            `INSERT INTO outbox (topic, payload, created_at) VALUES (?, ?, ?)`,
            "WALLET_PAYMENT_TOPIC", payload, time.Now()); err != nil {
            return err
    }

    return tx.Commit() // both rows commit atomically, or neither does
}

// ---------- 2. Relay: drain unsent rows, publish, mark sent ----------

func RunRelay(ctx context.Context, db *sql.DB, pub Publisher) error {
    tick := time.NewTicker(500 * time.Millisecond)
    defer tick.Stop()

    for {
            select {
            case <-ctx.Done():
                    return ctx.Err()
            case <-tick.C:
                    if err := drainBatch(ctx, db, pub, 100); err != nil {
                            fmt.Println("relay error:", err)
                    }
            }
    }
}

func drainBatch(ctx context.Context, db *sql.DB, pub Publisher, limit int) error {
    tx, err := db.BeginTx(ctx, nil)
    if err != nil {
            return err
    }
    defer tx.Rollback()

    // FOR UPDATE SKIP LOCKED lets multiple relays run in parallel without stepping on each other.
    rows, err := tx.QueryContext(ctx,
            `SELECT id, topic, payload FROM outbox
                WHERE sent_at IS NULL
                ORDER BY id
                LIMIT ?
                FOR UPDATE SKIP LOCKED`, limit)
    if err != nil {
            return err
    }

    type item struct {
            id      int64
            topic   string
            payload []byte
    }
    var batch []item
    for rows.Next() {
            var it item
            if err := rows.Scan(&it.id, &it.topic, &it.payload); err != nil {
                    rows.Close()
                    return err
            }
            batch = append(batch, it)
    }
    rows.Close()

    for _, it := range batch {
            if err := pub.Publish(ctx, it.topic, it.payload); err != nil {
                    return err // unlock by rolling back; retry on next tick
            }
            if _, err := tx.ExecContext(ctx,
                    `UPDATE outbox SET sent_at = ? WHERE id = ?`, time.Now(), it.id); err != nil {
                    return err
            }
    }

    return tx.Commit()
}

Wire it up

db, _ := sql.Open("mysql", "user:pass@tcp(127.0.0.1:3306)/demo?parseTime=true")
pub := myMQClient // implements Publish(ctx, topic, payload) error

go RunRelay(context.Background(), db, pub)

CreateOrder(ctx, db, "a2b3c4d5", 100.50)
```


- Why this works

```
┌──────────────────────────────────────────────┬────────────────────────────────────────────────────────────────────────────────────────────┐
│                Failure point                 │                                        What happens                                        │
├──────────────────────────────────────────────┼────────────────────────────────────────────────────────────────────────────────────────────┤
│ Crash before tx.Commit()                     │ Both rows roll back. Order doesn't exist, no message.                                      │
├──────────────────────────────────────────────┼────────────────────────────────────────────────────────────────────────────────────────────┤
│ Crash after tx.Commit(), before publish      │ Order exists, outbox row pending. Relay picks it up on next tick.                          │
├──────────────────────────────────────────────┼────────────────────────────────────────────────────────────────────────────────────────────┤
│ Crash after publish, before UPDATE … sent_at │ Same row gets republished next tick → at-least-once delivery. Consumer must be idempotent. │
├──────────────────────────────────────────────┼────────────────────────────────────────────────────────────────────────────────────────────┤
│ Broker down for an hour                      │ Rows pile up in outbox, drain when broker recovers. No data loss.                          │
└──────────────────────────────────────────────┴────────────────────────────────────────────────────────────────────────────────────────────┘
```

## Things to get right

- Same DB transaction for the business row and the outbox row. That's the whole point. If they're in different transactions or different databases, you've reinvented the
dual-write problem.
- FOR UPDATE SKIP LOCKED lets you scale to multiple relay instances without one blocking another. (MySQL 8.0+, Postgres 9.5+.)
- Idempotency on the consumer. Same as RocketMQ transactional messages — relay can crash mid-batch and republish.
- Cleanup. Either keep sent_at IS NOT NULL rows for audit and prune them on a schedule, or DELETE instead of UPDATE. Don't let the table grow forever.
- Ordering caveat. Order is preserved per single relay batch; with parallel relays, only ordering within an aggregate (e.g. same orderId) matters — partition the table or hash
the dispatch if you need it.

## vs. RocketMQ transaction messages

```
┌────────────────────┬──────────────────────────┬───────────────────────────────────────────┐
│                    │          Outbox          │            RocketMQ TX message            │
├────────────────────┼──────────────────────────┼───────────────────────────────────────────┤
│ Source of truth    │ Your DB                  │ The broker (with check-back into your DB) │
├────────────────────┼──────────────────────────┼───────────────────────────────────────────┤
│ Operational pieces │ DB + relay process       │ Broker only                               │
├────────────────────┼──────────────────────────┼───────────────────────────────────────────┤
│ Broker portability │ Any                      │ RocketMQ-specific                         │
├────────────────────┼──────────────────────────┼───────────────────────────────────────────┤
│ Latency floor      │ Poll interval (~ms)      │ Near-immediate after commit               │
├────────────────────┼──────────────────────────┼───────────────────────────────────────────┤
│ Failure recovery   │ Relay reads pending rows │ Broker calls CheckLocalTransaction        │
└────────────────────┴──────────────────────────┴───────────────────────────────────────────┘
```