"""
11 · 区间 DP —— 矩阵链乘问题

═══════════════════════════════════════════════════════════════
【题目】
═══════════════════════════════════════════════════════════════

你有 n 个矩阵 A₁, A₂, ..., Aₙ，要算它们的乘积 A₁ × A₂ × ... × Aₙ。

矩阵乘法**结合律成立**：(AB)C = A(BC)，但**结合顺序不同，乘法次数不同**。

  - A 是 p×q，B 是 q×r → 算 A×B 需要 p×q×r 次标量乘法。

例子：A(10×30), B(30×5), C(5×60)

  - (AB)C：先算 AB（10×30×5 = 1500 次），得到 10×5 矩阵；再 ×C（10×5×60 = 3000）。共 **4500** 次。
  - A(BC)：先算 BC（30×5×60 = 9000 次），得到 30×60 矩阵；再 A×（10×30×60 = 18000）。共 **27000** 次。

差了 6 倍！**最优结合顺序值得算。**

给定每个矩阵的维度（用 n+1 个数 p₀, p₁, ..., pₙ 表示，其中第 i 个矩阵是 pᵢ₋₁ × pᵢ），
求计算 A₁...Aₙ 的最少标量乘法次数。

═══════════════════════════════════════════════════════════════
【思维】"区间 DP"是干什么的？
═══════════════════════════════════════════════════════════════

线性 DP 的状态是"前 i 个元素"，单维。

但有些问题（比如本题），处理一段子序列 A_l..A_r 时，你需要考虑：
**这一段的最优答案，依赖于把这一段从哪儿切一刀**。

  对 A_l × A_{l+1} × ... × A_r，如果在位置 k 处切（l ≤ k < r），结果是：
    (A_l...A_k) × (A_{k+1}...A_r)
  总代价 = 左半段代价 + 右半段代价 + 最后那一次"两个矩阵相乘"的代价

切点 k 可以在 l 到 r-1 任意位置。我们要枚举所有切点，取最小。

**这就是区间 DP**：状态用一段"区间 [l, r]"描述。

区间 DP 的标志：
  - 输入是一个序列，但**不能简单地"从左到右"算**；
  - 答案与"如何切分这段序列"有关；
  - 状态形如 dp[l][r]。

代表题：矩阵链乘、戳气球、回文分割、合并石子……

═══════════════════════════════════════════════════════════════
【方案】四步法
═══════════════════════════════════════════════════════════════

1️⃣ **定义状态**

   矩阵编号从 1 到 n，dims 数组 p[0..n] 表示维度。

    dp[l][r] = 计算 A_l × A_{l+1} × ... × A_r 的最少标量乘法次数

2️⃣ **转移方程**

   枚举切点 k ∈ [l, r-1]：

    dp[l][r] = min(  dp[l][k] + dp[k+1][r] + p[l-1] × p[k] × p[r]  )
                  k

   - dp[l][k]：算左半边 A_l...A_k 的代价
   - dp[k+1][r]：算右半边 A_{k+1}...A_r 的代价
   - p[l-1] × p[k] × p[r]：把"左半边结果（p[l-1] × p[k]）"乘以
     "右半边结果（p[k] × p[r]）"这最后一步的代价

3️⃣ **边界**

    dp[i][i] = 0     （只有一个矩阵，不用乘）

4️⃣ **计算顺序** ⚠️ 区间 DP 的灵魂

   **按区间长度从小到大**遍历（不是按 l 或按 r）。

   为什么？算 dp[l][r] 需要 dp[l][k] 和 dp[k+1][r]，这两个区间**都更短**。
   只要先把所有"短区间"的 dp 算完，长区间才能算。

   代码骨架：

       for length in range(2, n + 1):           # 区间长度
           for l in range(1, n - length + 2):   # 左端点
               r = l + length - 1               # 右端点
               dp[l][r] = min over k of (...)

═══════════════════════════════════════════════════════════════
【DP 表的形状：上三角】
═══════════════════════════════════════════════════════════════

dp[l][r] 只在 l ≤ r 时有意义，所以只用了二维表的**上三角部分**。
这是区间 DP 的标志性形态。

═══════════════════════════════════════════════════════════════
【可视化】
═══════════════════════════════════════════════════════════════

生成 output/11_matrix_chain.png：
  - 上三角热力图：dp[l][r] 的值，按"长度"逐层填充
  - 每格还标注最优切点 k*
  - 标题下方画出最优结合方式（带括号的算式）
"""
from __future__ import annotations

import matplotlib.pyplot as plt
import numpy as np

from _common import parse_plot_args, save_and_show


# ────────────────────────────────────────────────────────────
# DP 解法
# ────────────────────────────────────────────────────────────

def matrix_chain(p: list[int]) -> tuple[int, list[list[int]], list[list[int]]]:
    """p[0..n] 表示 n 个矩阵的维度。返回 (最少乘法次数, dp 表, 最优切点表)。"""
    n = len(p) - 1
    INF = float("inf")
    # dp 和 split 用 1..n 的下标方便
    dp = [[0] * (n + 2) for _ in range(n + 2)]
    split = [[0] * (n + 2) for _ in range(n + 2)]

    for length in range(2, n + 1):
        for l in range(1, n - length + 2):
            r = l + length - 1
            dp[l][r] = INF
            for k in range(l, r):
                cost = dp[l][k] + dp[k + 1][r] + p[l - 1] * p[k] * p[r]
                if cost < dp[l][r]:
                    dp[l][r] = cost
                    split[l][r] = k

    return dp[1][n], dp, split


def print_parenthesization(split: list[list[int]], l: int, r: int) -> str:
    if l == r:
        return f"A{l}"
    k = split[l][r]
    return f"({print_parenthesization(split, l, k)} × {print_parenthesization(split, k + 1, r)})"


# ────────────────────────────────────────────────────────────
# 可视化
# ────────────────────────────────────────────────────────────

def visualize(p: list[int]) -> None:
    n = len(p) - 1
    best, dp, split = matrix_chain(p)

    # 把上三角拿出来画
    arr = np.full((n, n), np.nan)
    for l in range(1, n + 1):
        for r in range(l, n + 1):
            arr[l - 1, r - 1] = dp[l][r]

    fig, ax = plt.subplots(figsize=(max(8, n * 1.2), max(7, n * 1.0)))
    masked = np.ma.array(arr, mask=np.isnan(arr))
    cmap = plt.cm.get_cmap("YlOrRd").copy()
    cmap.set_bad(color="#ecf0f1")
    im = ax.imshow(masked, cmap=cmap, aspect="equal")
    fig.colorbar(im, ax=ax, fraction=0.04, pad=0.04, label="dp[l][r]")

    for l in range(1, n + 1):
        for r in range(1, n + 1):
            if r >= l:
                value = dp[l][r]
                label = str(value)
                if l != r and split[l][r] > 0:
                    label += f"\nk*={split[l][r]}"
                ax.text(r - 1, l - 1, label,
                        ha="center", va="center", fontsize=9,
                        color="white" if value > best * 0.5 else "black",
                        fontweight="bold")
            else:
                ax.text(r - 1, l - 1, "—", ha="center", va="center", color="#bdc3c7")

    ax.set_xticks(range(n))
    ax.set_yticks(range(n))
    ax.set_xticklabels([f"r={i+1}" for i in range(n)])
    ax.set_yticklabels([f"l={i+1}" for i in range(n)])
    ax.set_xlabel("右端点 r")
    ax.set_ylabel("左端点 l")

    expr = print_parenthesization(split, 1, n)
    ax.set_title(
        f"矩阵链乘 DP 表（上三角）  维度={p}\n"
        f"最少乘法次数 = {best}    最优结合 = {expr}",
        fontsize=12,
    )

    plt.tight_layout()
    save_and_show(f"11_matrix_chain_n{n}.png")


# ────────────────────────────────────────────────────────────
# 主程序
# ────────────────────────────────────────────────────────────

def main() -> None:
    parse_plot_args()
    print("=" * 60)
    print("第 11 章：区间 DP — 矩阵链乘")
    print("=" * 60)

    test_cases = [
        [10, 30, 5, 60],            # 课本经典小例
        [30, 35, 15, 5, 10, 20, 25],  # 经典中等例
    ]

    for p in test_cases:
        n = len(p) - 1
        best, dp, split = matrix_chain(p)
        expr = print_parenthesization(split, 1, n)
        print(f"\n维度 p = {p}（{n} 个矩阵）")
        print(f"  最少乘法次数 = {best}")
        print(f"  最优结合方式 = {expr}")

    print("\n生成第二个例子的 dp 表上三角图...")
    visualize([30, 35, 15, 5, 10, 20, 25])


if __name__ == "__main__":
    main()
