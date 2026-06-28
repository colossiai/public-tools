# Bench report — 08 Lifetimes

Source: [`../examples/08_lifetimes.rs`](../examples/08_lifetimes.rs) ·
Harness: [`../benches/bench_all.rs`](../benches/bench_all.rs) (`bench_08_lifetimes`) ·
Machine: see [README](README.md).

## What is measured

Lifetimes are a *compile-time* mechanism with no runtime representation — so the
measurable payoff is what they **enable**: zero-copy borrowing. We tokenize a large
comma-separated string (~500K tokens) two ways:

- **borrow** — yield `&str` slices that point into the original string (what the
  lifetime annotations in the demo make safe). No allocation.
- **owned** — `.to_string()` each token into a fresh heap `String`.

Best of 7.

## Results

| run | borrow `&str` (ms) | owned `String` (ms) | owned / borrow |
|----:|-------------------:|--------------------:|---------------:|
| 1 | 8.60 | 31.44 | 3.65× |
| 2 | 6.29 | 23.23 | 3.69× |
| **representative** | **~7.5** | **~27** | **~3.7×** |

## Interpretation

- Borrowing is **~3.7× faster** here because it does **zero allocation** — each token
  is just a (pointer, length) window into the input. The owned version heap-allocates
  and copies once per token.
- Lifetimes (`&'a str`, the `Tokens<'a>` struct in the demo) are what let you return
  these borrowed slices *safely*: the compiler proves they never outlive the string
  they point into. The annotation costs nothing at runtime — it's erased after
  checking.
- The lesson: model with borrows on the hot path (parsers, views, slices) and only
  allocate an owned copy when you genuinely need to keep the data past the source's
  lifetime.

## Reproduce

```sh
cargo bench   # see the 08_lifetimes line
```
