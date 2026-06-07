"""
05 · DP 设计四步法 —— 拿到一道新题，怎么从零想清楚

═══════════════════════════════════════════════════════════════
【思维】DP 是一种"思考方式"，不是一组模板代码
═══════════════════════════════════════════════════════════════

新手最常见的痛苦：

  "我能看懂别人写好的 DP 解法。
   但下次遇到新题，我怎么也想不到要这样定义状态。"

这种"想不到"，其实是没有套路化的**思考流程**。资深选手脑子里跑的
是同一套四步法，只是熟到秒回。本章把这套四步法显式化。

═══════════════════════════════════════════════════════════════
【方案】DP 四步法
═══════════════════════════════════════════════════════════════

  ┌───────────────────────────────┐
  │ 1️⃣  定义状态                  │ ←── 最难、最关键、决定一切
  │     dp[...] 表示什么含义？    │
  └───────────────┬───────────────┘
                  │
  ┌───────────────▼───────────────┐
  │ 2️⃣  找状态转移方程            │
  │     dp[i] 怎么由更小的状态推出│
  └───────────────┬───────────────┘
                  │
  ┌───────────────▼───────────────┐
  │ 3️⃣  确定边界 / 初始条件        │
  │     最小子问题的答案是什么？  │
  └───────────────┬───────────────┘
                  │
  ┌───────────────▼───────────────┐
  │ 4️⃣  确定计算顺序              │
  │     为了让 dp[i] 用到的子状态 │
  │     先被算好，i 该怎么遍历？  │
  └───────────────────────────────┘

═══════════════════════════════════════════════════════════════
【一道小题贯穿四步：爬楼梯】
═══════════════════════════════════════════════════════════════

题目：有 n 级楼梯，每次可以爬 1 级或 2 级，问爬到顶有多少种走法。

────────────────────────────────────────────────────────────
1️⃣ 定义状态
────────────────────────────────────────────────────────────

让我们**慢慢推**这一步——这是最难的，多数新手卡在这里。

第一反应可能是："dp 表示什么？……不知道。"

技巧：**直接照搬题目最后问什么，把它的"前 i 个"版本当成状态**。

题目问"爬到第 n 级的走法数"，那就：

    dp[i] = 爬到第 i 级楼梯总共有几种走法

注意状态定义里**有变量 i**——这才是"状态"。一个数字是结果，不是状态。

────────────────────────────────────────────────────────────
2️⃣ 找状态转移方程
────────────────────────────────────────────────────────────

问自己："要走到第 i 级，**最后一步**怎么走的？"

只有两种可能：

  - 从第 i-1 级爬 1 步上来 → 前面那些走法贡献 dp[i-1] 种
  - 从第 i-2 级爬 2 步上来 → 前面那些走法贡献 dp[i-2] 种

两种情况**互不重叠**（最后一步是 1 还是 2，决定了情况，不会同时发生），
所以加起来：

    dp[i] = dp[i-1] + dp[i-2]

🤯 等等……这不就是斐波那契吗？！

是的。**爬楼梯的本质就是斐波那契。** 这就是 DP 的精妙：
看似不同的问题，状态定义对了，转移方程就一样。

────────────────────────────────────────────────────────────
3️⃣ 确定边界
────────────────────────────────────────────────────────────

  - dp[0] = 1：站在起点（第 0 级），有 1 种"走法"（什么都不做）。
    ⚠️ 这里特别容易写错成 0。想清楚定义：dp[0] 是"到达第 0 级的方案数"。
  - dp[1] = 1：第 1 级只能从地面走 1 步上来，1 种走法。

────────────────────────────────────────────────────────────
4️⃣ 确定计算顺序
────────────────────────────────────────────────────────────

转移方程里 dp[i] 依赖 dp[i-1] 和 dp[i-2]，所以 i 必须从小到大遍历：

    for i in range(2, n + 1):
        dp[i] = dp[i - 1] + dp[i - 2]

═══════════════════════════════════════════════════════════════
【验证 vs 暴力解】
═══════════════════════════════════════════════════════════════

四步法走完，代码已经出来。但状态定义对不对、转移方程漏没漏情况，
**新手最好用暴力解对拍验证**——也就是 DFS 枚举所有走法，看答案是否一致。

这是 DP 学习初期最有用的训练：**写完 DP，跑一遍暴力对拍**。

═══════════════════════════════════════════════════════════════
【可视化】
═══════════════════════════════════════════════════════════════

生成 output/05_dp_template.png：
  - 左图：DP 四步法流程图
  - 右图：dp 数组逐格填充 + 每格标注"由 dp[i-1] 和 dp[i-2] 相加得到"
"""
from __future__ import annotations

import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch, Rectangle

from _common import parse_plot_args, save_and_show


# ────────────────────────────────────────────────────────────
# 爬楼梯：暴力 vs DP
# ────────────────────────────────────────────────────────────

def climb_brute(n: int) -> int:
    """暴力 DFS 枚举所有走法。用于对拍。指数复杂度，n 别给太大。"""
    if n == 0:
        return 1
    if n < 0:
        return 0
    return climb_brute(n - 1) + climb_brute(n - 2)


def climb_dp(n: int) -> tuple[int, list[int]]:
    """四步法直接写出。"""
    dp = [0] * (n + 1)
    dp[0] = 1
    if n >= 1:
        dp[1] = 1
    for i in range(2, n + 1):
        dp[i] = dp[i - 1] + dp[i - 2]
    return dp[n], dp


# ────────────────────────────────────────────────────────────
# 可视化
# ────────────────────────────────────────────────────────────

def draw_template_flow(ax) -> None:
    """画 DP 四步法流程图。"""
    steps = [
        ("1️⃣  定义状态", "dp[i] 表示什么？\n（最难、决定一切）", "#e74c3c"),
        ("2️⃣  状态转移方程", "dp[i] = ?\n（看『最后一步』怎么走）", "#e67e22"),
        ("3️⃣  边界条件", "最小子问题的 dp 值\n（dp[0]、dp[1]）", "#f1c40f"),
        ("4️⃣  计算顺序", "怎么遍历 i，\n才能让依赖的子状态已就绪？", "#2ecc71"),
    ]
    box_w, box_h = 4.0, 1.2
    x_center = 2.5
    y_top = 6.0
    gap = 0.6

    centers = []
    for idx, (title, body, color) in enumerate(steps):
        y_top_this = y_top - idx * (box_h + gap)
        y_bottom = y_top_this - box_h
        box = FancyBboxPatch(
            (x_center - box_w / 2, y_bottom),
            box_w, box_h,
            boxstyle="round,pad=0.1",
            facecolor=color,
            edgecolor="black",
            alpha=0.85,
        )
        ax.add_patch(box)
        ax.text(x_center, y_top_this - 0.3, title, ha="center", va="top",
                fontsize=12, fontweight="bold", color="white")
        ax.text(x_center, y_top_this - 0.75, body, ha="center", va="top",
                fontsize=9, color="white")
        centers.append((x_center, y_top_this - box_h / 2))

    # 箭头
    for i in range(len(steps) - 1):
        a = (centers[i][0], centers[i][1] - box_h / 2)
        b = (centers[i + 1][0], centers[i + 1][1] + box_h / 2)
        ax.add_patch(FancyArrowPatch(a, b, arrowstyle="->", mutation_scale=18,
                                     color="black", linewidth=1.5))

    ax.set_xlim(0, 5)
    ax.set_ylim(-0.5, 6.5)
    ax.set_aspect("equal")
    ax.axis("off")
    ax.set_title("DP 设计四步法", fontsize=13)


def draw_climb_filling(ax, n: int) -> None:
    """画爬楼梯的 dp 数组，并在每格上方标注来源。"""
    _, dp = climb_dp(n)
    cell_w = 1.2
    for i, v in enumerate(dp):
        ax.add_patch(Rectangle((i * cell_w, 0), cell_w, 1.0,
                               facecolor="#3498db", edgecolor="black"))
        ax.text(i * cell_w + cell_w / 2, 0.5, str(v),
                ha="center", va="center", fontsize=14, color="white", fontweight="bold")
        ax.text(i * cell_w + cell_w / 2, -0.3, f"dp[{i}]",
                ha="center", va="center", fontsize=9, color="#555")
        if i >= 2:
            ax.text(i * cell_w + cell_w / 2, 1.3,
                    f"= dp[{i-1}]+dp[{i-2}]\n= {dp[i-1]}+{dp[i-2]}",
                    ha="center", va="center", fontsize=8, color="#c0392b")

    # 画 i ≥ 2 时来源箭头：dp[i-1] → dp[i] 和 dp[i-2] → dp[i]
    for i in range(2, len(dp)):
        # dp[i-1] → dp[i]
        x_from = (i - 1) * cell_w + cell_w / 2
        x_to = i * cell_w + cell_w / 2
        ax.add_patch(FancyArrowPatch(
            (x_from, 1.05), (x_to, 1.05),
            arrowstyle="->", mutation_scale=12, color="#16a085",
            connectionstyle="arc3,rad=-0.6", linewidth=1.2,
        ))
        # dp[i-2] → dp[i]
        x_from2 = (i - 2) * cell_w + cell_w / 2
        ax.add_patch(FancyArrowPatch(
            (x_from2, 1.05), (x_to, 1.05),
            arrowstyle="->", mutation_scale=12, color="#8e44ad",
            connectionstyle="arc3,rad=-0.8", linewidth=1.2,
        ))

    ax.set_xlim(-0.3, len(dp) * cell_w + 0.3)
    ax.set_ylim(-1.0, 2.5)
    ax.set_aspect("equal")
    ax.axis("off")
    ax.set_title(f"爬楼梯 dp 数组（n={n}）：每格 = 前两格之和", fontsize=12)


def visualize(n: int = 7) -> None:
    fig, axes = plt.subplots(1, 2, figsize=(16, 7), gridspec_kw={"width_ratios": [1, 2]})
    draw_template_flow(axes[0])
    draw_climb_filling(axes[1], n)
    fig.suptitle("DP 思维模板：用『爬楼梯』演示四步法落地", fontsize=14)
    plt.tight_layout()
    save_and_show(f"05_dp_template_climb{n}.png")


# ────────────────────────────────────────────────────────────
# 主程序
# ────────────────────────────────────────────────────────────

def main() -> None:
    parse_plot_args()
    print("=" * 60)
    print("第 05 章：DP 四步法（用爬楼梯演示）")
    print("=" * 60)

    print("\n── 对拍：暴力解 vs DP 解 ──")
    for n in range(0, 11):
        brute = climb_brute(n)
        dp_result, _ = climb_dp(n)
        ok = "✓" if brute == dp_result else "✗"
        print(f"n = {n:>2}   暴力 = {brute:>4}   DP = {dp_result:>4}   {ok}")

    print("\n── 状态表（n = 10）──")
    _, dp = climb_dp(10)
    for i, v in enumerate(dp):
        line = f"dp[{i}] = {v}"
        if i >= 2:
            line += f"   ← dp[{i-1}] + dp[{i-2}] = {dp[i-1]} + {dp[i-2]}"
        print(line)

    print("\n生成四步法流程图 + 填表图...")
    visualize(7)


if __name__ == "__main__":
    main()
