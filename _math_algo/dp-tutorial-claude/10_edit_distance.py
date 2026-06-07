"""
10 · 双序列 DP —— 编辑距离（Levenshtein 距离）

═══════════════════════════════════════════════════════════════
【题目】
═══════════════════════════════════════════════════════════════

给两个字符串 a 和 b。一次操作可以：

  - **插入**一个字符
  - **删除**一个字符
  - **替换**一个字符

问把 a 变成 b 最少需要几次操作？

例子：

    a = "horse"   →   b = "ros"

    一种方案（3 次）：
      horse  --删 h-->  orse
      orse   --删 r-->  ose   ← 等等好像不对
    再来：
      horse  --替 h→r-->  rorse
      rorse  --删 o-->  rrse        嗯也不太好

    其实最优是 3 次：
      horse → rorse (替换 h→r)
      rorse → rose  (删除 r)
      rose  → ros   (删除 e)

    所以 editDistance("horse", "ros") = 3。

═══════════════════════════════════════════════════════════════
【思维】两个字符串问题，状态几乎一定是二维的
═══════════════════════════════════════════════════════════════

经验法则：

   **"两个字符串" → 二维 DP（一个维度对应一个字符串的前缀长度）**

具体到本题，状态怎么定？

   仿照 LIS 那种"以谁结尾"的思路，但这里有两个串。
   最自然的设计：

    dp[i][j] = 把 a 的前 i 个字符 变成 b 的前 j 个字符 所需的最少操作数

   注意是"前缀长度"，不是"下标"。i 从 0 到 len(a)，j 从 0 到 len(b)。

═══════════════════════════════════════════════════════════════
【方案】四步法
═══════════════════════════════════════════════════════════════

1️⃣ **定义状态**（如上）

2️⃣ **转移方程**

   想象你正在处理 dp[i][j]。盯着 a 的第 i 个字符 a[i-1] 和 b 的第 j 个字符 b[j-1]：

   **情况 A：a[i-1] == b[j-1]**

     这两个字符已经一样了，**啥都不用操作**。问题缩小到把前 i-1 个 a
     变成前 j-1 个 b：

       dp[i][j] = dp[i-1][j-1]

   **情况 B：a[i-1] != b[j-1]**

     必须操作 1 次。有 3 种选择：

     - **替换** a[i-1] 为 b[j-1]：→ dp[i-1][j-1] + 1
       （替换完，两边都"对齐"了一个字符，子问题变成前 i-1 vs 前 j-1）

     - **删除** a[i-1]：→ dp[i-1][j] + 1
       （从 a 砍掉一个字符，b 不动，子问题变成前 i-1 vs 前 j）

     - **插入** 一个 b[j-1] 到 a 末尾：→ dp[i][j-1] + 1
       （a 不动，b 砍掉一个字符已被"匹配"，子问题变成前 i vs 前 j-1）

     取最小：

       dp[i][j] = 1 + min(dp[i-1][j-1], dp[i-1][j], dp[i][j-1])

3️⃣ **边界**

   - dp[0][j] = j     （把空串变成 b 的前 j 个字符，需要 j 次插入）
   - dp[i][0] = i     （把 a 的前 i 个字符变成空串，需要 i 次删除）

4️⃣ **计算顺序**

   dp[i][j] 依赖 dp[i-1][j-1]、dp[i-1][j]、dp[i][j-1]——左上、上方、左方。
   所以从左到右、从上到下逐行遍历就行。

═══════════════════════════════════════════════════════════════
【一道"换皮题"】
═══════════════════════════════════════════════════════════════

把"插入/删除/替换"这三种操作的代价改一改、加几条限制，就变出：

  - 拼写检查（计算两个词的相似度）
  - 生物信息学的序列比对（DNA 对齐）
  - Git diff 算法的核心
  - 模糊搜索（"我输 hellp，你猜我想说 hello"）

**所以双序列 DP 不只是面试题，是工业级算法。**

═══════════════════════════════════════════════════════════════
【可视化】
═══════════════════════════════════════════════════════════════

生成 output/10_edit_distance.png：
  - 二维 DP 表热力图（(len(a)+1) × (len(b)+1) 矩阵）
  - 行 = a 的前缀，列 = b 的前缀
  - 在每格上画 3 个箭头指出"来源"（左上=替换/匹配，上=删除，左=插入），
    实际生效的来源用粗红色，其余淡灰
  - 最终红色路径展示一种最优编辑过程
"""
from __future__ import annotations

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import FancyArrowPatch

from _common import parse_plot_args, save_and_show


# ────────────────────────────────────────────────────────────
# DP 解法
# ────────────────────────────────────────────────────────────

def edit_distance(a: str, b: str) -> tuple[int, list[list[int]]]:
    m, n = len(a), len(b)
    dp = [[0] * (n + 1) for _ in range(m + 1)]

    for i in range(m + 1):
        dp[i][0] = i
    for j in range(n + 1):
        dp[0][j] = j

    for i in range(1, m + 1):
        for j in range(1, n + 1):
            if a[i - 1] == b[j - 1]:
                dp[i][j] = dp[i - 1][j - 1]
            else:
                dp[i][j] = 1 + min(dp[i - 1][j - 1], dp[i - 1][j], dp[i][j - 1])

    return dp[m][n], dp


def reconstruct_path(a: str, b: str, dp: list[list[int]]) -> list[tuple[int, int, str]]:
    """回溯一条最优编辑路径：返回 [(i, j, 操作描述), ...]，从起点到终点。"""
    i, j = len(a), len(b)
    ops: list[tuple[int, int, str]] = []
    while i > 0 or j > 0:
        if i > 0 and j > 0 and a[i - 1] == b[j - 1]:
            ops.append((i, j, f"匹配 '{a[i-1]}'"))
            i, j = i - 1, j - 1
        elif i > 0 and j > 0 and dp[i][j] == dp[i - 1][j - 1] + 1:
            ops.append((i, j, f"替换 '{a[i-1]}' → '{b[j-1]}'"))
            i, j = i - 1, j - 1
        elif i > 0 and dp[i][j] == dp[i - 1][j] + 1:
            ops.append((i, j, f"删除 '{a[i-1]}'"))
            i -= 1
        else:
            ops.append((i, j, f"插入 '{b[j-1]}'"))
            j -= 1
    ops.append((0, 0, "起点（空串 → 空串）"))
    ops.reverse()
    return ops


# ────────────────────────────────────────────────────────────
# 可视化
# ────────────────────────────────────────────────────────────

def visualize(a: str, b: str) -> None:
    dist, dp = edit_distance(a, b)
    arr = np.array(dp)
    m, n = len(a), len(b)

    fig, ax = plt.subplots(figsize=(max(8, (n + 1) * 1.0), max(7, (m + 1) * 1.0)))
    im = ax.imshow(arr, cmap="YlGnBu", aspect="equal")
    fig.colorbar(im, ax=ax, fraction=0.04, pad=0.04, label="dp[i][j]")

    for i in range(m + 1):
        for j in range(n + 1):
            ax.text(j, i, str(arr[i, j]),
                    ha="center", va="center", fontsize=11,
                    color="white" if arr[i, j] > arr.max() / 2 else "black",
                    fontweight="bold")

    # 回溯路径
    path = reconstruct_path(a, b, dp)
    path_coords = [(i, j) for (i, j, _) in path]

    for k in range(1, len(path_coords)):
        i0, j0 = path_coords[k - 1]
        i1, j1 = path_coords[k]
        ax.add_patch(FancyArrowPatch(
            (j0, i0), (j1, i1),
            arrowstyle="-|>", mutation_scale=18,
            color="#c0392b", linewidth=2.5,
            zorder=5,
        ))

    # x 轴：b 的字符
    ax.set_xticks(range(n + 1))
    xlabels = [""] + list(b)
    ax.set_xticklabels(xlabels)
    ax.set_xlabel(f"b 的前 j 个字符  →  b = '{b}'")

    # y 轴：a 的字符
    ax.set_yticks(range(m + 1))
    ylabels = [""] + list(a)
    ax.set_yticklabels(ylabels)
    ax.set_ylabel(f"a 的前 i 个字符  →  a = '{a}'")

    op_summary = " → ".join(op for _, _, op in path)
    ax.set_title(
        f"编辑距离 DP 表    a='{a}'  →  b='{b}'    distance = {dist}\n"
        f"红色路径：一条最优编辑序列",
        fontsize=12,
    )

    # 在图侧把操作流程打印出来
    plt.gcf().text(
        0.02, 0.02,
        "操作序列：\n  " + "\n  ".join(op for _, _, op in path[1:]),
        fontsize=9,
        bbox=dict(boxstyle="round", facecolor="#ecf0f1", edgecolor="#95a5a6"),
    )

    plt.tight_layout(rect=[0, 0.15, 1, 1])
    save_and_show(f"10_edit_distance_{a}_to_{b}.png")


# ────────────────────────────────────────────────────────────
# 主程序
# ────────────────────────────────────────────────────────────

def main() -> None:
    parse_plot_args()
    print("=" * 60)
    print("第 10 章：双序列 DP — 编辑距离")
    print("=" * 60)

    test_cases = [
        ("horse", "ros"),
        ("intention", "execution"),
        ("kitten", "sitting"),
        ("", "abc"),
        ("abc", "abc"),
    ]

    for a, b in test_cases:
        dist, dp = edit_distance(a, b)
        print(f"\n'{a}' → '{b}'   编辑距离 = {dist}")
        if a and b and len(a) <= 12 and len(b) <= 12:
            ops = reconstruct_path(a, b, dp)
            print("  操作序列：")
            for _, _, op in ops[1:]:
                print(f"    · {op}")

    print("\n生成 'horse' → 'ros' 的 DP 表可视化...")
    visualize("horse", "ros")


if __name__ == "__main__":
    main()
