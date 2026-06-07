"""
06 · 线性 DP —— 凑硬币（最少硬币数）

═══════════════════════════════════════════════════════════════
【题目】
═══════════════════════════════════════════════════════════════

给你几种面值的硬币（每种数量无限），目标金额 amount，问最少用几枚
硬币能凑出 amount。如果凑不出来，返回 -1。

例子：

    coins = [1, 3, 4]
    amount = 6
    答案 = 2     （3 + 3）

═══════════════════════════════════════════════════════════════
【思维】先想暴力解，再想"我能记下什么"
═══════════════════════════════════════════════════════════════

新手最自然的思路：

  "嗯……贪心？每次选最大的硬币，4 + 1 + 1 = 3 枚？"

错了。最优是 3 + 3 = 2 枚。**贪心在这题失效**——这是 DP 的经典信号：
"局部最优不一定是全局最优"。

那暴力怎么写？

  「要凑 amount，我枚举第一枚选什么硬币：
   选 1 → 剩下凑 amount-1；
   选 3 → 剩下凑 amount-3；
   选 4 → 剩下凑 amount-4。
   答案 = 三个子问题最优答案 + 1（加上"第一枚"自己）。」

这是个递归。但你会发现：

  - 凑 amount-1，里面又会枚举凑 amount-1-1, amount-1-3...
  - 凑 amount-3，里面又会枚举凑 amount-3-1, amount-3-3...

**子问题大量重复**。又是 DP 的经典信号。

═══════════════════════════════════════════════════════════════
【方案】四步法套用
═══════════════════════════════════════════════════════════════

1️⃣ **定义状态**

    dp[x] = 凑出金额 x 所需的最少硬币数

2️⃣ **状态转移方程**

   要凑出 x，看"最后一枚硬币"选什么。如果选了面值 c：

    dp[x] = dp[x - c] + 1     （其中 c 遍历所有可用面值，且 x ≥ c）

   多种选择里取最小：

    dp[x] = min(dp[x - c] + 1)     for c in coins, c ≤ x

3️⃣ **边界**

    dp[0] = 0     （凑出金额 0，需要 0 枚硬币）

   其余 dp[x] 初始化成一个"哨兵值"（不可能达到的大数），
   习惯上用 amount + 1，因为最坏情况也不会用超过 amount 枚硬币
   （都用面值 1 的硬币凑也才 amount 枚）。

4️⃣ **计算顺序**

    x 从 1 到 amount，从小到大。
    （要算 dp[x] 时，所有 dp[x - c] 都已经在 x 之前算完。）

═══════════════════════════════════════════════════════════════
【最后判断是否有解】
═══════════════════════════════════════════════════════════════

如果 dp[amount] 还停留在哨兵值（amount + 1），说明根本凑不出来，返回 -1。

═══════════════════════════════════════════════════════════════
【可视化】
═══════════════════════════════════════════════════════════════

生成 output/06_coin_change.png：
  - 柱状图：横轴 x = 0..amount，纵轴是 dp[x]
  - 每根柱子顶部标注：dp[x] 是从 dp[x-c] 转移来的（c 是用的最后一枚硬币）
  - 用不同颜色箭头把 dp[x-c] → dp[x] 连起来
"""
from __future__ import annotations

import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch

from _common import parse_plot_args, save_and_show


# ────────────────────────────────────────────────────────────
# DP 解法
# ────────────────────────────────────────────────────────────

def coin_change(coins: list[int], amount: int) -> tuple[int, list[int], list[int]]:
    """返回 (最少硬币数 或 -1, dp 数组, 每个状态选用的"最后一枚"硬币面值)。

    last[x] 用于回溯和可视化：dp[x] 是通过用 last[x] 这枚硬币、
    从 dp[x - last[x]] 转移来的。
    """
    INF = amount + 1
    dp = [INF] * (amount + 1)
    last = [0] * (amount + 1)
    dp[0] = 0

    for x in range(1, amount + 1):
        for c in coins:
            if c <= x and dp[x - c] + 1 < dp[x]:
                dp[x] = dp[x - c] + 1
                last[x] = c

    return (dp[amount] if dp[amount] <= amount else -1), dp, last


def reconstruct(amount: int, last: list[int]) -> list[int]:
    """根据 last 数组回溯出具体用了哪些硬币。"""
    result = []
    x = amount
    while x > 0 and last[x] > 0:
        result.append(last[x])
        x -= last[x]
    return result


# ────────────────────────────────────────────────────────────
# 可视化
# ────────────────────────────────────────────────────────────

def visualize(coins: list[int], amount: int) -> None:
    INF = amount + 1
    _, dp, last = coin_change(coins, amount)

    fig, ax = plt.subplots(figsize=(max(10, amount * 0.9), 7))

    # 柱状图
    xs = list(range(amount + 1))
    heights = [v if v < INF else 0 for v in dp]
    bar_colors = ["#bdc3c7" if v >= INF else "#3498db" for v in dp]
    ax.bar(xs, heights, color=bar_colors, edgecolor="black")

    for x, v in enumerate(dp):
        ax.text(x, max(heights) * 0.05 + (v if v < INF else 0) + 0.15, str(v if v < INF else "∞"),
                ha="center", fontsize=11, fontweight="bold")
        if x > 0 and v < INF:
            ax.text(x, -max(heights) * 0.12, f"用 {last[x]}",
                    ha="center", fontsize=8, color="#c0392b")

    # 转移箭头：dp[x - last[x]] → dp[x]
    coin_colors = {c: col for c, col in zip(coins, ["#e74c3c", "#27ae60", "#9b59b6", "#f39c12", "#16a085"])}
    for x in range(1, amount + 1):
        if dp[x] >= INF:
            continue
        c = last[x]
        x_from = x - c
        arrow = FancyArrowPatch(
            (x_from, dp[x_from] + 0.3),
            (x, dp[x] + 0.3),
            arrowstyle="->", mutation_scale=14,
            color=coin_colors.get(c, "#7f8c8d"),
            connectionstyle="arc3,rad=-0.5",
            linewidth=1.4,
            alpha=0.7,
        )
        ax.add_patch(arrow)

    ax.set_xticks(xs)
    ax.set_xlabel("金额 x")
    ax.set_ylabel("dp[x] = 凑出金额 x 所需的最少硬币数")
    ax.set_title(
        f"凑硬币 DP（coins={coins}, amount={amount}）\n"
        f"箭头：dp[x] = dp[x − c] + 1 中那枚 c 的来源；"
        f"不同颜色 = 不同面值",
        fontsize=12,
    )
    ax.set_ylim(-max(heights) * 0.25, max(heights) * 1.4)
    ax.grid(axis="y", alpha=0.3)

    # 图例
    handles = [plt.Line2D([0], [0], color=col, lw=2, label=f"硬币 {c}") for c, col in coin_colors.items() if c in coins]
    ax.legend(handles=handles, loc="upper left")

    plt.tight_layout()
    save_and_show(f"06_coin_change_{amount}.png")


# ────────────────────────────────────────────────────────────
# 主程序
# ────────────────────────────────────────────────────────────

def main() -> None:
    parse_plot_args()
    print("=" * 60)
    print("第 06 章：线性 DP — 凑硬币")
    print("=" * 60)

    test_cases = [
        ([1, 3, 4], 6),
        ([2, 5, 10], 27),
        ([2], 3),  # 凑不出来
    ]

    for coins, amount in test_cases:
        ans, dp, last = coin_change(coins, amount)
        path = reconstruct(amount, last) if ans != -1 else []
        print(f"\ncoins={coins}, amount={amount}")
        print(f"  最少硬币数 = {ans}")
        if ans != -1:
            print(f"  具体方案   = {' + '.join(map(str, path))}")
        print(f"  dp 数组    = {dp}")

    print("\n生成 coins=[1,3,4], amount=11 的 dp 表 + 转移箭头图...")
    visualize([1, 3, 4], 11)


if __name__ == "__main__":
    main()
