"""
10 · 图 —— BFS / DFS / 拓扑排序 / 并查集

═══════════════════════════════════════════════════════════════
【题目】 本文件用三种典型题覆盖「图」这一大类
═══════════════════════════════════════════════════════════════

主例 —— 岛屿数量 (LC200)：
    给一个 '1'（陆地）/ '0'（水）组成的二维网格，上下左右相连的陆地
    算作一座岛。返回岛屿总数。

        1 1 0 0 0
        1 1 0 0 0
        0 0 1 0 0
        0 0 0 1 1

    答案 = 3

配菜一 —— 课程表 (LC207)：
    n 门课，prerequisites 里 [a, b] 表示「学 a 前必须先学 b」。
    判断能否修完所有课（即课程依赖图里有没有环）。

配菜二 —— 并查集 (Union-Find)：
    实现一个通用的并查集类，并用它数「无向图的连通分量个数」。

═══════════════════════════════════════════════════════════════
【什么时候想到这个套路】
═══════════════════════════════════════════════════════════════

看到「连通性 / 网格扩散 / 依赖顺序 / 环 / 分组」就往图上想：

  - 网格里数区域、扩散、洪水填充 → 把格子当节点，DFS / BFS 淹没。
  - 「A 依赖 B」这种先后关系 → 建有向图，拓扑排序（入度法）。
  - 反复合并、查询「这俩在不在一组」→ 并查集。
  - 无权图求最短步数 → BFS（第一次到达即最短）。

═══════════════════════════════════════════════════════════════
【思路】三种典型各自的骨架
═══════════════════════════════════════════════════════════════

① 岛屿数量（网格 DFS / 洪水填充）：
   遍历每个格子，遇到一块没访问过的陆地 → 岛屿数 +1，
   然后从这里出发把整块相连陆地全部「淹掉」（标记已访问），
   避免下次重复计数。

② 课程表（拓扑排序 · 入度法 / Kahn 算法）：
   - 统计每个节点的入度（有多少条依赖指向它）。
   - 把入度为 0 的（无前置要求的课）先入队。
   - 每修完一门课，就把它指向的后继课入度 -1；减到 0 就入队。
   - 最后能修完的课数 == n，说明无环，能全部修完。

③ 并查集：
   - find(x)：找 x 的「代表元」，配合路径压缩把树压扁。
   - union(x, y)：把两个集合合并（按秩合并，挂矮树到高树下）。
   - 连通分量数 = 不同代表元的个数。

═══════════════════════════════════════════════════════════════
【复杂度】
═══════════════════════════════════════════════════════════════

  - 岛屿数量：每个格子访问一次，O(行 × 列)。
  - 课程表：O(V + E)，每个点、每条边各处理常数次。
  - 并查集：路径压缩 + 按秩合并后，近乎 O(1)（反阿克曼函数 α）。
"""
from __future__ import annotations

from collections import deque


# ────────────────────────────────────────────────────────────
# 主例：岛屿数量 (LC200) —— 网格 DFS / 洪水填充
# ────────────────────────────────────────────────────────────

def num_islands(grid: list[list[str]]) -> int:
    if not grid or not grid[0]:
        return 0
    rows, cols = len(grid), len(grid[0])

    def sink(r: int, c: int) -> None:
        # 越界，或不是陆地（是水 / 已淹过）→ 停止扩散
        if r < 0 or r >= rows or c < 0 or c >= cols or grid[r][c] != "1":
            return
        grid[r][c] = "0"               # 就地淹掉，等价于「标记已访问」
        # 向四个方向继续淹，把整座岛连成的陆地一次性清空
        sink(r + 1, c)
        sink(r - 1, c)
        sink(r, c + 1)
        sink(r, c - 1)

    count = 0
    for r in range(rows):
        for c in range(cols):
            if grid[r][c] == "1":      # 碰到一块新陆地
                count += 1             # 说明发现了一座新岛
                sink(r, c)             # 把这座岛整块淹掉，防止重复计数
    return count


# ────────────────────────────────────────────────────────────
# 配菜一：课程表 (LC207) —— 拓扑排序（入度 / Kahn）
# ────────────────────────────────────────────────────────────

def can_finish(num_courses: int, prerequisites: list[list[int]]) -> bool:
    # 建图：graph[b] 里存所有「依赖 b」的后继课；indegree 记每门课的前置数
    graph: list[list[int]] = [[] for _ in range(num_courses)]
    indegree = [0] * num_courses
    for a, b in prerequisites:         # 学 a 前必须先学 b：边 b -> a
        graph[b].append(a)
        indegree[a] += 1               # a 多了一个前置要求

    # 入度为 0 的课没有任何前置，可以最先学
    queue = deque(c for c in range(num_courses) if indegree[c] == 0)
    learned = 0
    while queue:
        course = queue.popleft()
        learned += 1                   # 学完一门
        for nxt in graph[course]:      # 它解锁的后继课，前置数各减 1
            indegree[nxt] -= 1
            if indegree[nxt] == 0:     # 前置全清空 → 可以学了，入队
                queue.append(nxt)

    # 若有环，环上的课入度永远清不成 0，learned 会小于总数
    return learned == num_courses


# ────────────────────────────────────────────────────────────
# 配菜二：并查集 (Union-Find) —— 路径压缩 + 按秩合并
# ────────────────────────────────────────────────────────────

class UnionFind:
    """并查集：维护若干不相交集合，支持快速合并与查询。"""

    def __init__(self, n: int) -> None:
        self.parent = list(range(n))   # 初始每个元素自成一组，父亲是自己
        self.rank = [0] * n            # 秩 ≈ 树高，用于按秩合并
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
        if self.rank[rx] == self.rank[ry]:
            self.rank[rx] += 1         # 两树等高，合并后高度 +1
        self.count -= 1                # 合并一次，连通分量少一个
        return True


def count_components(n: int, edges: list[list[int]]) -> int:
    """用并查集数无向图的连通分量个数。"""
    uf = UnionFind(n)
    for a, b in edges:                 # 每条边把两个端点并到一组
        uf.union(a, b)
    return uf.count


# ────────────────────────────────────────────────────────────
# 主程序：assert 验证 + 可读演示
# ────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("=" * 63)
    print("第 10 章：图 —— BFS / DFS / 拓扑排序 / 并查集")
    print("=" * 63)

    # ---- LC200 岛屿数量 ----
    grid = [
        ["1", "1", "0", "0", "0"],
        ["1", "1", "0", "0", "0"],
        ["0", "0", "1", "0", "0"],
        ["0", "0", "0", "1", "1"],
    ]
    # 注意 num_islands 会就地修改 grid，先复制一份用于展示
    grid_copy = [row[:] for row in grid]
    assert num_islands(grid_copy) == 3
    assert num_islands([["1", "1", "1"], ["0", "1", "0"], ["1", "1", "1"]]) == 1
    assert num_islands([["0", "0"], ["0", "0"]]) == 0
    print("\n[LC200 岛屿数量]")
    for row in grid:
        print("  " + " ".join(row))
    print(f"  → 岛屿数量 = 3")

    # ---- LC207 课程表 ----
    assert can_finish(2, [[1, 0]]) is True            # 0 -> 1，无环
    assert can_finish(2, [[1, 0], [0, 1]]) is False   # 互相依赖，成环
    assert can_finish(4, [[1, 0], [2, 0], [3, 1], [3, 2]]) is True
    print("\n[LC207 课程表]")
    print(f"  4 门课, 依赖 [[1,0],[2,0],[3,1],[3,2]] → 能修完? "
          f"{can_finish(4, [[1, 0], [2, 0], [3, 1], [3, 2]])}")
    print(f"  2 门课, 依赖 [[1,0],[0,1]] (成环)      → 能修完? "
          f"{can_finish(2, [[1, 0], [0, 1]])}")

    # ---- 并查集：连通分量 ----
    # 5 个点，边 0-1, 1-2, 3-4：分成 {0,1,2} 和 {3,4} 两组
    assert count_components(5, [[0, 1], [1, 2], [3, 4]]) == 2
    assert count_components(5, []) == 5               # 没有边 → 各自独立
    assert count_components(4, [[0, 1], [1, 2], [2, 3]]) == 1
    print("\n[并查集 · 连通分量]")
    print(f"  5 个点, 边 [0-1,1-2,3-4] → 连通分量数 = "
          f"{count_components(5, [[0, 1], [1, 2], [3, 4]])}")

    print("\n全部断言通过 ✅")
