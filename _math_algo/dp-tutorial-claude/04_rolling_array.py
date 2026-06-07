"""
04 · 滚动数组 —— 大部分时候你只需要"最近两格"

═══════════════════════════════════════════════════════════════
【思维】观察 dp 数组的"实际使用范围"
═══════════════════════════════════════════════════════════════

我们已经把 fib 优化到 O(n) 时间、O(n) 空间了。看起来很完美？

仔细看上一章的表格法循环：

    for i in range(2, n + 1):
        dp[i] = dp[i - 1] + dp[i - 2]

**算 dp[i] 时，我们只用了 dp[i-1] 和 dp[i-2] 这两个值。**

那 dp[0], dp[1], ..., dp[i-3] 留着干嘛？没用了！

如果不需要保留中间过程（很多 DP 问题都是这样，最后只问"最终答案"），
我们完全可以**只保留最近 2 个值**，把空间从 O(n) 压到 O(1)。

═══════════════════════════════════════════════════════════════
【方案】两个变量轮流"滚"
═══════════════════════════════════════════════════════════════

把 dp 数组退化成两个变量：

    a = dp[i-2]      # "前前一格"
    b = dp[i-1]      # "前一格"

每一轮循环：

    new = a + b      # 当前 dp[i]
    a = b            # "前前一格"往前挪一位（变成原 b）
    b = new          # "前一格"变成新算出的 dp[i]

写得更紧凑（Python 的多元赋值）：

    a, b = 0, 1
    for _ in range(n - 1):
        a, b = b, a + b
    return b

空间从 O(n) → **O(1)**。

═══════════════════════════════════════════════════════════════
【什么时候能用滚动数组？】
═══════════════════════════════════════════════════════════════

判断规则：**看转移方程依赖了过去几格**。

  - 只依赖 dp[i-1]                 → 1 个变量
  - 依赖 dp[i-1] 和 dp[i-2]        → 2 个变量（Fibonacci）
  - 依赖 dp[i-1] 到 dp[i-k]        → k 个变量（滑窗）

**二维 DP 同样适用**：如果 dp[i][j] 只依赖 dp[i-1][*]，
可以把二维数组压成两行，甚至一行（08 章背包会看到这个）。

⚠ **何时不能压**：如果你最后需要**回溯出最优解的具体路径**（比如
"用了哪些硬币、走了哪条路"），就必须保留完整 dp 表。空间换信息。

═══════════════════════════════════════════════════════════════
【可视化】
═══════════════════════════════════════════════════════════════

生成 output/04_rolling_fib6.png：
  - 上半图：完整 dp 数组（占 n+1 格）
  - 下半图：只保留两个变量 (a, b)，每一步它们都在"滚动前进"
  - 用箭头标出 a → b、b → new 的赋值流向
"""
from __future__ import annotations

import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, Rectangle

from _common import parse_plot_args, save_and_show


# ────────────────────────────────────────────────────────────
# 三种实现对比
# ────────────────────────────────────────────────────────────

def fib_tab(n: int) -> int:
    """O(n) 空间。"""
    if n < 2:
        return n
    dp = [0] * (n + 1)
    dp[1] = 1
    for i in range(2, n + 1):
        dp[i] = dp[i - 1] + dp[i - 2]
    return dp[n]


def fib_rolling(n: int) -> int:
    """O(1) 空间：两个变量来回滚。"""
    if n < 2:
        return n
    a, b = 0, 1
    for _ in range(n - 1):
        a, b = b, a + b
    return b


# ────────────────────────────────────────────────────────────
# 可视化：完整数组 vs 滚动两变量
# ────────────────────────────────────────────────────────────

def draw_array_row(ax, values, ylevel, *, highlight_indices=(), label_prefix="dp"):
    """画一行格子。"""
    cell_w = 1.0
    for i, v in enumerate(values):
        if i in highlight_indices:
            color = "#f1c40f"
        else:
            color = "#3498db"
        ax.add_patch(Rectangle((i * cell_w, ylevel), cell_w, 1.0, facecolor=color, edgecolor="black"))
        ax.text(i * cell_w + cell_w / 2, ylevel + 0.5, str(v),
                ha="center", va="center", fontsize=12, color="white", fontweight="bold")
        ax.text(i * cell_w + cell_w / 2, ylevel - 0.25, f"{label_prefix}[{i}]",
                ha="center", va="center", fontsize=9, color="#555")


def visualize(n: int = 6) -> None:
    """画 fib(n) 在『完整 dp』vs『滚动两变量』两种实现下的对照。"""
    fig, axes = plt.subplots(2, 1, figsize=(12, 7))

    # 上：完整 dp 数组（最终态）
    ax_top = axes[0]
    _, _ = fib_tab(n), None
    dp = [0] * (n + 1)
    dp[1] = 1
    for i in range(2, n + 1):
        dp[i] = dp[i - 1] + dp[i - 2]
    draw_array_row(ax_top, dp, ylevel=0, highlight_indices={n}, label_prefix="dp")
    ax_top.set_xlim(-0.5, (n + 1) + 0.5)
    ax_top.set_ylim(-1, 1.5)
    ax_top.set_aspect("equal")
    ax_top.axis("off")
    ax_top.set_title(
        f"❶ 完整 dp 数组（O(n) 空间）：保留了所有中间结果\n"
        f"   实际上算 dp[{n}] 只用了 dp[{n-1}] 和 dp[{n-2}]，其余都白存了",
        fontsize=11, loc="left",
    )

    # 下：滚动两变量的多帧快照
    ax_bot = axes[1]
    a, b = 0, 1
    snapshots: list[tuple[int, int]] = [(a, b)]
    for _ in range(n - 1):
        a, b = b, a + b
        snapshots.append((a, b))

    cell_w = 1.0
    gap = 0.6
    block_w = 2 * cell_w + gap
    for step, (av, bv) in enumerate(snapshots):
        x0 = step * (block_w + gap)
        # 画 a
        ax_bot.add_patch(Rectangle((x0, 0), cell_w, 1.0, facecolor="#9b59b6", edgecolor="black"))
        ax_bot.text(x0 + cell_w / 2, 0.5, str(av), ha="center", va="center",
                    fontsize=12, color="white", fontweight="bold")
        ax_bot.text(x0 + cell_w / 2, -0.3, "a", ha="center", va="center", fontsize=10)
        # 画 b
        ax_bot.add_patch(Rectangle((x0 + cell_w + gap, 0), cell_w, 1.0, facecolor="#e67e22", edgecolor="black"))
        ax_bot.text(x0 + 1.5 * cell_w + gap, 0.5, str(bv), ha="center", va="center",
                    fontsize=12, color="white", fontweight="bold")
        ax_bot.text(x0 + 1.5 * cell_w + gap, -0.3, "b", ha="center", va="center", fontsize=10)

        ax_bot.text(x0 + block_w / 2, 1.4, f"step {step}", ha="center", fontsize=9, color="#555")

        # 滚动箭头：上一帧的 b → 这一帧的 a；上一帧的 (a+b) → 这一帧的 b
        if step > 0:
            x_prev = (step - 1) * (block_w + gap)
            # b_{step-1} → a_step
            arrow1 = FancyArrowPatch(
                (x_prev + 1.5 * cell_w + gap, 1.05),
                (x0 + cell_w / 2, 1.05),
                arrowstyle="->", color="#16a085", linewidth=1.5,
                connectionstyle="arc3,rad=-0.3",
            )
            ax_bot.add_patch(arrow1)

    ax_bot.set_xlim(-0.5, len(snapshots) * (block_w + gap))
    ax_bot.set_ylim(-0.8, 2.0)
    ax_bot.set_aspect("equal")
    ax_bot.axis("off")
    ax_bot.set_title(
        f"❷ 滚动数组（O(1) 空间）：只保留 (a, b) 两个变量\n"
        f"   每一步 a, b = b, a+b：上一帧的 b 变成下一帧的 a，新算出的和变成下一帧的 b",
        fontsize=11, loc="left",
    )

    fig.suptitle(f"空间优化：fib({n}) 的两种实现对照", fontsize=14)
    plt.tight_layout()
    save_and_show(f"04_rolling_fib{n}.png")


# ────────────────────────────────────────────────────────────
# 主程序
# ────────────────────────────────────────────────────────────

def main() -> None:
    parse_plot_args()
    print("=" * 60)
    print("第 04 章：滚动数组（空间 O(n) → O(1)）")
    print("=" * 60)

    for n in (6, 10, 20, 50):
        a = fib_tab(n)
        b = fib_rolling(n)
        assert a == b, f"两种实现应一致：{a} vs {b}"
        print(f"fib({n:>2}) = {a:>15}   (两种实现一致 ✓)")

    print(
        "\n复杂度对比：\n"
        "  朴素递归   ：时间 O(2^n)   空间 O(n)（栈深）\n"
        "  记忆化     ：时间 O(n)     空间 O(n)\n"
        "  表格法     ：时间 O(n)     空间 O(n)\n"
        "  滚动数组   ：时间 O(n)     空间 O(1)  ⭐\n"
    )

    print("生成 fib(6) 的滚动对照图...")
    visualize(6)


if __name__ == "__main__":
    main()
