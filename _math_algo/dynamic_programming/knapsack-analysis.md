# show detail classic knapsack analysis


The **0/1 Knapsack Problem** is one of the most important patterns in **Dynamic Programming**. Once you understand it deeply, you unlock solutions to dozens of problems (subset sum, partition equal subset, coin change variants, etc.).

I'll walk through the **full classic analysis** step-by-step.

---

# 1. Problem Definition

You have:

* `n` items
* each item has

  * weight `w[i]`
  * value `v[i]`

You have a knapsack with capacity `W`.

Goal:

Maximize total value without exceeding capacity.

Constraint:

Each item can be chosen **0 or 1 time**.

Example:

| item | weight | value |
| ---- | ------ | ----- |
| 1    | 1      | 1     |
| 2    | 3      | 4     |
| 3    | 4      | 5     |
| 4    | 5      | 7     |

Capacity = **7**

---

# 2. Brute Force Thinking (Exponential)

Each item has **2 choices**

```
take
not take
```

Total possibilities:

```
2^n
```

Example decision tree

```
item1
 ├─ take
 │   ├─ item2 take
 │   └─ item2 skip
 └─ skip
     ├─ item2 take
     └─ item2 skip
```

Time complexity:

```
O(2^n)
```

Too slow.

---

# 3. The Key DP Insight

We notice **overlapping subproblems**.

Define:

```
dp[i][w]
```

Meaning:

```
max value using first i items
with capacity w
```

---

# 4. State Transition (Core Equation)

For item `i`:

Two choices.

### 1. Do not take item i

```
dp[i][w] = dp[i-1][w]
```

### 2. Take item i (if possible)

```
dp[i][w] = dp[i-1][w - weight[i]] + value[i]
```

Combine:

```
dp[i][w] =
max(
    dp[i-1][w],
    dp[i-1][w-weight[i]] + value[i]
)
```

This is the **entire knapsack algorithm**.

---

# 5. Example DP Table

Items:

```
weights = [1,3,4,5]
values  = [1,4,5,7]
capacity = 7
```

DP table:

```
        capacity
      0 1 2 3 4 5 6 7
item0 0 0 0 0 0 0 0 0
item1 0 1 1 1 1 1 1 1
item2 0 1 1 4 5 5 5 5
item3 0 1 1 4 5 6 6 9
item4 0 1 1 4 5 7 8 9
```

Answer:

```
9
```

Items chosen:

```
item2 + item3
```

---

# 6. Classic Implementation (Go)

```go
func knapsack(weights []int, values []int, W int) int {
    n := len(weights)

    dp := make([][]int, n+1)
    for i := range dp {
        dp[i] = make([]int, W+1)
    }

    for i := 1; i <= n; i++ {
        for w := 1; w <= W; w++ {

            if weights[i-1] <= w {
                dp[i][w] = max(
                    dp[i-1][w],
                    dp[i-1][w-weights[i-1]] + values[i-1],
                )
            } else {
                dp[i][w] = dp[i-1][w]
            }

        }
    }

    return dp[n][W]
}
```

---

# 7. Time & Space Complexity

|       | complexity |
| ----- | ---------- |
| Time  | `O(nW)`    |
| Space | `O(nW)`    |

Where:

```
n = number of items
W = capacity
```

---

# 8. Space Optimization (The Famous Trick)

Observation:

```
dp[i] depends only on dp[i-1]
```

So we collapse to **1D DP**.

### Key rule

Iterate capacity **backwards**.

```
for w := W; w >= weight[i]; w--
```

---

### Optimized Go Version

```go
func knapsack(weights []int, values []int, W int) int {

    dp := make([]int, W+1)

    for i := 0; i < len(weights); i++ {

        for w := W; w >= weights[i]; w-- {

            dp[w] = max(
                dp[w],
                dp[w-weights[i]] + values[i],
            )

        }
    }

    return dp[W]
}
```

---

# 9. Why Backward Iteration Matters

If we go **forward**, the item may be used **multiple times**.

Backward ensures:

```
each item used once
```

Forward iteration becomes:

```
unbounded knapsack
```

---

# 10. Visual Intuition (Why DP Works)

The DP grid represents **all capacities × all prefixes of items**.

```
items →
capacity ↓
```

Each cell answers:

> "What is the best we can do so far?"

DP builds solutions **incrementally**.

---

# 11. Knapsack Pattern Recognition

Many problems secretly use knapsack.

Examples:

| Problem                | Mapping            |
| ---------------------- | ------------------ |
| Subset Sum             | value = weight     |
| Partition Equal Subset | subset sum / 2     |
| Target Sum             | sign knapsack      |
| Coin Change            | unbounded knapsack |
| Rod Cutting            | unbounded knapsack |

---

# 12. The Deep Insight (What DP Really Does)

Knapsack converts an **exponential decision tree**

```
2^n
```

into a **grid of states**

```
n × W
```

So DP is essentially:

```
memoization of decisions
```

---

✅ **Most important takeaway**

Knapsack DP always follows this template:

```
dp[state] =
    max(
        don't choose,
        choose
    )
```

---

If you'd like, I can also show:

**The 5 knapsack variants that appear in Google/Meta interviews**

1. 0/1 knapsack
2. complete knapsack
3. multiple knapsack
4. group knapsack
5. tree knapsack

They all share **one identical DP structure**.


# review the logic this solution

```go
// Classic Knapsack
// dp[i] = max(dp[i], dp[i-weights[i]] + values[i])
// dp[i] = max(dp[i], i > weights[i]的前提下,不要weights[i]的价值 + value[i])
func knap(weights []int, values []int, capacity int) int {
	dp := make([]int, capacity+1)
	for curr := 1; curr <= capacity; curr++ {
		for weiIdx := range weights {
			if curr >= weights[weiIdx] {
				dp[curr] = max(dp[curr], dp[curr-weights[weiIdx]]+values[weiIdx])
			}
		}
	}
	return dp[capacity]
}
```


Your code is **almost correct**, but it actually solves a **different problem than classic 0/1 knapsack**.

Let’s analyze it carefully.

---

# 1. Your Code

```go
func knap(weights []int, values []int, capacity int) int {
	dp := make([]int, capacity+1)

	for curr := 1; curr <= capacity; curr++ {
		for weiIdx := range weights {
			if curr >= weights[weiIdx] {
				dp[curr] = max(dp[curr], dp[curr-weights[weiIdx]]+values[weiIdx])
			}
		}
	}

	return dp[capacity]
}
```

DP relation used:

```
dp[curr] = max(dp[curr], dp[curr-weight[i]] + value[i])
```

---

# 2. What Problem This Actually Solves

This is **not 0/1 knapsack**.

This is:

**Unbounded Knapsack (Complete Knapsack)**

Meaning:

```
each item can be taken unlimited times
```

Why?

Because when computing:

```
dp[curr]
```

you use

```
dp[curr-weight[i]]
```

which may **already include the same item i**.

Example:

```
weight = 2
value = 3
capacity = 6
```

Your DP will do:

```
dp[2] = 3
dp[4] = dp[2] + 3 = 6
dp[6] = dp[4] + 3 = 9
```

Same item used **multiple times**.

---

# 3. Why This Happens

Your loops are:

```
for capacity
    for items
```

which allows reuse of items.

Classic **0/1 knapsack** requires:

```
for items
    for capacity backwards
```

to prevent reuse.

---

# 4. Correct 0/1 Knapsack Version

```go
func knap(weights []int, values []int, capacity int) int {
	dp := make([]int, capacity+1)

	for i := 0; i < len(weights); i++ {

		for w := capacity; w >= weights[i]; w-- {

			dp[w] = max(
				dp[w],
				dp[w-weights[i]] + values[i],
			)

		}
	}

	return dp[capacity]
}
```

Critical difference:

```
capacity loop runs backwards
```

---

# 5. Loop Order Rule (Very Important)

This is the **golden rule of knapsack DP**.

| Problem            | Loop order         |
| ------------------ | ------------------ |
| 0/1 knapsack       | items → capacity ↓ |
| unbounded knapsack | capacity → items   |
| coin change        | capacity → items   |

---

# 6. Why Your Solution Is Still Good

Your code is actually a **perfect template** for:

* coin change (max value)
* rod cutting
* complete knapsack

Example rod cutting:

```
length = weight
price  = value
```

Exact same DP.

---

# 7. Small Code Improvement

You can simplify:

```go
for _, w := range weights {
```

But you also need value index, so better:

```go
for i := range weights {
```

---

# 8. Minor Comment Correction

Your comment:

```
// dp[i] = max(dp[i], i > weights[i]的前提下,不要weights[i]的价值 + value[i])
```

Better:

```
// dp[c] = max(dp[c], dp[c-weight[i]] + value[i])
// meaning: take item i (can be used unlimited times)
```

---

# 9. Summary

Your code solves:

```
Unbounded Knapsack
```

Time complexity:

```
O(n * capacity)
```

Space:

```
O(capacity)
```

---

✅ **Interview Insight**

The easiest way to distinguish knapsack types:

| Loop Pattern       | Problem            |
| ------------------ | ------------------ |
| items → capacity ↓ | 0/1 knapsack       |
| items → capacity ↑ | unbounded knapsack |
| capacity → items   | coin change        |

Senior engineers instantly recognize the problem **just from loop order**.

---

If you'd like, I can also show the **single mental model that unifies all knapsack problems** (a trick many engineers at Google use to derive DP in seconds).
