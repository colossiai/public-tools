# in `func coinChange(coins []int, amount int) int`

why init dp with 

```    for i := 1; i <= amount; i++ {
        dp[i] = amount + 1
    }
```


## ANSWER:


In the classic **Coin Change DP**, the line

```go
for i := 1; i <= amount; i++ {
    dp[i] = amount + 1
}
```

is used to initialize the DP array with a **sentinel value representing "impossible / infinity"**.

Let's break down **why `amount + 1` is chosen**.

---

# 1️⃣ What `dp[i]` Means

Definition:

```
dp[i] = minimum number of coins needed to make amount i
```

Example:

```
coins = [1,3,4]
amount = 6
```

Goal:

```
dp[6]
```

---

# 2️⃣ Why We Need an Initial "Infinity"

When computing:

```
dp[i] = min(dp[i], dp[i-coin] + 1)
```

We want **real answers to replace the initial value**.

So the initial value must be **larger than any possible valid answer**.

---

# 3️⃣ Why `amount + 1` Works

Worst case:

```
coins = [1]
```

To make amount `N`, we need:

```
N coins
```

Example:

```
amount = 7
coins = [1]
```

Best solution:

```
7 coins
```

So the **maximum valid answer** is:

```
amount
```

Therefore we initialize with something **bigger**:

```
amount + 1
```

This acts like **∞ (infinity)**.

---

# 4️⃣ Example

```
coins = [1,3,4]
amount = 6
```

Initial dp:

```
index: 0 1 2 3 4 5 6
value: 0 7 7 7 7 7 7
```

(7 = amount+1)

Now we update.

---

### i = 1

```
dp[1] = min(7, dp[0]+1)
      = 1
```

```
0 1 7 7 7 7 7
```

---

### i = 3

```
dp[3] = min(
    dp[2]+1,
    dp[0]+1
)
```

```
min(3,1) = 1
```

---

### final

```
0 1 2 1 1 2 2
```

---

# 5️⃣ Why Not Initialize With 0?

If we did:

```
dp[i] = 0
```

Then:

```
dp[i] = min(0, dp[i-coin]+1)
```

would always stay **0**, which is wrong.

---

# 6️⃣ Why Not Use `math.MaxInt`?

You *can*, but `amount+1` is better because:

1️⃣ It's guaranteed **larger than any valid solution**
2️⃣ No **integer overflow risk** when adding `+1`
3️⃣ Slightly faster / simpler

Example danger:

```
math.MaxInt + 1  → overflow
```

---

# 7️⃣ Final Check

At the end we verify:

```go
if dp[amount] > amount {
    return -1
}
```

Meaning:

```
no valid solution found
```

Because the value never changed from **infinity**.

---

# Key DP Pattern

Many DP problems initialize with:

```
∞ for minimum problems
-∞ for maximum problems
```

Examples:

| Problem                 | Initialization |
| ----------------------- | -------------- |
| Coin change (min coins) | ∞              |
| Shortest path           | ∞              |
| Max profit              | -∞             |

---

✅ **One-line intuition**

```
amount + 1 is used as "infinity" because the answer can never exceed amount.
```

---

If you'd like, I can also show a **very powerful mental model that makes DP transitions (like `dp[i-coin] + 1`) instantly obvious**, which many senior engineers use when designing DP from scratch.
