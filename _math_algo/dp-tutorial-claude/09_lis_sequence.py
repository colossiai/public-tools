"""
09 · 序列 DP —— 最长上升子序列（LIS）

═══════════════════════════════════════════════════════════════
【题目】
═══════════════════════════════════════════════════════════════

给一个数组 nums，找出其中**最长的严格上升子序列**的长度。

  - "子序列"：从原数组里挑出一些元素，**保持相对顺序**，但**不要求连续**。
  - "严格上升"：后一个数 > 前一个数。

例子：

    nums = [10, 9, 2, 5, 3, 7, 101, 18]
    最长上升子序列之一：[2, 3, 7, 101]   长度 = 4
                       或 [2, 3, 7, 18]  长度 = 4

═══════════════════════════════════════════════════════════════
【思维】序列 DP 的关键决策：状态以"以谁结尾"为锚
═══════════════════════════════════════════════════════════════

最容易踩坑的状态定义：

    ❌ dp[i] = nums[0..i] 中最长上升子序列的长度

   为什么不行？因为只知道"长度"，下次要往后接的时候，
   你**根本不知道这条最长子序列结尾是几**——而它能不能接上下一个数，
   完全取决于结尾值。状态没存够信息，转移转不动。

正确的做法是**让"结尾"成为状态的一部分**：

    ✅ dp[i] = 必须以 nums[i] 作为最后一个元素的、最长上升子序列的长度

注意"必须以 nums[i] 结尾"这个约束。这是序列 DP 最常见的状态设计：
**强制把当前元素钉在最后，让转移变得清晰**。

═══════════════════════════════════════════════════════════════
【方案】四步法
═══════════════════════════════════════════════════════════════

1️⃣ **定义状态**

    dp[i] = 以 nums[i] 结尾的最长上升子序列长度

2️⃣ **转移方程**

   要让 nums[i] 接在某个上升子序列后面，那个子序列的**最后一个数**
   必须**严格小于** nums[i]：

    dp[i] = max(dp[j] + 1)     for all j < i, nums[j] < nums[i]

   如果找不到任何这样的 j，nums[i] 只能"自己一个人"成为长度 1 的序列：

    dp[i] = 1     （初始默认值）

3️⃣ **边界**

    dp[i] 初始全部为 1（每个元素自己就是长度 1 的上升子序列）。

4️⃣ **计算顺序**

   i 从 0 到 n-1。算 dp[i] 时要枚举所有 j < i，所以也是单调向前。

最终答案：

    LIS 长度 = max(dp[0], dp[1], ..., dp[n-1])

   注意**不是** dp[n-1]——LIS 可以以任何位置结尾。

═══════════════════════════════════════════════════════════════
【O(n²) → O(n log n) 的简单一提】
═══════════════════════════════════════════════════════════════

本章给的是经典 O(n²) DP，是面试基础款。还有一个 O(n log n) 的
"贪心 + 二分"解法，思路完全不同（维护一个"长度 k 的上升子序列最小末尾值"
数组，二分插入）。本教程不展开，但你**值得在掌握基础之后去研究**——
它能让你看到"DP 不是唯一通路"的事实。

═══════════════════════════════════════════════════════════════
【可视化】
═══════════════════════════════════════════════════════════════

生成 output/09_lis.png：
  - 上半图：nums 数组以柱状图展示，柱子高度 = 元素值，
    标注 dp[i]
  - 下半图：把最长上升子序列的元素用红色连线 highlight 出来
  - 用箭头标出每个 dp[i] 是从哪个 dp[j] 转移来的（前驱关系）
"""
from __future__ import annotations

import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch

from _common import parse_plot_args, save_and_show


# ────────────────────────────────────────────────────────────
# DP 解法
# ────────────────────────────────────────────────────────────

def lis(nums: list[int]) -> tuple[int, list[int], list[int], list[int]]:
    """返回 (LIS 长度, dp 数组, prev 前驱数组, LIS 元素下标列表)。"""
    n = len(nums)
    dp = [1] * n
    prev = [-1] * n

    for i in range(n):
        for j in range(i):
            if nums[j] < nums[i] and dp[j] + 1 > dp[i]:
                dp[i] = dp[j] + 1
                prev[i] = j

    # 回溯：从最大 dp 值的位置开始
    best_end = max(range(n), key=lambda k: dp[k])
    path: list[int] = []
    k = best_end
    while k != -1:
        path.append(k)
        k = prev[k]
    path.reverse()

    return dp[best_end], dp, prev, path


# ────────────────────────────────────────────────────────────
# 可视化
# ────────────────────────────────────────────────────────────

def visualize(nums: list[int]) -> None:
    length, dp, prev, path = lis(nums)
    n = len(nums)

    fig, ax = plt.subplots(figsize=(max(12, n * 1.0), 7))

    # 柱状图：每个元素的值
    in_path = set(path)
    bar_colors = ["#e74c3c" if i in in_path else "#3498db" for i in range(n)]
    ax.bar(range(n), nums, color=bar_colors, edgecolor="black", zorder=2)

    for i, v in enumerate(nums):
        # 值标注
        ax.text(i, v + max(nums) * 0.03, str(v),
                ha="center", fontsize=10, fontweight="bold")
        # dp 标注
        ax.text(i, -max(nums) * 0.08, f"dp={dp[i]}",
                ha="center", fontsize=10, color="#c0392b")
        ax.text(i, -max(nums) * 0.18, f"idx={i}",
                ha="center", fontsize=8, color="#555")

    # LIS 路径用红色连线（在柱顶画出）
    for k in range(1, len(path)):
        x0, x1 = path[k - 1], path[k]
        ax.add_patch(FancyArrowPatch(
            (x0, nums[x0]), (x1, nums[x1]),
            arrowstyle="-|>", mutation_scale=18,
            color="#c0392b", linewidth=2.5,
            connectionstyle="arc3,rad=-0.15",
            zorder=3,
        ))

    # 前驱关系箭头（淡灰色，纯粹展示 dp 之间的依赖）
    for i in range(n):
        if prev[i] != -1:
            ax.add_patch(FancyArrowPatch(
                (prev[i], -max(nums) * 0.05),
                (i, -max(nums) * 0.05),
                arrowstyle="->", mutation_scale=10,
                color="#7f8c8d", linewidth=0.8,
                connectionstyle="arc3,rad=0.5",
                alpha=0.5,
                zorder=1,
            ))

    ax.set_xlim(-0.5, n - 0.5)
    ax.set_xticks(range(n))
    ax.set_ylim(-max(nums) * 0.3, max(nums) * 1.2)
    ax.set_ylabel("nums[i]")
    ax.set_title(
        f"最长上升子序列（LIS）  长度 = {length}\n"
        f"红色柱 + 红色箭头：LIS 之一 = {[nums[k] for k in path]}\n"
        f"灰色弧：dp[i] 由哪个 dp[j] 转移而来",
        fontsize=12,
    )
    plt.grid(axis="y", alpha=0.3)

    plt.tight_layout()
    save_and_show(f"09_lis_n{n}.png")


# ────────────────────────────────────────────────────────────
# 主程序
# ────────────────────────────────────────────────────────────

def main() -> None:
    parse_plot_args()
    print("=" * 60)
    print("第 09 章：序列 DP — 最长上升子序列（LIS）")
    print("=" * 60)

    test_cases = [
        [10, 9, 2, 5, 3, 7, 101, 18],
        [0, 1, 0, 3, 2, 3],
        [7, 7, 7, 7, 7, 7, 7],
        [1, 3, 6, 7, 9, 4, 10, 5, 6],
    ]

    for nums in test_cases:
        length, dp, _, path = lis(nums)
        print(f"\nnums = {nums}")
        print(f"  dp   = {dp}")
        print(f"  LIS  = {[nums[k] for k in path]}   长度 = {length}")

    print("\n生成可视化图...")
    visualize([1, 3, 6, 7, 9, 4, 10, 5, 6])


if __name__ == "__main__":
    main()
