# Price Alert Edge Trigger

A self-contained design note on **edge-triggered price alerts**: what an "edge"
means for a price stream, why edge triggering is the correct default for alerts,
and the rules that keep alerts from firing too much or too little.

---

## 1. Level vs. Edge

Borrowed from digital electronics, a **condition** over a price can be observed in
two ways:

| Mode | Fires when… | Behavior |
|------|-------------|----------|
| **Level trigger** | the condition *is currently true* | keeps firing on every tick while true |
| **Edge trigger** | the condition *becomes true* (false → true transition) | fires once per crossing |

For a threshold alert like `price >= 100`:

- A **level** view is true on *every* tick as long as price stays at or above 100.
  Naively alerting on level produces a storm of duplicate notifications.
- An **edge** view is true only on the tick where price moves from below 100 to at
  or above 100. That single transition is the *edge*, and it is what a human
  actually wants to be told about.

> An edge trigger fires on the **transition**, not on the **state**.

---

## 2. The Core Model

An edge trigger needs three ingredients:

1. **A predicate** `P(price)` — the condition, e.g. `price >= threshold`.
2. **The previous evaluation** `prev = P(price_{t-1})`.
3. **The current evaluation** `curr = P(price_t)`.

The alert fires **iff** `prev == false && curr == true`.

```
       previous      current      action
       --------      -------      ------
        false         false        (nothing)
        false         true         FIRE   ← the edge
        true          true         (nothing — still true, no new edge)
        true          false        (nothing — reset; arms the next edge)
```

The `true → false` step is silent but essential: it **re-arms** the trigger so the
next `false → true` can fire again. Without tracking `prev`, the system cannot
distinguish "newly true" from "still true."

### Rising vs. falling edge

- **Rising edge** — price crosses a threshold *upward* (`>=`): "notify me when BTC
  reaches 100k."
- **Falling edge** — price crosses *downward* (`<=`): "notify me when it drops to
  90k."

Both are the same mechanism with a different predicate. A two-sided band ("notify
if it leaves the 95k–105k range") is simply the OR of two edge predicates.

---

## 3. Why Edge, Not Level

| Problem with level triggering | How edge triggering solves it |
|-------------------------------|-------------------------------|
| Alert fires on every tick while condition holds → notification spam | Fires once per crossing |
| User can't tell "just happened" from "still happening" | The edge *is* the "just happened" signal |
| Cost/rate-limit pressure on the notification channel | O(crossings) instead of O(ticks) |
| Repeated alerts train the user to ignore them | Each alert corresponds to a real event |

The whole value of an alert is that it marks a **change worth attention**. Level
triggering conflates change with state and destroys that value.

---

## 4. Necessary State

To detect an edge you must remember something between evaluations. The minimum is
the previous predicate result (`armed` / `not armed`). Practically, systems store:

- **`last_state`** (armed / triggered) — the FSM position.
- **`last_price`** or **`last_eval`** — to recompute the predicate on the boundary.
- **`triggered_at`** — for cooldown / dedup (see §6).

```
        price crosses up
  ┌────────┐ ─────────────────▶ ┌───────────┐
  │ ARMED  │                    │ TRIGGERED │  → emit alert
  └────────┘ ◀───────────────── └───────────┘
        price falls back below (minus hysteresis)
```

A trigger that has fired sits in **TRIGGERED** and will not fire again until price
returns to the ARMED side. This is what makes it "once per crossing."

---

## 5. The Boundary Problems

Real price streams are noisy and discrete. A correct edge trigger must decide the
following explicitly:

### 5.1 Exact equality
Is `price == threshold` a crossing? Pick one convention and apply it consistently.
Using `>=` for the rising predicate means touching the threshold counts as crossing;
using `>` means it must strictly exceed. Document the choice — off-by-one at the
boundary is the most common alert bug.

### 5.2 Gaps and skips
Price is sampled, not continuous. If the previous sample is 98 and the next is 103,
the price *crossed* 100 even though no sample equals 100. Edge detection based on
predicate transition (`prev=false, curr=true`) handles this correctly — do **not**
require a sample *at* the threshold.

### 5.3 First evaluation / cold start
On the very first tick there is no `prev`. Two safe conventions:

- **Seed as not-yet-fired**: initialize `prev` by evaluating the predicate on the
  first price *without firing*. An alert set to `>= 100` while price is already 110
  will **not** fire immediately — it waits for a genuine future crossing.
- **Fire-if-already-true**: some products intentionally fire on creation if the
  condition already holds. This is a deliberate product choice, not a default.

Prefer *seed-without-firing* unless the product explicitly wants creation-time
alerts; otherwise every alert created "already in the money" spams instantly.

### 5.4 Flapping (chatter)
Price hovering exactly at the threshold (100.0, 99.9, 100.1, 99.9, …) crosses the
boundary many times per second, producing an edge storm. This is the single most
important failure mode and is addressed by hysteresis and cooldown below.

---

## 6. Debouncing an Edge

Three complementary techniques prevent a noisy signal from producing a noisy alert.

### 6.1 Hysteresis (a dead band)
Use **two** thresholds instead of one:

- Fire when price rises **above** `T_high`.
- Re-arm only when price falls **below** `T_low` (with `T_low < T_high`).

Price must travel the full band to re-arm, so small oscillations near `T_high` can
no longer flap. The band width is chosen from the instrument's typical noise.

```
  price ─────────────────────────────
        ── T_high ── ● fire ──────────
                        (dead band — no state change)
        ── T_low  ─────────────── ○ re-arm
```

### 6.2 Cooldown (minimum re-fire interval)
After firing, suppress any further fire for a fixed duration (e.g. 5 minutes),
regardless of crossings. Guarantees an upper bound on notification rate per alert.

### 6.3 Confirmation (debounce window)
Require the predicate to hold for N consecutive ticks, or for T milliseconds, before
firing. Filters out single-tick spikes and bad ticks at the cost of a small delay.

Choose per product: hysteresis for oscillation, cooldown for rate-limiting,
confirmation for spike rejection. They compose.

---

## 7. One-Shot vs. Recurring

- **One-shot**: the alert fires once and is then disabled/deleted. No re-arming.
  Common for "tell me when it hits my target" user alerts.
- **Recurring**: after firing it re-arms (per §4/§6) and can fire on every future
  crossing. Common for monitoring/ops alerts.

Both are edge-triggered; they differ only in what happens *after* the edge.

---

## 8. Reference Pseudocode

```text
function evaluate(alert, price, now):
    curr = predicate(alert, price)          # e.g. price >= alert.threshold

    if alert.state == ARMED:
        if curr:                            # false → true : the rising edge
            if now - alert.triggered_at < alert.cooldown:
                return                      # suppressed by cooldown
            fire(alert)
            alert.triggered_at = now
            alert.state = TRIGGERED
            if alert.one_shot:
                disable(alert)

    else:  # TRIGGERED
        if price_below_rearm(alert, price): # apply hysteresis band here
            alert.state = ARMED             # silent re-arm

# cold start: set alert.state based on predicate(price0) WITHOUT firing
```

Key invariants:
- Never fire while already in `TRIGGERED`.
- Re-arm is silent.
- Cooldown is checked at the moment of firing, not at re-arm.
- Edge is derived from state transition, never from the raw level.

---

## 9. Design Checklist

- [ ] Predicate and equality convention (`>=` vs `>`) are documented.
- [ ] `prev`/state is persisted so restarts don't lose armed/triggered status.
- [ ] Cold-start behavior chosen: seed-without-firing (default) or fire-if-true.
- [ ] Gap crossings (no sample at threshold) fire correctly.
- [ ] Anti-flap strategy chosen: hysteresis and/or cooldown and/or confirmation.
- [ ] One-shot vs. recurring lifecycle defined.
- [ ] Notification is idempotent / deduplicated against replayed ticks.
- [ ] Upper bound on fires-per-interval is guaranteed.

---

## 10. Glossary

- **Edge** — a transition of the predicate from false to true (or true to false).
- **Rising / falling edge** — upward / downward threshold crossing.
- **Arm** — the state in which the next edge is allowed to fire.
- **Trigger / fire** — emit the alert on a detected edge.
- **Hysteresis** — separate fire and re-arm thresholds forming a dead band.
- **Cooldown** — minimum interval between two fires of the same alert.
- **Debounce / confirmation** — require persistence before firing.
- **Flapping** — rapid repeated crossings caused by noise at the boundary.