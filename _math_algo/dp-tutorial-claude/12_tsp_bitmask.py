"""
12 · 状态压缩 DP —— 旅行商问题（TSP，小规模）

═══════════════════════════════════════════════════════════════
【题目】旅行商问题（TSP）
═══════════════════════════════════════════════════════════════

n 个城市，两两之间有距离 dist[i][j]。从城市 0 出发，要**每个城市恰好访问一次**，
最后回到城市 0。求最短总路程。

这是计算机科学最著名的 NP-Hard 问题之一。**通用最优解的复杂度是指数级**——但当 n ≤ 20
左右时，状态压缩 DP 能在 O(n² · 2ⁿ) 时间内给出精确解，比朴素枚举的 O(n!) 快得多。

═══════════════════════════════════════════════════════════════
【思维】当"已经访问过哪些城市"本身就是状态时……
═══════════════════════════════════════════════════════════════

朴素思路：n! 种排列全枚举。n=10 就要算 360 万；n=15 直接爆炸。

DP 思路第一步：**怎么定义状态**？

  - 你正站在某个城市 `cur`；
  - 你已经访问过一组城市 `visited`；
  - 接下来要去 `cur` 之外、`visited` 之外的某个城市。

未来要走多远，**只取决于**：
  1. 你当前在哪 (cur)
  2. 哪些城市还没去 (即 visited 的补集)

**未来与"你走过的具体顺序"无关！** 这就是无后效性，DP 能用。

但是……"已访问城市集合" `visited` 怎么塞进 dp 数组的下标？

答案：**用一个整数的二进制位来表示集合**（bitmask）。

  - 第 i 位是 1 ⇔ 城市 i 已被访问
  - 例：n = 5，visited = {0, 2, 4} → 二进制 10101 → 整数 21

集合操作变成位运算：
  - 加入城市 i：mask | (1 << i)
  - 城市 i 在集合中？(mask >> i) & 1
  - 已访问的城市数：bin(mask).count("1")

═══════════════════════════════════════════════════════════════
【方案】四步法
═══════════════════════════════════════════════════════════════

1️⃣ **定义状态**

    dp[mask][cur] = "已访问城市集合恰好是 mask，当前正站在城市 cur" 时，
                    已经走过的最短路程

    （注意 cur 必须 ∈ mask；其余 dp 值无意义，用 INF 表示）

2️⃣ **转移方程**

   要从 dp[mask][cur] 转移：枚举下一个去的城市 next，
   要求 next ∉ mask（即 (mask >> next) & 1 == 0）：

    dp[mask | (1<<next)][next] = min(
        dp[mask | (1<<next)][next],
        dp[mask][cur] + dist[cur][next]
    )

3️⃣ **边界**

    dp[1 << 0][0] = 0     （只访问了城市 0，站在城市 0，路程 0）
    其余 = INF

4️⃣ **计算顺序**

   按 mask 从小到大（等价于按已访问城市数从少到多）。
   外层枚举 mask（0 到 2ⁿ-1），内层枚举 cur 和 next。

═══════════════════════════════════════════════════════════════
【最终答案】
═══════════════════════════════════════════════════════════════

走完所有城市后，再回到起点 0：

    answer = min over cur of (  dp[(1<<n) - 1][cur] + dist[cur][0]  )

  - (1<<n) - 1 是"所有城市都访问过"的 mask（全 1）
  - 在末尾哪个城市最优，要枚举

═══════════════════════════════════════════════════════════════
【为什么叫"状态压缩"？】
═══════════════════════════════════════════════════════════════

把一个"集合"压缩成了**一个整数**。本来需要 n 个 bool 才能表示
"哪些城市被访问"，现在一个 mask 搞定。

这种技巧适用于：
  - 集合是状态的一部分
  - 集合元素个数不大（≤ 20）
  - 集合操作（增删查）能用位运算高效完成

═══════════════════════════════════════════════════════════════
【可视化】
═══════════════════════════════════════════════════════════════

生成 output/12_tsp.png：
  - 左图：城市散点 + 最优 TSP 路径（红色折线）
  - 右图：dp 表片段——按访问城市数分层，展示 mask 是如何"长大"的
"""
from __future__ import annotations

import math
from itertools import permutations

import matplotlib.pyplot as plt
import numpy as np

from _common import parse_plot_args, save_and_show


# ────────────────────────────────────────────────────────────
# DP 解法（状态压缩）
# ────────────────────────────────────────────────────────────

def tsp_dp(dist: list[list[float]]) -> tuple[float, list[int]]:
    """O(n² · 2ⁿ)。返回 (最短总路程, 最优访问顺序——以城市 0 开始 0 结束)。"""
    n = len(dist)
    INF = math.inf
    full = 1 << n

    dp = [[INF] * n for _ in range(full)]
    parent = [[-1] * n for _ in range(full)]
    dp[1 << 0][0] = 0.0

    for mask in range(full):
        for cur in range(n):
            if not (mask >> cur) & 1:
                continue
            if dp[mask][cur] == INF:
                continue
            for nxt in range(n):
                if (mask >> nxt) & 1:
                    continue
                new_mask = mask | (1 << nxt)
                new_cost = dp[mask][cur] + dist[cur][nxt]
                if new_cost < dp[new_mask][nxt]:
                    dp[new_mask][nxt] = new_cost
                    parent[new_mask][nxt] = cur

    # 末尾再回到 0
    end_mask = full - 1
    best = INF
    last = -1
    for cur in range(1, n):
        total = dp[end_mask][cur] + dist[cur][0]
        if total < best:
            best = total
            last = cur

    # 回溯路径：从 last 沿 parent 一路回到 0，再翻转
    path: list[int] = []
    cur = last
    mask = end_mask
    while cur != -1:
        path.append(cur)
        prev = parent[mask][cur]
        mask ^= (1 << cur)
        cur = prev
    path.reverse()
    path.append(0)  # 回到起点

    return best, path


def tsp_brute(dist: list[list[float]]) -> tuple[float, list[int]]:
    """O(n!) 暴力，用于对拍。n 别给太大（≤ 8）。"""
    n = len(dist)
    others = list(range(1, n))
    best = math.inf
    best_path: list[int] = []
    for perm in permutations(others):
        order = [0, *perm, 0]
        total = sum(dist[order[k]][order[k + 1]] for k in range(len(order) - 1))
        if total < best:
            best = total
            best_path = order
    return best, best_path


# ────────────────────────────────────────────────────────────
# 可视化
# ────────────────────────────────────────────────────────────

def visualize(coords: list[tuple[float, float]]) -> None:
    n = len(coords)
    # 距离矩阵
    dist = [[math.hypot(coords[i][0] - coords[j][0], coords[i][1] - coords[j][1])
             for j in range(n)] for i in range(n)]

    best, path = tsp_dp(dist)

    fig, axes = plt.subplots(1, 2, figsize=(16, 7), gridspec_kw={"width_ratios": [1, 1.2]})

    # 左：城市 + 最优路径
    ax = axes[0]
    xs = [c[0] for c in coords]
    ys = [c[1] for c in coords]
    ax.scatter(xs, ys, s=200, c="#3498db", edgecolor="black", zorder=3)
    for i, (x, y) in enumerate(coords):
        ax.text(x, y, str(i), ha="center", va="center", fontsize=12, fontweight="bold", color="white", zorder=4)
    for k in range(len(path) - 1):
        x0, y0 = coords[path[k]]
        x1, y1 = coords[path[k + 1]]
        ax.plot([x0, x1], [y0, y1], "-", color="#e74c3c", linewidth=2, zorder=2)

    ax.set_title(f"最优 TSP 路径\n顺序: {' → '.join(map(str, path))}    总路程 ≈ {best:.2f}", fontsize=12)
    ax.set_aspect("equal")
    ax.grid(alpha=0.3)

    # 右：按"已访问城市数"分层展示 dp 状态扩展
    ax = axes[1]
    levels = {k: [] for k in range(0, n + 1)}
    for mask in range(1 << n):
        levels[bin(mask).count("1")].append(mask)

    # 每层挑一些 mask 展示，最多 8 个，避免太挤
    ax.axis("off")
    ax.set_title(
        "状态压缩 DP 的状态扩展\n"
        "每一行：已访问城市数 = k 的所有 mask\n"
        "（左下→右上，按访问数增长，DP 顺序）",
        fontsize=12,
    )

    y_top = n
    for k in range(1, n + 1):
        ax.text(-0.5, y_top - k, f"已访问 {k} 个：",
                ha="right", va="center", fontsize=10, fontweight="bold")
        masks = sorted(levels[k])[:10]
        for idx, mask in enumerate(masks):
            binstr = format(mask, f"0{n}b")
            # 用颜色区分 0/1
            for bit_idx, bit in enumerate(reversed(binstr)):
                color = "#27ae60" if bit == "1" else "#ecf0f1"
                ax.add_patch(plt.Rectangle((idx * (n + 1) + bit_idx * 0.6, y_top - k - 0.3),
                                           0.5, 0.6, facecolor=color, edgecolor="black", linewidth=0.5))
                ax.text(idx * (n + 1) + bit_idx * 0.6 + 0.25, y_top - k,
                        bit, ha="center", va="center", fontsize=7, color="white" if bit == "1" else "#7f8c8d")

    ax.set_xlim(-3, max(10, n) * (n + 1) * 0.8)
    ax.set_ylim(-1, n + 1)

    plt.tight_layout()
    save_and_show(f"12_tsp_n{n}.png")


# ────────────────────────────────────────────────────────────
# 主程序
# ────────────────────────────────────────────────────────────

def main() -> None:
    parse_plot_args()
    print("=" * 60)
    print("第 12 章：状态压缩 DP — 旅行商问题（TSP）")
    print("=" * 60)

    # 一组固定坐标，方便复现
    coords = [
        (0.0, 0.0),
        (1.0, 3.0),
        (4.0, 3.0),
        (5.0, 0.0),
        (3.0, -2.0),
        (1.0, -2.0),
    ]
    n = len(coords)
    dist = [[math.hypot(coords[i][0] - coords[j][0], coords[i][1] - coords[j][1])
             for j in range(n)] for i in range(n)]

    print(f"\n城市坐标：{coords}")

    print("\n── 对拍：暴力 O(n!) vs DP O(n² · 2ⁿ) ──")
    best_brute, path_brute = tsp_brute(dist)
    best_dp, path_dp = tsp_dp(dist)
    print(f"暴力解：路程 = {best_brute:.4f}   路径 = {path_brute}")
    print(f"DP 解 ：路程 = {best_dp:.4f}   路径 = {path_dp}")
    print(f"一致？ {abs(best_brute - best_dp) < 1e-9}")

    print(
        "\n→ 暴力解枚举了 {0}! = {1} 种排列；".format(n - 1, math.factorial(n - 1))
        + "\n  DP 解的状态数是 n × 2^n = {0}，".format(n * (2 ** n))
        + "差距随 n 越大越夸张。\n"
    )

    print("生成 TSP 可视化图...")
    visualize(coords)


if __name__ == "__main__":
    main()
