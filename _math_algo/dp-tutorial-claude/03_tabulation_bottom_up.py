"""
03 · 表格法（Bottom-Up / 自底向上）—— 干脆从小往大算

═══════════════════════════════════════════════════════════════
【思维】把"问题"翻面，从答案的根基开始搭
═══════════════════════════════════════════════════════════════

记忆化（上一章）已经把 fib 优化到 O(n) 了。但它的写法还是**递归**：
程序栈来回跳，函数调用本身有开销，n 很大的时候还会栈溢出。

更聪明的做法是：

    "fib(n) 需要 fib(n-1) 和 fib(n-2)。
     既然如此，我**先**算 fib(2)，再算 fib(3)、fib(4) ……一路算到 fib(n)。
     算的时候，左边的答案已经在数组里等着我了。"

这就是**表格法（tabulation）**，也叫"自底向上"。

关键 mindset 转换：

    递归思维：『要算 F(n)，先算 F(n-1) 和 F(n-2)』（递推关系往下走）
    表格思维：『我手里有 F(0), F(1)，能算 F(2)；
              有 F(0..2)，能算 F(3)；……』（信息从底向上累积）

两种思维**用的是同一个递推公式**，但程序结构完全不同：
**没有递归，只有一个 for 循环**。

═══════════════════════════════════════════════════════════════
【方案】写表格法的 4 步
═══════════════════════════════════════════════════════════════

  1. **开一个数组** dp[0..n]，dp[i] 表示子问题 i 的答案。
     这一步对应"状态定义"。Fibonacci 里 dp[i] 就是 F(i)。

  2. **填初始值**（边界条件）：dp[0] = 0, dp[1] = 1。
     这些是"无法继续递归下去"的最小子问题。

  3. **决定循环顺序**：因为 dp[i] 依赖 dp[i-1] 和 dp[i-2]，
     所以 i 必须从小到大遍历。

  4. **照着转移方程填**：dp[i] = dp[i-1] + dp[i-2]。

代码：

    def fib(n):
        dp = [0] * (n + 1)
        dp[0], dp[1] = 0, 1
        for i in range(2, n + 1):
            dp[i] = dp[i - 1] + dp[i - 2]
        return dp[n]

清爽得一塌糊涂。这就是表格法的魅力。

═══════════════════════════════════════════════════════════════
【可视化】
═══════════════════════════════════════════════════════════════

生成 output/03_tabulation_filling.png：
  - 6 张子图按时间顺序排列
  - 每张子图展示 dp 数组在某一步时刻的状态
  - 当前正在填充的格子高亮黄色，已填好的格子绿色，未填的灰色
  - 让你"亲眼看到"表格是怎么从左到右长出来的

这种"逐步填表"的视觉体验，是理解 DP 最直接的方式。
"""
from __future__ import annotations

import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle

from _common import parse_plot_args, save_and_show


# ────────────────────────────────────────────────────────────
# 表格法 Fibonacci
# ────────────────────────────────────────────────────────────

def fib_tab(n: int) -> tuple[int, list[int]]:
    """返回 (F(n), 完整的 dp 数组)。dp 数组用于可视化。"""
    if n == 0:
        return 0, [0]
    dp = [0] * (n + 1)
    dp[1] = 1
    for i in range(2, n + 1):
        dp[i] = dp[i - 1] + dp[i - 2]
    return dp[n], dp


# ────────────────────────────────────────────────────────────
# 可视化：分步骤展示填表过程
# ────────────────────────────────────────────────────────────

def render_step(ax, dp: list[int], filled_until: int, current: int | None) -> None:
    """在一个子图里画一行表格（即 dp 数组当前状态）。"""
    n = len(dp) - 1
    cell_w = 1.0
    for i in range(n + 1):
        if i == current:
            color = "#f1c40f"
            text_color = "black"
        elif i <= filled_until:
            color = "#2ecc71"
            text_color = "white"
        else:
            color = "#bdc3c7"
            text_color = "#7f8c8d"
        ax.add_patch(Rectangle((i * cell_w, 0), cell_w, 1.0, facecolor=color, edgecolor="black"))
        value_text = str(dp[i]) if i <= max(filled_until, current if current is not None else -1) else "?"
        ax.text(i * cell_w + cell_w / 2, 0.5, value_text,
                ha="center", va="center", fontsize=14, color=text_color, fontweight="bold")
        ax.text(i * cell_w + cell_w / 2, -0.25, f"i={i}",
                ha="center", va="center", fontsize=9, color="#555")

    ax.set_xlim(-0.2, (n + 1) * cell_w + 0.2)
    ax.set_ylim(-0.6, 1.4)
    ax.set_aspect("equal")
    ax.axis("off")


def visualize(n: int) -> None:
    """画 (n+1) 个步骤的填表过程，每个步骤一张子图。"""
    # 重新跑一遍 DP，把每一步的"快照"存下来
    snapshots: list[tuple[list[int], int, int | None]] = []  # (dp 副本, filled_until, current)

    dp = [0] * (n + 1)
    snapshots.append((dp.copy(), 0, None))  # 初始：dp[0]=0 已填

    dp[1] = 1
    snapshots.append((dp.copy(), 1, None))  # dp[1]=1 已填

    for i in range(2, n + 1):
        # 先画"正要算 dp[i]"的那一帧
        snapshots.append((dp.copy(), i - 1, i))
        dp[i] = dp[i - 1] + dp[i - 2]

    snapshots.append((dp.copy(), n, None))  # 最终

    rows = (len(snapshots) + 1) // 2
    fig, axes = plt.subplots(rows, 2, figsize=(14, 1.6 * rows))
    axes = axes.flatten() if rows > 1 else [axes] if rows == 1 else axes

    for idx, (snap_dp, filled, current) in enumerate(snapshots):
        ax = axes[idx]
        render_step(ax, snap_dp, filled, current)
        if current is not None:
            ax.set_title(
                f"第 {idx + 1} 步：算 dp[{current}] = dp[{current-1}] + dp[{current-2}] "
                f"= {snap_dp[current-1]} + {snap_dp[current-2]} = {snap_dp[current-1] + snap_dp[current-2]}",
                fontsize=10, loc="left", color="#c0392b",
            )
        elif filled == 0:
            ax.set_title(f"第 {idx + 1} 步：初始化 dp[0] = 0", fontsize=10, loc="left")
        elif filled == 1 and idx == 1:
            ax.set_title(f"第 {idx + 1} 步：初始化 dp[1] = 1", fontsize=10, loc="left")
        else:
            ax.set_title(f"完成：dp[{filled}] = {snap_dp[filled]}", fontsize=10, loc="left", color="#27ae60")

    # 把多余的空子图隐藏
    for j in range(len(snapshots), len(axes)):
        axes[j].axis("off")

    fig.suptitle(
        f"自底向上填表：从小到大算出 fib({n})\n"
        "🟢 (GREEN)已填  🟡 (YELLOW)当前正在算  ⬜ (GREY)尚未填",
        fontsize=13,
    )
    plt.tight_layout()
    save_and_show(f"03_tabulation_fib{n}.png")


# ────────────────────────────────────────────────────────────
# 主程序
# ────────────────────────────────────────────────────────────

def main() -> None:
    parse_plot_args()
    print("=" * 60)
    print("第 03 章：表格法（Bottom-Up）")
    print("=" * 60)

    for n in (6, 10, 20):
        result, dp = fib_tab(n)
        print(f"\nfib_tab({n}) = {result}")
        print(f"  dp 数组 = {dp}")

    print(
        "\n→ 没有递归，没有缓存命中判断，就是一个 for 循环。\n"
        "→ 这就是表格法（自底向上）。代码更短，速度也更快"
        "（省掉了函数调用栈的开销）。\n"
    )

    print("生成 fib(6) 的逐步填表图...")
    visualize(6)


if __name__ == "__main__":
    main()
