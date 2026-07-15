"""
03 · 二分查找 / 二分答案 —— lower_bound 与「爱吃香蕉的珂珂」

═══════════════════════════════════════════════════════════════
【题目】 标准二分（lower_bound） + LeetCode 875（爱吃香蕉的珂珂）
═══════════════════════════════════════════════════════════════

主例：在升序数组中求 lower_bound(target)——
      第一个 >= target 的下标（即 target 的插入位置）。

    nums = [1, 3, 3, 5, 8], target = 3   ->  下标 1
    nums = [1, 3, 3, 5, 8], target = 4   ->  下标 3
    nums = [1, 3, 3, 5, 8], target = 9   ->  下标 5（插到末尾）

附例：LC875 爱吃香蕉的珂珂。piles 每堆香蕉，警卫 h 小时后回来。
      珂珂每小时最多吃一堆里的 speed 根（吃不完也得等下一小时）。
      求能在 h 小时内吃完的「最小速度」。

    piles = [3, 6, 7, 11], h = 8   ->  4

═══════════════════════════════════════════════════════════════
【什么时候想到这个套路】
═══════════════════════════════════════════════════════════════

触发信号（普通二分）：
  - 数据「有序」，找目标 / 找边界（第一个/最后一个满足）。

触发信号（二分答案）：
  - 求「最小的最大值」「最大的最小值」「满足条件的最小/最大 X」。
  - 存在单调的可行性函数 check(x)：x 越大越容易（或越难）成立。
  - 此时不是在数组上二分，而是在「答案的取值空间」上二分。

═══════════════════════════════════════════════════════════════
【思路】统一用「找左边界」模板，避免死循环
═══════════════════════════════════════════════════════════════

区间写成左闭右闭 [lo, hi]，循环条件 lo < hi，收缩时：

    while lo < hi:
        mid = (lo + hi) // 2        # 偏左取中，保证 mid < hi，防死循环
        if check(mid):  hi = mid    # mid 可行，答案在 [lo, mid]，保留 mid
        else:           lo = mid + 1 # mid 不行，答案在 [mid+1, hi]
    return lo                        # lo == hi，即第一个满足 check 的位置

lower_bound 的 check(i) 就是 nums[i] >= target。
二分答案的 check(speed) 就是「用这个速度能否在 h 小时内吃完」。

    答案空间（速度）：1 2 3 [4] 5 6 ... max(piles)
                     不可行 |  可行 ──────────►
    check 单调：速度越大越吃得完，所以边界左侧不可行、右侧可行。
    我们要的是「第一个可行」的速度 = 找左边界。

═══════════════════════════════════════════════════════════════
【复杂度】
═══════════════════════════════════════════════════════════════
  lower_bound：时间 O(log n) 空间 O(1)
  LC875     ：时间 O(n · log(max(piles)))，check 是 O(n)，二分 O(log 值域)
"""
from __future__ import annotations

import math


# ────────────────────────────────────────────────────────────
# 主例：标准二分 —— lower_bound（第一个 >= target 的下标）
# ────────────────────────────────────────────────────────────

def lower_bound(nums: list[int], target: int) -> int:
    """返回第一个 >= target 的下标；若都比 target 小则返回 len(nums)。"""
    # 用左闭右闭区间 [lo, hi]；hi 取 len(nums) 以允许「插到末尾」
    lo, hi = 0, len(nums)
    while lo < hi:
        # 偏左取中：保证 mid 严格小于 hi，收缩时不会卡住
        mid = (lo + hi) // 2
        if nums[mid] >= target:
            # mid 满足条件，答案可能就是 mid，收右边界但保留 mid
            hi = mid
        else:
            # mid 太小，答案一定在 mid 右侧
            lo = mid + 1
    return lo


# ────────────────────────────────────────────────────────────
# 附例：二分答案 —— 爱吃香蕉的珂珂（LC875）
# ────────────────────────────────────────────────────────────

def min_eating_speed(piles: list[int], h: int) -> int:
    """求能在 h 小时内吃完所有香蕉的最小速度。"""

    def can_finish(speed: int) -> bool:
        # 速度固定时，吃第 i 堆要 ceil(pile / speed) 小时（吃不满也占一小时）
        hours = sum(math.ceil(pile / speed) for pile in piles)
        return hours <= h

    # 答案空间：速度至少 1，至多等于最大那堆（一小时吃完一堆足矣）
    lo, hi = 1, max(piles)
    while lo < hi:
        mid = (lo + hi) // 2
        if can_finish(mid):
            # 这个速度够用，尝试更小的速度（找左边界）
            hi = mid
        else:
            # 太慢，吃不完，必须更快
            lo = mid + 1
    return lo


# ────────────────────────────────────────────────────────────
# 主程序：断言 + 可读演示
# ────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("=" * 60)
    print("03 · 二分查找 / 二分答案")
    print("=" * 60)

    # ---- 断言：lower_bound ----
    assert lower_bound([1, 3, 3, 5, 8], 3) == 1
    assert lower_bound([1, 3, 3, 5, 8], 4) == 3
    assert lower_bound([1, 3, 3, 5, 8], 9) == 5
    assert lower_bound([1, 3, 3, 5, 8], 0) == 0
    assert lower_bound([], 5) == 0

    # ---- 断言：LC875 ----
    assert min_eating_speed([3, 6, 7, 11], 8) == 4
    assert min_eating_speed([30, 11, 23, 4, 20], 5) == 30
    assert min_eating_speed([30, 11, 23, 4, 20], 6) == 23

    # ---- 演示轨迹：lower_bound 的区间收缩 ----
    print("\n【标准二分】lower_bound   nums=[1,3,3,5,8], target=4")
    nums, target = [1, 3, 3, 5, 8], 4
    lo, hi = 0, len(nums)
    step = 1
    while lo < hi:
        mid = (lo + hi) // 2
        ok = nums[mid] >= target
        print(f"  step{step}: [lo={lo}, hi={hi}) mid={mid}(={nums[mid]}) "
              f"nums[mid]>={target}? {ok}")
        if ok:
            hi = mid
        else:
            lo = mid + 1
        step += 1
    print(f"  => 插入位置下标 {lo}")

    # ---- 演示轨迹：在速度空间上二分答案 ----
    print("\n【二分答案】爱吃香蕉的珂珂   piles=[3,6,7,11], h=8")
    piles, h = [3, 6, 7, 11], 8
    lo, hi = 1, max(piles)
    step = 1
    while lo < hi:
        mid = (lo + hi) // 2
        hours = sum(math.ceil(p / mid) for p in piles)
        ok = hours <= h
        print(f"  step{step}: 速度区间[{lo},{hi}] 试速度={mid} "
              f"需要{hours}小时 <= {h}? {ok}")
        if ok:
            hi = mid
        else:
            lo = mid + 1
        step += 1
    print(f"  => 最小速度 {lo}")

    print("\n全部断言通过 ✓")
