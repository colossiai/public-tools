⏺ This is a ZGC allocation stall log that shows how many times application threads had to wait for GC to free up memory during different GC phases.

  Log Breakdown

  [6.654s]                    # Timestamp: 6.654 seconds since JVM start
  [info][gc,alloc]            # Log level: info, tags: gc+alloc
  GC(68)                      # This is the 68th GC cycle
  y:                          # Young gen marker (legacy compatibility)

  The Table

  The log shows allocation stall counts across 4 GC phases:

```
  ┌────────────────┬────────┬───────────────────────────────────────────────┐
  │     Phase      │ Stalls │                    Meaning                    │
  ├────────────────┼────────┼───────────────────────────────────────────────┤
  │ Mark Start     │ 0      │ Stalls during the start of concurrent marking │
  ├────────────────┼────────┼───────────────────────────────────────────────┤
  │ Mark End       │ 0      │ Stalls at the end of marking phase            │
  ├────────────────┼────────┼───────────────────────────────────────────────┤
  │ Relocate Start │ 0      │ Stalls at the start of relocation             │
  ├────────────────┼────────┼───────────────────────────────────────────────┤
  │ Relocate End   │ 0      │ Stalls at the end of relocation               │
  └────────────────┴────────┴───────────────────────────────────────────────┘
```

  ---
  What is an "Allocation Stall"?

  An allocation stall occurs when:

  1. Application thread tries to allocate a new object
  2. ZGC has no free memory available
  3. ZGC concurrent work hasn't kept pace with allocation rate
  4. Thread must WAIT (stall) for GC to reclaim memory
  5. Application effectively pauses despite ZGC being "low latency"

  This is the key failure mode that scenario 3 (Allocation Spike) is designed to demonstrate!

  ---
  Interpreting the Values

  ✅ All zeros (like your log):

  Allocation Stalls:  0  0  0  0
  GOOD! No stalls occurred. ZGC is keeping up with allocation rate.

  ❌ Non-zero values (broken scenario):

  Allocation Stalls:  5  12  3  8
  BAD! Application threads stalled 28 times waiting for GC. This means:
  - Low pause times (GC pauses still <1ms)
  - But terrible throughput (app threads keep blocking)
  - The paradox: "Low latency GC" but app barely makes progress!

  ---
  When You'll See Stalls

  In the broken scenarios, you should see:

  Scenario 2 (CPU Starvation):
  Allocation Stalls:  10  20  5  15  # GC too slow, app must wait

  Scenario 3 (Allocation Spike):
  Allocation Stalls:  25  50  30  40  # Extreme allocation overwhelms GC

  ---
  How to Enable This Log

  This log appears when you use:
  -Xlog:gc+alloc=trace

  You can see it's enabled in scenario-3-allocation-spike.sh line 21:
  -Xlog:gc+alloc=trace

  This is a diagnostic flag to track allocation stalls and prove that ZGC can fail to provide good throughput even with low pause times!