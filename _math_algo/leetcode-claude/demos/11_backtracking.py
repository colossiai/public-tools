"""
11 · 回溯 —— 选择 / 递归 / 撤销选择

═══════════════════════════════════════════════════════════════
【题目】 本文件用三道经典题打磨「回溯」骨架
═══════════════════════════════════════════════════════════════

主例 —— 全排列 (LC46)：
    给一个不含重复数字的数组 nums，返回它所有可能的排列。
    nums = [1, 2, 3] → [[1,2,3],[1,3,2],[2,1,3],[2,3,1],[3,1,2],[3,2,1]]

配菜一 —— 子集 (LC78)：
    返回数组的所有子集（幂集），含空集与自身。
    nums = [1, 2, 3] → [[],[1],[2],[3],[1,2],[1,3],[2,3],[1,2,3]]

配菜二 —— 组合总和 (LC39)：
    给 candidates（无重复）和目标 target，每个数可重复选用任意次，
    返回所有和为 target 的组合。
    candidates = [2, 3, 6, 7], target = 7 → [[2,2,3],[7]]

═══════════════════════════════════════════════════════════════
【什么时候想到这个套路】
═══════════════════════════════════════════════════════════════

看到「列出所有 …」就该警觉：排列、组合、子集、切割、棋盘、路径。
关键词是 **穷举所有可能** 而不是求一个最优值（那多半是 DP / 贪心）。

数据规模也在提示你：n ≤ 10~20 这种小到离谱的上限，往往就是在暗示
「放心指数级枚举吧」（见 summary 里「从数据规模反推算法」）。

═══════════════════════════════════════════════════════════════
【思路】回溯骨架：选择 → 递归 → 撤销选择
═══════════════════════════════════════════════════════════════

    def backtrack(path, 可选项):
        if 满足终止条件:
            记录 path 的一份拷贝     # 注意要拷贝！path 后面还会被改
            return
        for 选项 in 可选项:
            做选择   (path.append)
            backtrack(新的 path, 剩余可选项)
            撤销选择 (path.pop)      # 回到做选择之前的状态，去试下一个

把整个过程想成一棵「决策树」：每往下走一层就是做一个选择，走到底
（叶子）就得到一个候选答案；然后回退（撤销），换个分支继续。

三道题的差异只在两处：**从哪里开始选**、**终止/剪枝条件**。

  - 全排列：每层可选「所有还没用过的数」，用 used[] 标记 → 长度够了就收。
  - 子集：每个位置都做「选或不选」，其实等价于「每到一个节点就记一次」，
          用 start 保证不回头，避免 [1,2] 和 [2,1] 这种重复。
  - 组合总和：数可重复用，所以递归时 start 不 +1（下次还能选自己）；
          剪枝：排序后一旦「当前数 > 剩余目标」，后面更大的都不用试了。

═══════════════════════════════════════════════════════════════
【复杂度】
═══════════════════════════════════════════════════════════════

回溯本质是枚举，复杂度由「解的数量 × 每个解的长度」主导：
  - 全排列：O(n × n!)。
  - 子集：O(n × 2ⁿ)。
  - 组合总和：与解的个数相关，最坏接近指数级；剪枝能显著剪掉分支。
"""
from __future__ import annotations


# ────────────────────────────────────────────────────────────
# 主例：全排列 (LC46) —— used[] 标记已用元素
# ────────────────────────────────────────────────────────────

def permute(nums: list[int]) -> list[list[int]]:
    result: list[list[int]] = []
    used = [False] * len(nums)         # used[i] 表示 nums[i] 是否已在当前 path 里
    path: list[int] = []

    def backtrack() -> None:
        # 终止条件：路径长度等于 nums，就凑成了一个完整排列
        if len(path) == len(nums):
            result.append(path[:])     # 拷贝一份存起来（path 之后还会被改）
            return
        for i in range(len(nums)):
            if used[i]:                # 这个数已经用过，跳过（排列不能重复用）
                continue
            # 做选择
            used[i] = True
            path.append(nums[i])
            # 递归：在「剩下没用的数」里继续排
            backtrack()
            # 撤销选择：还原现场，好让 nums[i] 能出现在别的位置
            path.pop()
            used[i] = False

    backtrack()
    return result


# ────────────────────────────────────────────────────────────
# 配菜一：子集 (LC78) —— start 防止重复，每个节点都记一次
# ────────────────────────────────────────────────────────────

def subsets(nums: list[int]) -> list[list[int]]:
    result: list[list[int]] = []
    path: list[int] = []

    def backtrack(start: int) -> None:
        # 没有单独的「终止条件」——决策树上每一个节点都是一个合法子集
        result.append(path[:])
        # 从 start 往后选，保证元素下标只增不减，天然去重
        for i in range(start, len(nums)):
            path.append(nums[i])       # 做选择
            backtrack(i + 1)           # 下一层从 i+1 开始，不回头
            path.pop()                 # 撤销选择

    backtrack(0)
    return result


# ────────────────────────────────────────────────────────────
# 配菜二：组合总和 (LC39) —— 可重复用 + 排序剪枝
# ────────────────────────────────────────────────────────────

def combination_sum(candidates: list[int], target: int) -> list[list[int]]:
    result: list[list[int]] = []
    candidates = sorted(candidates)    # 排序是为了剪枝：一旦超了就能整段跳过
    path: list[int] = []

    def backtrack(start: int, remain: int) -> None:
        # 终止条件：剩余目标正好归零 → 找到一个合法组合
        if remain == 0:
            result.append(path[:])
            return
        for i in range(start, len(candidates)):
            # 剪枝：候选已排序，当前数都比 remain 大，后面更大的也不可能凑成
            if candidates[i] > remain:
                break
            path.append(candidates[i])          # 做选择
            # 关键：下一层仍从 i 开始（不是 i+1），因为同一个数可以重复取
            backtrack(i, remain - candidates[i])
            path.pop()                          # 撤销选择

    backtrack(0, target)
    return result


# ────────────────────────────────────────────────────────────
# 主程序：assert 验证 + 可读演示
# ────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("=" * 63)
    print("第 11 章：回溯 —— 选择 / 递归 / 撤销选择")
    print("=" * 63)

    # ---- LC46 全排列 ----
    perms = permute([1, 2, 3])
    assert len(perms) == 6             # 3! = 6 个排列
    assert sorted(perms) == sorted([
        [1, 2, 3], [1, 3, 2], [2, 1, 3],
        [2, 3, 1], [3, 1, 2], [3, 2, 1],
    ])
    assert permute([0]) == [[0]]
    print("\n[LC46 全排列]  nums = [1, 2, 3]")
    print(f"  共 {len(perms)} 个: {perms}")

    # ---- LC78 子集 ----
    subs = subsets([1, 2, 3])
    assert len(subs) == 8              # 2^3 = 8 个子集
    assert [] in subs and [1, 2, 3] in subs
    assert sorted(subs) == sorted([
        [], [1], [2], [3], [1, 2], [1, 3], [2, 3], [1, 2, 3],
    ])
    print("\n[LC78 子集]  nums = [1, 2, 3]")
    print(f"  共 {len(subs)} 个: {subs}")

    # ---- LC39 组合总和 ----
    combos = combination_sum([2, 3, 6, 7], 7)
    assert sorted(combos) == sorted([[2, 2, 3], [7]])
    assert sorted(combination_sum([2, 3, 5], 8)) == sorted(
        [[2, 2, 2, 2], [2, 3, 3], [3, 5]])
    assert combination_sum([2], 1) == []       # 凑不出来 → 空
    print("\n[LC39 组合总和]  candidates = [2, 3, 6, 7], target = 7")
    print(f"  所有组合: {combos}")

    print("\n全部断言通过 ✅")
