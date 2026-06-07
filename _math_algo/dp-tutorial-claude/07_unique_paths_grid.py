"""
07 · 网格 DP —— 不同路径数（机器人走方格）

═══════════════════════════════════════════════════════════════
【题目】
═══════════════════════════════════════════════════════════════

一个 m × n 的方格地图。机器人从左上角 (0, 0) 出发，要走到右下角
(m-1, n-1)。每一步只能往**右**或往**下**走。问总共有多少条不同的路径。

例子：3 × 3 网格 → 6 条不同路径。

═══════════════════════════════════════════════════════════════
【思维】网格题的"灵魂三问"
═══════════════════════════════════════════════════════════════

拿到网格题，永远先问自己：

  ❶  "要走到格子 (i, j)，**最后一步**是从哪儿过来的？"
  ❷  "可能的'上一步'有几种？"
  ❸  "把这几种'上一步'的方案数加起来，是不是就是 (i, j) 的方案数？"

对本题：

  - 题目规定只能向右或向下，所以要到 (i, j)，最后一步要么从上方 (i-1, j) 下来，
    要么从左方 (i, j-1) 右移。
  - 两种"上一步"路径**互不重叠**（最后一步的方向不同，决定了不同路径）。
  - 所以 (i, j) 的方案数 = (i-1, j) 的方案数 + (i, j-1) 的方案数。

这就直接出转移方程了。

═══════════════════════════════════════════════════════════════
【方案】四步法
═══════════════════════════════════════════════════════════════

1️⃣ **定义状态**

    dp[i][j] = 从 (0, 0) 走到 (i, j) 的不同路径数

2️⃣ **转移方程**

    dp[i][j] = dp[i-1][j] + dp[i][j-1]     （当 i ≥ 1 且 j ≥ 1）

3️⃣ **边界**

    - dp[0][0] = 1                 起点本身就是 1 种方案（"什么都不走"）
    - dp[0][j] = 1 (j ≥ 1)         第一行只能一路向右
    - dp[i][0] = 1 (i ≥ 1)         第一列只能一路向下

4️⃣ **计算顺序**

   dp[i][j] 依赖左边 dp[i][j-1] 和上面 dp[i-1][j]，所以从左到右、
   从上到下逐行遍历即可。

═══════════════════════════════════════════════════════════════
【一个小彩蛋：杨辉三角】
═══════════════════════════════════════════════════════════════

把 dp 表斜着看，你会发现它就是**杨辉三角**：

       1
       1  1
       1  2  1
       1  3  3  1
       1  4  6  4  1
       ...

因为本题答案在数学上 = C(m+n-2, m-1)，组合数嘛！
**DP 是组合数学的"算法实现"**——这是一个非常深的洞察，记住它，
未来很多组合计数题你都能用 DP 优雅地解决。

═══════════════════════════════════════════════════════════════
【可视化】
═══════════════════════════════════════════════════════════════

生成 output/07_grid_paths.png：
  - 热力图展示 m × n 的 dp 表（颜色深浅 = 路径数大小）
  - 每个格子标注 dp 值
  - 每个格子画两个箭头（上方 ↓ 和 左方 →）显示路径流向
"""
from __future__ import annotations

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import FancyArrowPatch

from _common import parse_plot_args, save_and_show


# ────────────────────────────────────────────────────────────
# DP 解法
# ────────────────────────────────────────────────────────────

def unique_paths(m: int, n: int) -> tuple[int, list[list[int]]]:
    dp = [[0] * n for _ in range(m)]

    # 边界：第一行、第一列全是 1
    for i in range(m):
        dp[i][0] = 1
    for j in range(n):
        dp[0][j] = 1

    # 状态转移
    for i in range(1, m):
        for j in range(1, n):
            dp[i][j] = dp[i - 1][j] + dp[i][j - 1]

    return dp[m - 1][n - 1], dp


# ────────────────────────────────────────────────────────────
# 可视化
# ────────────────────────────────────────────────────────────

def visualize(m: int, n: int) -> None:
    _, dp = unique_paths(m, n)
    arr = np.array(dp)

    fig, ax = plt.subplots(figsize=(max(7, n * 1.3), max(6, m * 1.3)))

    im = ax.imshow(arr, cmap="YlOrRd", aspect="equal")
    fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04, label="dp[i][j] = 到达该格的路径数")

    # 在每格中央写数字
    for i in range(m):
        for j in range(n):
            ax.text(j, i, str(arr[i, j]),
                    ha="center", va="center",
                    fontsize=13, fontweight="bold",
                    color="white" if arr[i, j] > arr.max() / 2 else "black")

    # 画箭头：从上方和左方"流入"每个非边界格子
    for i in range(m):
        for j in range(n):
            if i >= 1:
                ax.add_patch(FancyArrowPatch(
                    (j, i - 1 + 0.35), (j, i - 0.35),
                    arrowstyle="->", mutation_scale=12, color="#2c3e50", linewidth=1.2,
                ))
            if j >= 1:
                ax.add_patch(FancyArrowPatch(
                    (j - 1 + 0.35, i), (j - 0.35, i),
                    arrowstyle="->", mutation_scale=12, color="#16a085", linewidth=1.2,
                ))

    # 标注起点终点
    ax.text(0, -0.65, "起点 S", ha="center", fontsize=11, color="#27ae60", fontweight="bold")
    ax.text(n - 1, m - 0.35, "终点 G", ha="center", fontsize=11, color="#c0392b", fontweight="bold")

    ax.set_xticks(range(n))
    ax.set_yticks(range(m))
    ax.set_xticklabels([f"j={j}" for j in range(n)])
    ax.set_yticklabels([f"i={i}" for i in range(m)])
    ax.set_title(
        f"不同路径数（{m} × {n} 网格）= {dp[m-1][n-1]}\n"
        f"灰色箭头 ↓ : 从上方继承  ｜  绿色箭头 → : 从左方继承  ｜  当前格 = 两者之和",
        fontsize=12,
    )

    plt.tight_layout()
    save_and_show(f"07_grid_paths_{m}x{n}.png")


# ────────────────────────────────────────────────────────────
# 主程序
# ────────────────────────────────────────────────────────────

def main() -> None:
    parse_plot_args()
    print("=" * 60)
    print("第 07 章：网格 DP — 不同路径数")
    print("=" * 60)

    for m, n in [(3, 3), (4, 5), (1, 7), (7, 7)]:
        ans, _ = unique_paths(m, n)
        print(f"{m} × {n} 网格 → {ans} 条不同路径")

    print(
        "\n（顺带验证：3×3 的答案 6 正好是 C(4, 2) = 6，\n"
        " 4×5 的答案是 C(7, 3) = 35。DP 表就是杨辉三角斜着看。）\n"
    )

    print("打印 4 × 5 网格的完整 dp 表：")
    _, dp = unique_paths(4, 5)
    for row in dp:
        print("  " + "  ".join(f"{v:>3}" for v in row))

    print("\n生成 4 × 5 网格的热力图...")
    visualize(4, 5)


if __name__ == "__main__":
    main()
