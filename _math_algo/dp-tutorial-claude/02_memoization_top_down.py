"""
02 · 记忆化（Top-Down / 自顶向下）—— 算过的就别再算了

═══════════════════════════════════════════════════════════════
【思维】最朴素的优化思路：缓存
═══════════════════════════════════════════════════════════════

回顾上一章：fib(n) 的朴素递归之所以慢，**唯一**的原因是同一个
fib(k) 被反复计算。

那解决思路是不是非常自然？

    "诶，fib(3) 我刚才不是算过吗？答案是 2。下次再问 fib(3)，
     我直接报 2，不就行了？"

是的，这就是**记忆化（memoization）**：

  1. 备一个本子（哈希表 / 数组）。
  2. 算 fib(k) 之前先翻本子，**算过就直接抄答案**。
  3. 算完一个新答案，**记到本子里**再返回。

代码改动只有 3 行，但复杂度从 O(2^n) 暴跌到 O(n)。

═══════════════════════════════════════════════════════════════
【方案】把递归改造成"查表 + 算 + 存"三步走
═══════════════════════════════════════════════════════════════

伪代码：

    memo = {}
    def fib(n):
        if n < 2: return n
        if n in memo: return memo[n]      # 1) 查表
        memo[n] = fib(n-1) + fib(n-2)     # 2) 算
        return memo[n]                    # 3) 返回（隐含"已存"）

**为什么这就把指数变成了线性？**

每个 fib(k) 在整个递归过程里**只会真正计算一次**（之后都是 O(1) 查表）。
n 个不同的 k 值（0, 1, ..., n），所以总工作量是 O(n)。

**记忆化 vs 表格法**

  - 记忆化（本章）：写法贴近原始递归，**思维顺序自顶向下**。
    适合状态稀疏 / 转移复杂 / 自己也搞不清要算哪些子状态的情况。
  - 表格法（下一章）：从最小子问题开始，**反过来从底往上算**。
    适合状态规整 / 容易枚举的情况。两者复杂度通常相同。

═══════════════════════════════════════════════════════════════
【可视化】
═══════════════════════════════════════════════════════════════

跑完会生成 output/02_memoization_tree.png：
  - 绿色节点 = 第一次真正计算的子问题（实算）
  - 灰色节点 = 缓存命中，直接抄答案（O(1)）
  - 对比第 01 章的全红重复树，你会看到记忆化把"白干的活"全省了。
"""
from __future__ import annotations

from collections import Counter

import matplotlib.pyplot as plt
import networkx as nx

from _common import parse_plot_args, save_and_show


# ────────────────────────────────────────────────────────────
# 记忆化版 Fibonacci
# ────────────────────────────────────────────────────────────

def fib_memo(n: int, memo: dict[int, int] | None = None) -> int:
    if memo is None:
        memo = {}
    if n < 2:
        return n
    if n in memo:
        return memo[n]
    memo[n] = fib_memo(n - 1, memo) + fib_memo(n - 2, memo)
    return memo[n]


# ────────────────────────────────────────────────────────────
# 追踪每个节点是"实算"还是"缓存命中"，用于画图
# ────────────────────────────────────────────────────────────

def trace_memoized_calls(n: int) -> tuple[nx.DiGraph, dict[str, tuple[float, float]], set[str]]:
    """模拟带记忆化的递归过程，记下每个节点是否为缓存命中。

    返回 (图, 节点坐标, 缓存命中节点集合)。
    """
    graph = nx.DiGraph()
    positions: dict[str, tuple[float, float]] = {}
    cache_hits: set[str] = set()
    memo: dict[int, int] = {}
    next_id = [0]

    def expand(k: int, depth: int, x_range: tuple[float, float]) -> str:
        nid = f"n{next_id[0]}"
        next_id[0] += 1
        graph.add_node(nid, k=k)
        positions[nid] = ((x_range[0] + x_range[1]) / 2, -depth)

        if k < 2:
            memo[k] = k
            return nid
        if k in memo:
            # 缓存命中：不再展开子树
            cache_hits.add(nid)
            return nid

        mid = (x_range[0] + x_range[1]) / 2
        left = expand(k - 1, depth + 1, (x_range[0], mid))
        right = expand(k - 2, depth + 1, (mid, x_range[1]))
        graph.add_edge(nid, left)
        graph.add_edge(nid, right)
        memo[k] = 1  # 标记已算（值不重要）
        return nid

    expand(n, 0, (0.0, 1.0))
    return graph, positions, cache_hits


def visualize(n: int) -> None:
    graph, positions, cache_hits = trace_memoized_calls(n)

    node_colors = [
        "#95a5a6" if nid in cache_hits else "#2ecc71"
        for nid in graph.nodes
    ]
    labels = {nid: f"F({graph.nodes[nid]['k']})" for nid in graph.nodes}

    plt.figure(figsize=(13, 7))
    nx.draw(
        graph,
        pos=positions,
        labels=labels,
        node_color=node_colors,
        node_size=1200,
        font_size=10,
        edge_color="#7f8c8d",
        arrows=False,
    )

    plt.title(
        f"记忆化后 fib({n}) 的调用树\n"
        f"绿色 = 真正算一次  ｜  灰色 = 缓存直接命中",
        fontsize=13,
    )

    counter: Counter[str] = Counter("hit" if nid in cache_hits else "real" for nid in graph.nodes)
    plt.gcf().text(
        0.78, 0.5,
        (
            "本次调用统计\n"
            + "—" * 18 + "\n"
            + f"实算节点 = {counter['real']}\n"
            + f"缓存命中 = {counter['hit']}\n"
            + f"复杂度    = O(n)"
        ),
        fontsize=10,
        verticalalignment="center",
        bbox=dict(boxstyle="round", facecolor="#ecf0f1", edgecolor="#95a5a6"),
    )

    plt.axis("off")
    plt.tight_layout()
    save_and_show(f"02_memoization_tree_fib{n}.png")


# ────────────────────────────────────────────────────────────
# 主程序
# ────────────────────────────────────────────────────────────

def main() -> None:
    parse_plot_args()
    print("=" * 60)
    print("第 02 章：记忆化（Top-Down）")
    print("=" * 60)

    for n in (10, 20, 40, 80):
        memo: dict[int, int] = {}
        result = fib_memo(n, memo)
        print(f"fib_memo({n:>3}) = {result:>20}   缓存条目数 = {len(memo)}")

    print(
        "\n→ fib(80) 在朴素递归下会算到天荒地老，"
        "记忆化下只用 80 个缓存条目就拿到答案。\n"
        "→ 缓存条目数 = O(n)，时间复杂度 = O(n)，空间复杂度 = O(n)。\n"
    )

    print("生成 fib(6) 的记忆化调用树（和 01 章的红色暴力树对比着看）...")
    visualize(6)


if __name__ == "__main__":
    main()
