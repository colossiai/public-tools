# io_uring vs Java Disruptor

Both are built on the same core insight: replace a lock-based, boundary-crossing-heavy
handoff with a **pre-allocated ring buffer + sequence counters coordinated by memory
barriers**. This note captures what io_uring is, and how it relates to the LMAX Disruptor.

## What is io_uring?

`io_uring` is a Linux asynchronous I/O interface (kernel 5.1, 2019, by Jens Axboe). It
fixes the performance/usability problems of `epoll`, POSIX AIO, and `libaio`.

### The name

`io_uring` = **I/O userspace ring buffer**:

- **io** — input/output
- **u** — **userspace**: the ring buffers are `mmap`-ed into the process and shared with
  the kernel, so userspace produces submissions and consumes completions directly in
  shared memory — no syscall needed just to enqueue/dequeue. This is the defining
  innovation, hence the "u" in the name.
- **ring** — the SQ (submission) and CQ (completion) ring buffers.

Pronounced "I-O-U-ring"; Axboe has noted the happy coincidence that it reads as "IOU"
("I owe you") — you submit a request now, the kernel owes you a completion later, which
fits its deferred, completion-based nature.

### Architecture: two shared ring buffers

```
   Userspace                          Kernel
  ┌───────────────┐                 ┌───────────────┐
  │  Submission   │  ── entries ──▶ │   processes    │
  │  Queue (SQ)   │                 │   the SQEs     │
  └───────────────┘                 └───────────────┘
  ┌───────────────┐                 ┌───────────────┐
  │  Completion   │  ◀── results ── │  posts CQEs    │
  │  Queue (CQ)   │                 │                │
  └───────────────┘                 └───────────────┘
```

- **SQ / SQE**: you fill submission queue entries — opcode (`read`, `write`, `accept`,
  `send`, …), fd, buffer pointer, offset, and a `user_data` tag.
- **CQ / CQE**: the kernel posts completion queue entries with the result (return value +
  your `user_data` so you can match it to the request).
- Each ring uses head/tail indices, coordinated with memory barriers instead of locks.

### The three syscalls

1. `io_uring_setup(entries, params)` — creates the rings, returns an fd.
2. `io_uring_enter(fd, to_submit, min_complete, flags)` — process submissions and/or wait
   for completions. The only hot-path call, and it **batches** many ops into one.
3. `io_uring_register(...)` — pre-register buffers/files to avoid re-pinning memory and
   re-doing refcount work per op.

Most code uses **liburing** (Axboe's helper library) rather than raw syscalls.

### What makes it fast

- **Batching** — queue N operations, one `io_uring_enter` submits them all.
- **`IORING_SETUP_SQPOLL`** — a kernel thread polls the SQ, so steady-state submission is
  **zero syscalls**.
- **Registered buffers/files** — skip per-op memory pinning and fd lookups.
- **Provided buffers** — kernel picks a buffer from a pool at completion time.
- **Linked SQEs** (`IOSQE_IO_LINK`) — chain dependent ops without a userspace round-trip.

### Comparison with older I/O

| | Syscalls/op | Model | Files | Sockets |
|---|---|---|---|---|
| blocking I/O | 1 | sync | ✅ | ✅ (blocks) |
| `epoll` | 2 (wait + read) | readiness | ⚠️ poor | ✅ |
| POSIX AIO / libaio | 1+ | completion | ⚠️ limited | ❌ |
| **io_uring** | ~0 (batched/SQPOLL) | completion | ✅ | ✅ |

---

## The connection to the LMAX Disruptor

### Shared principle

Both replace a lock-based, contention/syscall-heavy handoff with a pre-allocated ring
buffer + sequence counters coordinated by memory barriers.

| Concept | Disruptor | io_uring |
|---|---|---|
| The buffer | `RingBuffer` of pre-allocated slots | SQ / CQ rings in shared memory |
| Position tracking | `Sequence` (padded `AtomicLong`) cursors | head/tail indices |
| Coordination | memory barriers, no locks | memory barriers, no locks |
| Allocation | slots reused, no per-event GC | entries reused, no per-op alloc |
| Producer/consumer | claim slot → publish → advance | fill SQE → advance tail |

Mental model for both: **a fixed circular array where one side advances a "produced up to
here" counter and the other advances a "consumed up to here" counter; the gap is the
outstanding work. Neither side locks — they synchronize purely through ordered
reads/writes of the sequence counters.**

### Why both avoid locks the same way

The expensive thing in both worlds is the **boundary crossing**:

- Disruptor: boundary is **thread↔thread**; cost is cache-line contention + lock/CAS +
  context switches when a queue blocks.
- io_uring: boundary is **userspace↔kernel**; cost is the syscall + context switch.

Both attack it identically: batch across the boundary, and in steady state don't cross it
at all (Disruptor batches available sequences; io_uring `SQPOLL` crosses zero syscalls).

### Shared detail: mechanical sympathy

- Disruptor pads `Sequence` to 64 bytes so producer/consumer cursors don't share a cache
  line (false sharing).
- io_uring lays out SQ tail and CQ head to avoid the same cache-line thrashing.
- Both design the data layout around how CPU caches and memory ordering actually work.

### Where they genuinely differ

1. **What's on the other side.**
   - Disruptor: another application thread, same address space. Pure userspace.
   - io_uring: the kernel, which does actual I/O (disk, NIC). The ring is the interface to
     a privileged domain.

2. **Completion model.**
   - Disruptor is a one-way pipe (producer → consumers). A "result" needs a second ring.
   - io_uring is intrinsically request/response: SQ = requests, CQ = completions, matched
     by `user_data`. Two rings because every submission expects a later completion (the
     "IOU").

3. **What flows through it.**
   - Disruptor slots hold your objects/events — arbitrary in-process data.
   - io_uring entries hold operation descriptors (opcode + fd + buffer pointer). The data
     buffer lives elsewhere; the ring carries the instruction, not usually the bytes.

4. **Ordering / dependency guarantees.**
   - Disruptor offers rich consumer topologies — dependency graphs, multiple consumers,
     gating sequences (batch → parallel → journal → replicate).
   - io_uring completions can arrive out of order; ordering is opt-in via linked SQEs.

### Summary

At the level of *lock-free ring buffer + sequence counters + memory barriers + mechanical
sympathy to kill boundary-crossing cost*, they are the **same principle** — convergent
design against the same physics (cache coherence, cost of synchronization).

They differ in **what the boundary is** (thread↔thread vs userspace↔kernel) and **what
semantics they layer on top** (one-way event stream vs two-way request/completion).

If you understand why the Disruptor beats an `ArrayBlockingQueue`, you already understand
~80% of why io_uring beats `epoll` + `read()`. The remaining 20% is just "one side of the
ring happens to be the kernel doing real I/O."
