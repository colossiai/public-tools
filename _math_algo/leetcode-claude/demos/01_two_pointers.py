"""
01 · 双指针 —— 两数之和 II（有序数组）

═══════════════════════════════════════════════════════════════
【题目】 LeetCode 167 — 两数之和 II（输入有序数组）
═══════════════════════════════════════════════════════════════

给你一个「已按升序排列」的数组 numbers 和目标值 target，请找出两个数，
使它们相加之和等于 target。返回这两个数的下标（从 1 开始）。

    numbers = [2, 7, 11, 15], target = 9
    答案 = [1, 2]     （2 + 7 = 9）

═══════════════════════════════════════════════════════════════
【什么时候想到这个套路】
═══════════════════════════════════════════════════════════════

触发信号（对撞指针）：
  - 数组「有序」+ 找两个数配对满足某条件（和 / 差）。
  - 「有序」是关键——它让我们能靠「大小关系」决定指针往哪走。

触发信号（快慢指针）：
  - 原地移除 / 去重 / 移动元素，要求 O(1) 额外空间。

═══════════════════════════════════════════════════════════════
【思路】对撞指针：一个从头，一个从尾，向中间收缩
═══════════════════════════════════════════════════════════════

    left ─►                       ◄─ right
     ↓                             ↓
   [ 2 ,   7 ,   11 ,   15 ]
     0     1      2      3

    s = numbers[left] + numbers[right]

  - s == target ：找到了，直接返回。
  - s <  target ：和太小，需要更大的数 → left 右移（因为数组有序，
                  right 左移只会让和更小，毫无意义）。
  - s >  target ：和太大，需要更小的数 → right 左移。

为什么正确？每一步都「排除」掉一整行/一整列的组合而不会漏解——
当前 left 与所有大于 right 的位置都试过必然更大，反之亦然。

═══════════════════════════════════════════════════════════════
【复杂度】 时间 O(n)  空间 O(1)
═══════════════════════════════════════════════════════════════

暴力双重循环是 O(n²)；有序这个前提让我们省掉一层循环。
"""
from __future__ import annotations


# ────────────────────────────────────────────────────────────
# 主例：对撞指针 —— 两数之和 II（LC167）
# ────────────────────────────────────────────────────────────

def two_sum_sorted(numbers: list[int], target: int) -> list[int]:
    """在有序数组中找和为 target 的两个数，返回其 1-based 下标。"""
    left, right = 0, len(numbers) - 1

    while left < right:
        s = numbers[left] + numbers[right]
        if s == target:
            # 找到唯一解；题目下标从 1 开始，所以各 +1
            return [left + 1, right + 1]
        elif s < target:
            # 和偏小：只能把左端换成更大的数（数组升序，left 右移变大）
            left += 1
        else:
            # 和偏大：把右端换成更小的数（right 左移变小）
            right -= 1

    # 题目保证有唯一解，正常不会走到这里
    return []


# ────────────────────────────────────────────────────────────
# 第二例：快慢指针 —— 移动零（LC283）
# ────────────────────────────────────────────────────────────

def move_zeroes(nums: list[int]) -> list[int]:
    """把所有 0 移到末尾，保持非零元素的相对顺序（原地修改）。"""
    # slow 指向「下一个非零元素该放的位置」；fast 负责向前扫描
    slow = 0
    for fast in range(len(nums)):
        if nums[fast] != 0:
            # 遇到非零就搬到 slow 处，再把 slow 前进一格
            # slow 之前的区间始终是「已排好的非零前缀」
            nums[slow], nums[fast] = nums[fast], nums[slow]
            slow += 1
    return nums


# ────────────────────────────────────────────────────────────
# 主程序：断言 + 可读演示
# ────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("=" * 60)
    print("01 · 双指针")
    print("=" * 60)

    # ---- 断言：证明正确性 ----
    assert two_sum_sorted([2, 7, 11, 15], 9) == [1, 2]
    assert two_sum_sorted([2, 3, 4], 6) == [1, 3]
    assert two_sum_sorted([-1, 0], -1) == [1, 2]

    assert move_zeroes([0, 1, 0, 3, 12]) == [1, 3, 12, 0, 0]
    assert move_zeroes([0, 0, 1]) == [1, 0, 0]
    assert move_zeroes([1, 2, 3]) == [1, 2, 3]

    # ---- 演示轨迹：对撞指针如何收缩 ----
    print("\n【对撞指针】两数之和 II   numbers=[2,7,11,15], target=9")
    numbers, target = [2, 7, 11, 15], 9
    left, right = 0, len(numbers) - 1
    step = 1
    while left < right:
        s = numbers[left] + numbers[right]
        rel = "==" if s == target else ("<" if s < target else ">")
        print(f"  step{step}: left={left}(={numbers[left]:>2}) "
              f"right={right}(={numbers[right]:>2}) "
              f"和={s:>2} {rel} {target}")
        if s == target:
            print(f"  => 命中，返回下标 [{left + 1}, {right + 1}]")
            break
        elif s < target:
            left += 1
        else:
            right -= 1
        step += 1

    # ---- 演示轨迹：快慢指针如何搬运非零 ----
    print("\n【快慢指针】移动零        nums=[0,1,0,3,12]")
    nums = [0, 1, 0, 3, 12]
    slow = 0
    for fast in range(len(nums)):
        if nums[fast] != 0:
            nums[slow], nums[fast] = nums[fast], nums[slow]
            print(f"  fast={fast} 遇非零 -> 放到 slow={slow}: {nums}")
            slow += 1
    print(f"  => 结果 {nums}")

    print("\n全部断言通过 ✓")
