"""
01 · 为什么需要动态规划 —— 从一棵长歪了的递归树说起

═══════════════════════════════════════════════════════════════
【思维】凭直觉写出来的递归，到底慢在哪？
═══════════════════════════════════════════════════════════════

我们用一个最简单的例子开场：**斐波那契数列**。

    F(0) = 0
    F(1) = 1
    F(n) = F(n-1) + F(n-2)      （n ≥ 2）

数列：0, 1, 1, 2, 3, 5, 8, 13, 21, ...

如果你从没见过 DP，让你写代码求 F(n)，最自然的写法就是：

    def fib(n):
        if n < 2:
            return n
        return fib(n - 1) + fib(n - 2)

读起来就跟数学定义一样优雅。但你跑一下 fib(40)，会等好几秒；
跑 fib(50)，可能等到生气。

**为什么？**

把 fib(5) 展开成一棵递归树，你会看见这件事：

                       fib(5)
                      /       \\
                fib(4)         fib(3)
                /    \\         /    \\
            fib(3)  fib(2)  fib(2)  fib(1)
            /   \\   ...     ...
        fib(2) fib(1)

注意 ——

  - fib(3) 出现了 **2 次**
  - fib(2) 出现了 **3 次**
  - fib(1) 出现了 **5 次**

这棵树的节点数大约是 1.6^n 级别，最终是 **O(2^n)**。每个子问题都被
独立地、从头到尾算了好多遍。

这就是"暴力递归"的根本病灶：**重叠子问题（overlapping subproblems）**。

只要把这个病灶看穿了，DP 的两个核心思想就呼之欲出：

  1. **算过的就记下来**（→ 02 章：记忆化）
  2. **干脆从小往大反着算**（→ 03 章：表格法）

═══════════════════════════════════════════════════════════════
【方案】本文件做什么
═══════════════════════════════════════════════════════════════

本文件**不修复**朴素递归（那是 02 章的事），只做两件事：

  1. 写出朴素递归 fib(n)，**同时统计每个子问题被调用了多少次**。
  2. 把递归树画出来，**重复出现的节点用红色高亮**，让你一眼看到浪费。

═══════════════════════════════════════════════════════════════
【可视化】
═══════════════════════════════════════════════════════════════

跑完会生成 output/01_recursion_tree.png：
  - 节点 = 一次函数调用
  - 红色节点 = 这个 fib(k) 已经在树的别处算过了
  - 节点旁边的小数字 = 该 fib(k) 总共被调用了几次

如果你看完这张图还觉得"暴力递归没问题"，那 02 章救不了你 🙂
"""
from __future__ import annotations

from collections import Counter

import matplotlib.pyplot as plt
import networkx as nx

from _common import parse_plot_args, save_and_show


# ────────────────────────────────────────────────────────────
# 朴素递归 + 调用计数
# ────────────────────────────────────────────────────────────

call_count: Counter[int] = Counter()


def fib_naive(n: int) -> int:
    """最朴素的递归实现。每次调用都给 call_count 加一笔。"""
    call_count[n] += 1
    if n < 2:
        return n
    return fib_naive(n - 1) + fib_naive(n - 2)


# ────────────────────────────────────────────────────────────
# 把递归树展开成一张图
# ────────────────────────────────────────────────────────────

def build_recursion_tree(n: int) -> tuple[nx.DiGraph, dict[str, tuple[float, float]]]:
    """把 fib(n) 的递归树展开成有向图（每次调用是独立节点）。

    返回 (图, 节点坐标)。坐标按层 + 中序铺开，方便 matplotlib 画。
    """
    graph = nx.DiGraph()
    positions: dict[str, tuple[float, float]] = {}

    # 用一个计数器给每次调用一个唯一 id（同一个 fib(k) 在不同位置算多次时区分开）
    next_id = [0]

    def expand(k: int, depth: int, x_range: tuple[float, float]) -> str:
        nid = f"n{next_id[0]}"
        next_id[0] += 1
        graph.add_node(nid, k=k)
        # 坐标：y 用深度（越深越下），x 用区间中点
        x = (x_range[0] + x_range[1]) / 2
        y = -depth
        positions[nid] = (x, y)
        if k >= 2:
            mid = (x_range[0] + x_range[1]) / 2
            left = expand(k - 1, depth + 1, (x_range[0], mid))
            right = expand(k - 2, depth + 1, (mid, x_range[1]))
            graph.add_edge(nid, left)
            graph.add_edge(nid, right)
        return nid

    expand(n, 0, (0.0, 1.0))
    return graph, positions


def visualize(n: int) -> None:
    graph, positions = build_recursion_tree(n)

    # 统计每个 k 值在树里出现了多少次
    k_count: Counter[int] = Counter(graph.nodes[nid]["k"] for nid in graph.nodes)

    # 颜色：出现 ≥2 次的子问题标红，1 次的标灰
    node_colors = []
    for nid in graph.nodes:
        k = graph.nodes[nid]["k"]
        node_colors.append("#e74c3c" if k_count[k] >= 2 else "#bdc3c7")

    labels = {nid: f"F({graph.nodes[nid]['k']})" for nid in graph.nodes}

    plt.figure(figsize=(14, 8))
    nx.draw(
        graph,
        pos=positions,
        labels=labels,
        node_color=node_colors,
        node_size=1200,
        font_size=9,
        edge_color="#7f8c8d",
        arrows=False,
    )

    # 在图侧边打印每个 k 被调用的次数
    summary_lines = [f"F({k}): 调用 {cnt} 次" for k, cnt in sorted(k_count.items(), reverse=True)]
    plt.gcf().text(
        0.78, 0.5,
        "重复子问题统计\n" + "—" * 18 + "\n" + "\n".join(summary_lines),
        fontsize=10,
        verticalalignment="center",
        bbox=dict(boxstyle="round", facecolor="#ecf0f1", edgecolor="#95a5a6"),
    )

    plt.title(
        f"朴素递归 fib({n}) 的调用树\n"
        f"红色节点 = 重复子问题（被算了不止一次）",
        fontsize=13,
    )
    plt.axis("off")
    plt.tight_layout()
    save_and_show(f"01_recursion_tree_fib{n}.png")


# ────────────────────────────────────────────────────────────
# 主程序
# ────────────────────────────────────────────────────────────

def main() -> None:
    parse_plot_args()
    print("=" * 60)
    print("第 01 章：为什么需要动态规划")
    print("=" * 60)

    for n in (5, 10, 20):
        call_count.clear()
        result = fib_naive(n)
        total_calls = sum(call_count.values())
        print(
            f"\nfib({n}) = {result:>6}   "
            f"总调用次数 = {total_calls:>7}   "
            f"其中 fib(2) 被算了 {call_count[2]} 次"
        )

    print(
        "\n→ 注意 fib(20) 的总调用次数已经过万。\n"
        "  随着 n 增加，调用次数大致按 1.6^n 爆炸。\n"
        "  这就是『重叠子问题』的代价。\n"
    )
    print("生成 fib(6) 的递归树图（小例子方便看清楚）...")
    visualize(6)


if __name__ == "__main__":
    main()
