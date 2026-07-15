"""
09 · 图 —— Graphs（并查集数连通分量 · 无权图 BFS 最短路）

═══════════════════════════════════════════════════════════════
【题目】 本文件用两道 HackerRank 图论题覆盖「并查集」与「BFS」
═══════════════════════════════════════════════════════════════

主例 —— Roads and Libraries (HackerRank)：
    有 n 座城市和 m 条候选道路。每座城市要么直接建一座图书馆
    （花费 c_lib），要么通过修路连到某座「有图书馆的城市」
    （每条路花费 c_road）。目标：让每座城市都能访问到图书馆，
    求最小总花费。

    关键洞察：
      - 若 c_lib <= c_road：每座城市各自建馆最划算 → n × c_lib。
      - 否则：每个连通分量里只建 1 座馆，其余城市靠修路连过去。
        一个 size 个城市的连通分量，需要 (size-1) 条路把它们串起来。
        该分量花费 = c_lib + (size-1) × c_road。

        n=3, c_lib=2, c_road=1, 道路 [(1,2),(3,1),(2,3)]
        三城连成 1 个分量 → 建 1 馆 + 2 条路 = 2 + 2×1 = 4

配菜 —— BFS: Shortest Reach in a Graph (HackerRank)：
    无权无向图，从起点 s 出发，每条边「长度固定为 6」。求 s 到
    其余每个节点的最短距离；不可达记 -1。

        4 个节点(1..4)，边 1-2、1-3，起点 s=1
        到 2：6   到 3：6   到 4：不可达 -1

═══════════════════════════════════════════════════════════════
【什么时候想到这个套路】
═══════════════════════════════════════════════════════════════

  - 「分组 / 连通分量 / 反复合并两点」→ 并查集，近乎 O(1) 合并查询。
  - 「无权图 / 每步代价相同 / 求最少步数」→ BFS，第一次到达即最短。
  - Roads and Libraries 这类「建点 vs 连边」的成本权衡题，先想清楚
    每个连通分量内部怎么最省，再把各分量成本相加。

═══════════════════════════════════════════════════════════════
【思路】
═══════════════════════════════════════════════════════════════

① Roads and Libraries（并查集数连通分量）：
   - 用并查集把所有由道路相连的城市合并成若干连通分量。
   - 若建馆比修路还便宜（c_lib <= c_road）→ 干脆每城一馆。
   - 否则逐个分量结算：每个分量 1 座馆 + (size-1) 条路。
   - 把每个分量的花费加起来就是答案。

       分量 A: {1,2,3} size=3 → c_lib + 2·c_road
       分量 B: {4}     size=1 → c_lib + 0
       总花费 = 各分量之和

② BFS 最短路（无权图 · 边权固定）：
   - 从 s 出发，按「层」向外扩展；第 k 层的节点距离 = k × 6。
   - 用 deque 做队列，dist 数组兼当「是否访问过」（-1 表示未访问）。
   - 第一次把某节点入队时就定下它的最短距离，之后不再更新。

       s=1 →(6)→ 2, 3 →(12)→ 它们的邻居 ...
       未被 BFS 触达的节点保持 -1。

═══════════════════════════════════════════════════════════════
【复杂度】
═══════════════════════════════════════════════════════════════

  - Roads and Libraries：并查集处理 m 条边，近乎 O(m + n)。
  - BFS 最短路：每个节点、每条边各处理一次，O(V + E)。
"""
from __future__ import annotations

import io
from collections import deque


# ────────────────────────────────────────────────────────────
# 并查集（Union-Find）：路径压缩 + 按秩合并，两题主例的基石
# ────────────────────────────────────────────────────────────

class UnionFind:
    """并查集：维护若干不相交集合，支持快速合并与查询。"""

    def __init__(self, n: int) -> None:
        self.parent = list(range(n))   # 初始每个元素自成一组，父亲是自己
        self.rank = [0] * n            # 秩 ≈ 树高，用于按秩合并
        self.size = [1] * n            # 每个根所在集合的元素个数
        self.count = n                 # 当前连通分量个数

    def find(self, x: int) -> int:
        # 路径压缩：一路把沿途节点直接挂到根上，下次查询更快
        while self.parent[x] != x:
            self.parent[x] = self.parent[self.parent[x]]  # 隔代压缩
            x = self.parent[x]
        return x

    def union(self, x: int, y: int) -> bool:
        rx, ry = self.find(x), self.find(y)
        if rx == ry:                   # 本来就在同一组，无需合并
            return False
        # 按秩合并：把矮树挂到高树下，避免树越长越高
        if self.rank[rx] < self.rank[ry]:
            rx, ry = ry, rx
        self.parent[ry] = rx
        self.size[rx] += self.size[ry]  # 大根吸收小根的元素数
        if self.rank[rx] == self.rank[ry]:
            self.rank[rx] += 1         # 两树等高，合并后高度 +1
        self.count -= 1                # 合并一次，连通分量少一个
        return True


# ────────────────────────────────────────────────────────────
# 主例：Roads and Libraries —— 并查集数连通分量 + 成本权衡
# ────────────────────────────────────────────────────────────

def roads_and_libraries(
    n: int, c_lib: int, c_road: int, roads: list[tuple[int, int]]
) -> int:
    # 特判：建馆不比修路贵，那就每座城市各建一座，最省心也最省钱
    if c_lib <= c_road:
        return n * c_lib

    # 否则用并查集把道路相连的城市并成连通分量
    uf = UnionFind(n)                  # 城市用 0..n-1 编号
    for u, v in roads:
        uf.union(u, v)

    # 逐个「分量的根」结算：每个分量建 1 座馆 + (size-1) 条路
    total = 0
    for city in range(n):
        if uf.find(city) == city:      # 只在分量的代表元处结算一次
            size = uf.size[city]
            total += c_lib + (size - 1) * c_road
    return total


# ────────────────────────────────────────────────────────────
# 配菜：BFS Shortest Reach —— 无权图单源最短路（边权固定 6）
# ────────────────────────────────────────────────────────────

EDGE_WEIGHT = 6  # HackerRank 本题规定每条边长度固定为 6


def shortest_reach(n: int, edges: list[tuple[int, int]], start: int) -> list[int]:
    """
    返回从 start 到其余每个节点的最短距离（不含 start 自己）。
    节点编号 1..n，start 用 1-based。不可达为 -1。
    """
    # 邻接表：graph[u] 存 u 的所有邻居（无向图两端都加）
    graph: list[list[int]] = [[] for _ in range(n + 1)]
    for u, v in edges:
        graph[u].append(v)
        graph[v].append(u)

    # dist 兼当「访问标记」：-1 表示还没到达过
    dist = [-1] * (n + 1)
    dist[start] = 0
    queue = deque([start])
    while queue:
        cur = queue.popleft()
        for nxt in graph[cur]:
            if dist[nxt] == -1:        # 第一次到达 nxt，此刻即最短
                dist[nxt] = dist[cur] + EDGE_WEIGHT
                queue.append(nxt)      # 入队，稍后从它继续向外扩展

    # 输出格式：按 1..n 顺序，跳过起点自身
    return [dist[node] for node in range(1, n + 1) if node != start]


# ────────────────────────────────────────────────────────────
# HackerRank stdin 解析：两题的真实输入格式（用 StringIO 模拟）
# ────────────────────────────────────────────────────────────

def parse_roads_and_libraries(text: str) -> tuple[int, int, int, list[tuple[int, int]]]:
    """
    Roads and Libraries 输入格式（单组，城市 1-based，这里转成 0-based）：
        第一行  n m c_lib c_road
        接下来 m 行，每行两个城市编号表示一条路
    """
    r = io.StringIO(text)
    n, m, c_lib, c_road = map(int, r.readline().split())
    roads = []
    for _ in range(m):
        u, v = map(int, r.readline().split())
        roads.append((u - 1, v - 1))   # 转 0-based，配合 UnionFind
    return n, c_lib, c_road, roads


def parse_shortest_reach(text: str) -> tuple[int, list[tuple[int, int]], int]:
    """
    BFS Shortest Reach 输入格式（单组，节点保持 1-based）：
        第一行  n m
        接下来 m 行，每行两个节点表示一条边
        最后一行 s（起点）
    """
    r = io.StringIO(text)
    n, m = map(int, r.readline().split())
    edges = []
    for _ in range(m):
        u, v = map(int, r.readline().split())
        edges.append((u, v))
    s = int(r.readline().strip())
    return n, edges, s


# ────────────────────────────────────────────────────────────
# 主程序：assert 验证 + 可读演示
# ────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("=" * 63)
    print("第 09 章：图 —— Graphs（并查集 · BFS 最短路）")
    print("=" * 63)

    # ---- Roads and Libraries ----
    # n=3, 建馆2 修路1：修路更便宜，三城连一片 → 1馆 + 2路 = 4
    assert roads_and_libraries(3, 2, 1, [(0, 1), (2, 0), (1, 2)]) == 4
    # 建馆更便宜（1 < 2）：每城各建一馆 → 3×1 = 3
    assert roads_and_libraries(3, 1, 2, [(0, 1), (2, 0), (1, 2)]) == 3
    # 两个分量 {0,1,2} 与 {3,4,5}，各 1 馆 + 2 路 → 2×(3 + 2×2) = 14
    assert roads_and_libraries(6, 3, 2, [(0, 1), (1, 2), (3, 4), (4, 5)]) == 14
    # 没有任何路：每城被迫各建一馆 → 5×6 = 30（此处 c_lib < c_road 也成立）
    assert roads_and_libraries(5, 6, 100, []) == 30
    # 验证 stdin 解析后接算法（输入用 1-based）
    n, c_lib, c_road, roads = parse_roads_and_libraries("3 3 2 1\n1 2\n3 1\n2 3\n")
    assert roads_and_libraries(n, c_lib, c_road, roads) == 4

    print("\n[Roads and Libraries · 并查集]")
    print("  n=3, c_lib=2, c_road=1, 三城连成一片")
    print(f"  → 最小花费 = {roads_and_libraries(3, 2, 1, [(0, 1), (2, 0), (1, 2)])}"
          f"  (1 座馆 + 2 条路)")

    # ---- BFS: Shortest Reach ----
    # 4 节点，边 1-2、1-3，起点 1：到 2=6, 到 3=6, 到 4=-1
    assert shortest_reach(4, [(1, 2), (1, 3)], 1) == [6, 6, -1]
    # 链 1-2-3-4，起点 1：6, 12, 18
    assert shortest_reach(4, [(1, 2), (2, 3), (3, 4)], 1) == [6, 12, 18]
    # 起点在中间：链 1-2-3，起点 2 → 到 1=6, 到 3=6
    assert shortest_reach(3, [(1, 2), (2, 3)], 2) == [6, 6]
    # 完全孤立：无边，起点 1 → 其余全 -1
    assert shortest_reach(3, [], 1) == [-1, -1]
    # 验证 stdin 解析后接算法
    n, edges, s = parse_shortest_reach("4 2\n1 2\n1 3\n1\n")
    assert shortest_reach(n, edges, s) == [6, 6, -1]

    print("\n[BFS Shortest Reach · 无权图 BFS]")
    print("  4 节点, 边 1-2 / 1-3, 起点 s=1")
    print(f"  → 到节点 2,3,4 的最短距离 = {shortest_reach(4, [(1, 2), (1, 3)], 1)}")
    print("  链 1-2-3-4, 起点 1")
    print(f"  → 到节点 2,3,4 的最短距离 = {shortest_reach(4, [(1, 2), (2, 3), (3, 4)], 1)}")

    print("\n全部断言通过 ✅")
