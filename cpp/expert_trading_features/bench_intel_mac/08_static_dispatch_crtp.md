# Bench report — 08 Static dispatch (CRTP vs virtual)

Source: [`../08_static_dispatch_crtp.cpp`](../08_static_dispatch_crtp.cpp) ·
Technique: replace a `virtual` per-tick callback with compile-time polymorphism (CRTP)
so the body **inlines** into the feed loop instead of dispatching through a vtable.

## Environment

| | |
|---|---|
| CPU | Intel Core i7-9750H @ 2.60 GHz (Coffee Lake, 6C/12T, turbo to ~4.5 GHz) |
| OS / arch | macOS (Darwin 25.5), x86_64 |
| Compiler | Apple clang 21.0.0, libc++ |
| Flags | `-std=c++20 -O2 -Wall -Wextra -pthread` |

> Laptop, turbo + frequency scaling left on, threads not pinned. Numbers are
> *illustrative ratios*.

## What is measured

A momentum "strategy" processes a feed of `N = 20,000,000` ticks, two ways:

- **virtual** — `std::unique_ptr<IStrategy>`, `vs->on_tick(t)` through the vtable
  (the realistic, pessimistic case: the compiler can't see the target).
- **CRTP** — `MomentumCRTP` with static dispatch; `on_tick` resolves at compile time
  and inlines into the loop.

Both compute the same P&L (printed, and equal — a correctness check). Reported as
ns/tick.

## Results (3 runs)

| run | virtual ns/tick | CRTP ns/tick | speedup |
|----:|----------------:|-------------:|--------:|
| 1 | 2.732 | 1.612 | 1.69× |
| 2 | 2.409 | 1.174 | 2.05× |
| 3 | 2.252 | 1.278 | 1.76× |
| **representative** | **~2.5** | **~1.3** | **~1.8×** |

## Interpretation

- Removing the vtable indirection is worth ~**1.8×** here. The virtual call is an
  indirect jump the CPU can't inline across; CRTP lets the compiler inline the body,
  keep strategy state in registers, and optimize across iterations.
- The win **scales inversely with callback size**: the smaller and hotter the body,
  the more the vtable overhead dominates and the bigger the inlining payoff. For a
  heavy callback the relative gap shrinks.
- Use this when the **set of strategy types is known at compile time**. When you need
  runtime-pluggable strategies, `std::variant` + `std::visit` keeps a closed type set
  with no vtable while still allowing heterogeneous containers.
- Both paths produce identical P&L (`10000990`), so the speedup is free of behavioral
  change — purely a dispatch-cost difference.

## Reproduce

```sh
make bin/08_static_dispatch_crtp && bin/08_static_dispatch_crtp
```
