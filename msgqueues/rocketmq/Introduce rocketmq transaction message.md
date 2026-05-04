# Introduce RocketMQ transaction message

```
⏺ RocketMQ Transaction Message

  A transaction message in RocketMQ is a two-phase commit pattern that solves one specific problem: how do I atomically (a) write to my local database AND (b) publish a message,
  with no possibility of one succeeding while the other fails?

  This is the classic dual-write problem. Without transactional messages you have to choose which one to do first — and either order can leave the system inconsistent if the
  second step fails.

  ---
  The Two-Phase Protocol

  Producer                          Broker                       Consumer
     │                                │                              │
     │  ① send HALF message           │                              │
     ├───────────────────────────────►│  (stored, NOT visible)       │
     │                                │                              │
     │  ② execute local transaction   │                              │
     │     (write DB row)             │                              │
     │                                │                              │
     │  ③ COMMIT / ROLLBACK / UNKNOW  │                              │
     ├───────────────────────────────►│                              │
     │                                │                              │
     │                                │  if COMMIT: deliver ────────►│
     │                                │  if ROLLBACK: discard        │
     │                                │  if UNKNOW: ④ check-back     │
     │  ④ checkLocalTransaction()     │                              │
     │◄───────────────────────────────┤                              │
     │  query DB → COMMIT or ROLLBACK │                              │
     ├───────────────────────────────►│                              │

  Phase 1 — Half message

  The producer sends the message to a special internal topic (RMQ_SYS_TRANS_HALF_TOPIC). The broker stores it but does not deliver it to consumers — it's invisible.

  Phase 2 — Local transaction

  The producer runs executeLocalTransaction() (your business DB write) and reports one of three outcomes:

  ┌──────────────────┬───────────────────────────────────────────────────────────────┐
  │      State       │                         Broker action                         │
  ├──────────────────┼───────────────────────────────────────────────────────────────┤
  │ COMMIT_MESSAGE   │ Move half message to the real topic → consumers see it        │
  ├──────────────────┼───────────────────────────────────────────────────────────────┤
  │ ROLLBACK_MESSAGE │ Discard the half message                                      │
  ├──────────────────┼───────────────────────────────────────────────────────────────┤
  │ UNKNOW           │ Wait, then ask the producer again via checkLocalTransaction() │
  └──────────────────┴───────────────────────────────────────────────────────────────┘

  Phase 3 — Check-back (the safety net)

  If the producer crashes between writing the DB row and reporting commit, the broker periodically calls checkLocalTransaction() on any producer in the same group. That callback
  queries the DB ("does row with orderId=X exist?") and answers COMMIT or ROLLBACK. This is what makes the protocol crash-safe.

  ---
  How this project uses it

  In order-charge-gateway-server, ChargeOrderPaymentTranProducer does exactly this for the order-creation + wallet-payment hop:

  // step ①  send half message to WALLET_PAYMENT_TOPIC
  // step ②  executeLocalTransaction:
  //           INSERT INTO t_merchant_order (...)
  //           return COMMIT_MESSAGE on success, UNKNOW on exception
  // step ④  checkLocalTransaction:
  //           SELECT FROM t_merchant_order WHERE order_id=?
  //           found    → COMMIT_MESSAGE
  //           not found → ROLLBACK_MESSAGE

  Without the transaction message, two failure modes would be possible:

  1. DB written, message never sent → order exists but wallet never gets debited.
  2. Message sent, DB write failed → wallet gets debited for an order that doesn't exist.

  The transaction message eliminates both: the consumer (notify service) only ever sees the message after the broker confirms the DB write actually committed.

  ---
  Important properties (and non-properties)

  ✅ Atomic with the local DB — the message becomes visible iff the local transaction committed.

  ✅ Crash-safe — check-back recovers from producer crashes between phase 1 and phase 3.

  ❌ NOT distributed XA — the consumer's processing is not part of the transaction. Once delivered, the consumer must handle the message at-least-once with its own idempotency.

  ❌ NOT zero-latency — the message is held until the local transaction reports back, and check-backs happen on a timer (default ~60s).

  ⚠️ Idempotency is still your job — RocketMQ may deliver the same committed message more than once. That's why WalletPaymentMsgListenerImpl first checks t_merchant_charge_record
   by orderId before deducting — same message arriving twice doesn't double-charge.

  ---
  Why not just use a local DB transaction + outbox table?

  The outbox pattern (write the message to a pending_outbox table in the same DB transaction, have a poller publish it) is the alternative. RocketMQ's transaction message is
  essentially the outbox pattern with the broker maintaining the pending state and doing the polling for you — at the cost of coupling to RocketMQ. The trade-off is operational
  simplicity vs. portability.

```