"""
08 · 背包 DP —— 0/1 背包（DP 模式之王）

═══════════════════════════════════════════════════════════════
【题目】
═══════════════════════════════════════════════════════════════

你有一个容量为 W 的背包，和 n 件物品。第 i 件物品的重量是 w[i]，
价值是 v[i]。每件物品**最多只能拿一次**（要么拿要么不拿，所以叫"0/1"）。

问：在背包不超重的前提下，能装出的**最大总价值**是多少？

例子：

    物品   重量  价值
     A      1     1
     B      3     4
     C      4     5
     D      5     7
    背包容量 W = 7

    最优：B + C   重量 = 3+4 = 7   价值 = 4+5 = 9   ⭐

═══════════════════════════════════════════════════════════════
【思维】为什么 0/1 背包是"DP 模式之王"？
═══════════════════════════════════════════════════════════════

非常多 DP 题，本质上都在问：

  "**每件物品 / 每个数 / 每个字符，我要不要选？**"

  - 子集和（能不能凑出和 S）→ 每个数选 / 不选
  - 分割等和子集 → 每个数分到 A 堆 / B 堆
  - 目标和（给每个数加正负号求和 = target）→ 每个数当正 / 当负
  - 组合数限制下的最大收益 → 每个选项要 / 不要

**只要遇到"每个东西二选一"，先想 0/1 背包。**

═══════════════════════════════════════════════════════════════
【方案】四步法
═══════════════════════════════════════════════════════════════

1️⃣ **定义状态**

   关键决策：状态需要**两个维度**才描述得清楚——
   "我考虑到第几件物品" + "目前背包还剩多少容量"。

    dp[i][c] = 只考虑前 i 件物品、背包容量为 c 时能装出的最大价值

   注意 i 是"前几件"，从 0 到 n；c 是"容量"，从 0 到 W。

2️⃣ **转移方程**

   对第 i 件物品（下标从 1 开始），**只有两种决策**：

   - **不拿**：dp[i][c] = dp[i-1][c]
     （和"只考虑前 i-1 件物品"完全一样的局面）

   - **拿**（前提：c ≥ w[i]）：
     dp[i][c] = dp[i-1][c - w[i]] + v[i]
     （先腾出 w[i] 容量装第 i 件物品，剩余 c - w[i] 容量交给前 i-1 件物品去打算盘，
      最后加上第 i 件物品自带的 v[i] 价值）

   取两种决策的较大者：

    dp[i][c] = max(
        dp[i-1][c],                            # 不拿
        dp[i-1][c - w[i]] + v[i]               # 拿（c ≥ w[i] 时）
    )

3️⃣ **边界**

    dp[0][c] = 0     for all c       (一件物品都没考虑过，价值为 0)

4️⃣ **计算顺序**

   外层枚举 i（1 → n），内层枚举 c（0 → W）。
   dp[i][c] 只依赖 dp[i-1][*]（上一行），所以这个顺序天然正确。

═══════════════════════════════════════════════════════════════
【回溯具体选了哪些物品】
═══════════════════════════════════════════════════════════════

跑完 DP 拿到最大价值不够，面试常问"具体拿了哪几件？"。回溯方法：

   从 dp[n][W] 倒着推：
   - 如果 dp[i][c] == dp[i-1][c]，说明第 i 件没拿。i 减 1。
   - 否则，说明第 i 件拿了。记录下来，i 减 1，c 减 w[i]。

═══════════════════════════════════════════════════════════════
【空间优化（顺带提一句）】
═══════════════════════════════════════════════════════════════

dp[i][c] 只用到 dp[i-1][*]，所以可以压缩成一维：

    for i in range(1, n + 1):
        for c in range(W, w[i] - 1, -1):       # ⚠️ 注意：必须倒序
            dp[c] = max(dp[c], dp[c - w[i]] + v[i])

为什么要倒序？正序的话，dp[c - w[i]] 已经是"本轮新值"（相当于这件
物品被拿了不止一次），就变成完全背包了。**倒序就是 0/1 背包，正序就是
完全背包**——这是面试常考的"魔鬼细节"。

═══════════════════════════════════════════════════════════════
【可视化】
═══════════════════════════════════════════════════════════════

生成 output/08_knapsack_table.png：
  - 二维 DP 表热力图（行 = 物品 0..n，列 = 容量 0..W）
  - 每格标注 dp 值
  - 用红色框出最优解的回溯路径（最终 dp[n][W] 是怎么一步步来的）
"""
from __future__ import annotations

import matplotlib.pyplot as plt
import numpy as np

from _common import parse_plot_args, save_and_show


# ────────────────────────────────────────────────────────────
# DP 解法
# ────────────────────────────────────────────────────────────

def knapsack_01(weights: list[int], values: list[int], capacity: int
                ) -> tuple[int, list[list[int]], list[int]]:
    """返回 (最大价值, 完整 dp 表, 选中物品下标列表)。"""
    n = len(weights)
    dp = [[0] * (capacity + 1) for _ in range(n + 1)]

    for i in range(1, n + 1):
        w, v = weights[i - 1], values[i - 1]
        for c in range(capacity + 1):
            dp[i][c] = dp[i - 1][c]  # 不拿
            if c >= w:
                dp[i][c] = max(dp[i][c], dp[i - 1][c - w] + v)  # 拿 vs 不拿

    # 回溯
    chosen = []
    i, c = n, capacity
    while i > 0:
        if dp[i][c] != dp[i - 1][c]:
            chosen.append(i - 1)  # 第 i 件物品（0-indexed: i-1）被选了
            c -= weights[i - 1]
        i -= 1
    chosen.reverse()

    return dp[n][capacity], dp, chosen


# ────────────────────────────────────────────────────────────
# 可视化
# ────────────────────────────────────────────────────────────

def visualize(weights: list[int], values: list[int], capacity: int,
              item_names: list[str]) -> None:
    n = len(weights)
    best, dp, chosen = knapsack_01(weights, values, capacity)
    arr = np.array(dp)

    fig, ax = plt.subplots(figsize=(max(10, capacity * 0.9), max(6, (n + 1) * 0.7)))
    im = ax.imshow(arr, cmap="Blues", aspect="equal")
    fig.colorbar(im, ax=ax, fraction=0.03, pad=0.04, label="dp[i][c]")

    for i in range(n + 1):
        for c in range(capacity + 1):
            ax.text(c, i, str(arr[i, c]),
                    ha="center", va="center", fontsize=10,
                    color="white" if arr[i, c] > arr.max() / 2 else "black")

    # 回溯路径用红框圈出
    path_cells: list[tuple[int, int]] = []
    i, c = n, capacity
    while i > 0:
        path_cells.append((i, c))
        if dp[i][c] != dp[i - 1][c]:
            c -= weights[i - 1]
        i -= 1
    path_cells.append((0, c))

    for (i_, c_) in path_cells:
        ax.add_patch(plt.Rectangle((c_ - 0.5, i_ - 0.5), 1, 1,
                                   fill=False, edgecolor="#e74c3c", linewidth=3))

    # 行标签：物品名 + 重量价值
    yticks = list(range(n + 1))
    ylabels = ["(无物品)"] + [f"{item_names[i]} (w={weights[i]}, v={values[i]})" for i in range(n)]
    ax.set_yticks(yticks)
    ax.set_yticklabels(ylabels)

    ax.set_xticks(range(capacity + 1))
    ax.set_xticklabels([f"c={c}" for c in range(capacity + 1)])
    ax.set_xlabel("背包剩余容量 c")
    ax.set_ylabel("已考虑的物品（前 i 件）")
    chosen_names = ", ".join(item_names[k] for k in chosen)
    ax.set_title(
        f"0/1 背包 DP 表（n={n}, W={capacity}）  最大价值 = {best}\n"
        f"红框：回溯出的最优解路径   ｜   选中物品 = {{ {chosen_names} }}",
        fontsize=12,
    )

    plt.tight_layout()
    save_and_show(f"08_knapsack_W{capacity}.png")


# ────────────────────────────────────────────────────────────
# 主程序
# ────────────────────────────────────────────────────────────

def main() -> None:
    parse_plot_args()
    print("=" * 60)
    print("第 08 章：0/1 背包（DP 模式之王）")
    print("=" * 60)

    weights = [1, 3, 4, 5]
    values = [1, 4, 5, 7]
    names = ["A", "B", "C", "D"]
    capacity = 7

    print(f"\n物品：")
    for n_, w, v in zip(names, weights, values):
        print(f"  {n_}  重 {w}  值 {v}")
    print(f"背包容量 W = {capacity}")

    best, dp, chosen = knapsack_01(weights, values, capacity)
    print(f"\n最大价值 = {best}")
    print(f"选中物品 = {[names[k] for k in chosen]}")

    print(f"\n完整 dp 表（行 = 前 i 件，列 = 容量 c）：")
    print("       " + "  ".join(f"c={c}" for c in range(capacity + 1)))
    for i, row in enumerate(dp):
        label = "i=0" if i == 0 else f"i={i}({names[i-1]})"
        print(f"  {label:<8}" + "  ".join(f"{v:>3}" for v in row))

    print("\n生成 DP 表热力图 + 回溯路径...")
    visualize(weights, values, capacity, names)


if __name__ == "__main__":
    main()
