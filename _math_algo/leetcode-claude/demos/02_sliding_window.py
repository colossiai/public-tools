"""
02 · 滑动窗口 —— 无重复字符的最长子串

═══════════════════════════════════════════════════════════════
【题目】 LeetCode 3 — 无重复字符的最长子串
═══════════════════════════════════════════════════════════════

给定字符串 s，找出其中「不含重复字符」的最长子串的长度。

    s = "abcabcbb"
    答案 = 3      （最长无重复子串是 "abc"）

═══════════════════════════════════════════════════════════════
【什么时候想到这个套路】
═══════════════════════════════════════════════════════════════

触发信号：
  - 「连续」的子数组 / 子串（注意：连续，不是任意子序列）。
  - 求「最长 / 最短」满足某条件的区间，或「不超过 K 个 xxx」。
  - 窗口内的合法性随长度单调变化——加元素更容易违规，删元素恢复合法。

═══════════════════════════════════════════════════════════════
【思路】右指针扩张，违规时左指针收缩
═══════════════════════════════════════════════════════════════

维护一个窗口 [left, right]，用一个集合/字典记录窗口内出现的字符。

    s = "a b c a b c b b"
         └───────┘
        left    right

  - right 每次向右吃进一个新字符。
  - 如果新字符已经在窗口里（重复了），就不停地从左边吐出字符、
    left 右移，直到窗口重新变得「无重复」。
  - 每一步用当前窗口长度 (right - left + 1) 更新答案。

为什么每个字符最多进出窗口各一次？left 和 right 都只增不减，
所以总移动次数是 O(n)，不是 O(n²)。

    吃进重复的 'a'（原窗口 "abc"）：
      abc a bcbb
      └─┘             窗口 "abc"，遇到第二个 'a' 重复
       ↓ 从左吐出 'a'
        bca ...       窗口变成 "bca"，恢复无重复

═══════════════════════════════════════════════════════════════
【复杂度】 时间 O(n)  空间 O(min(n, 字符集大小))
═══════════════════════════════════════════════════════════════
"""
from __future__ import annotations


# ────────────────────────────────────────────────────────────
# 主例：无重复字符的最长子串（LC3）—— 窗口内容由「合法性」驱动
# ────────────────────────────────────────────────────────────

def length_of_longest_substring(s: str) -> int:
    """返回不含重复字符的最长子串长度。"""
    seen: set[str] = set()   # 记录当前窗口 [left, right] 内的字符
    left = 0
    best = 0

    for right, ch in enumerate(s):
        # 若新字符已在窗口内，说明产生重复：从左边收缩直到 ch 被移出
        while ch in seen:
            seen.discard(s[left])
            left += 1
        # 此时窗口重新合法，把新字符纳入
        seen.add(ch)
        # 用当前合法窗口长度刷新最优
        best = max(best, right - left + 1)

    return best


# ────────────────────────────────────────────────────────────
# 第二例：长度最小的子数组（LC209）—— 目标驱动的可变窗口
# ────────────────────────────────────────────────────────────

def min_subarray_len(target: int, nums: list[int]) -> int:
    """求和 >= target 的最短连续子数组长度；不存在返回 0（元素均为正）。"""
    left = 0
    total = 0                 # 当前窗口的元素和
    best = len(nums) + 1      # 用一个不可能达到的大值作哨兵

    for right, x in enumerate(nums):
        total += x            # 右指针扩张：吃进 nums[right]
        # 一旦满足条件，就尽量收缩左边界，找「刚好满足」的最短窗口
        while total >= target:
            best = min(best, right - left + 1)
            total -= nums[left]
            left += 1

    # 从没满足过 target，则哨兵未被更新
    return best if best <= len(nums) else 0


# ────────────────────────────────────────────────────────────
# 主程序：断言 + 可读演示
# ────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("=" * 60)
    print("02 · 滑动窗口")
    print("=" * 60)

    # ---- 断言：证明正确性 ----
    assert length_of_longest_substring("abcabcbb") == 3   # "abc"
    assert length_of_longest_substring("bbbbb") == 1       # "b"
    assert length_of_longest_substring("pwwkew") == 3      # "wke"
    assert length_of_longest_substring("") == 0

    assert min_subarray_len(7, [2, 3, 1, 2, 4, 3]) == 2    # [4,3]
    assert min_subarray_len(4, [1, 4, 4]) == 1             # [4]
    assert min_subarray_len(11, [1, 1, 1, 1, 1]) == 0      # 凑不到

    # ---- 演示轨迹：无重复最长子串的窗口变化 ----
    print("\n【固定条件窗口】最长无重复子串   s=\"abcabcbb\"")
    s = "abcabcbb"
    seen: set[str] = set()
    left = 0
    best = 0
    for right, ch in enumerate(s):
        while ch in seen:
            seen.discard(s[left])
            left += 1
        seen.add(ch)
        best = max(best, right - left + 1)
        window = s[left:right + 1]
        print(f"  right={right}('{ch}') 窗口=\"{window}\" 长度={len(window)} 最优={best}")
    print(f"  => 答案 {best}")

    # ---- 演示轨迹：最短子数组的窗口伸缩 ----
    print("\n【可变窗口】长度最小子数组   target=7, nums=[2,3,1,2,4,3]")
    target, nums = 7, [2, 3, 1, 2, 4, 3]
    left = 0
    total = 0
    best = len(nums) + 1
    for right, x in enumerate(nums):
        total += x
        while total >= target:
            best = min(best, right - left + 1)
            print(f"  窗口 nums[{left}:{right + 1}]={nums[left:right + 1]} "
                  f"和={total} >= {target} -> 长度={right - left + 1}")
            total -= nums[left]
            left += 1
    print(f"  => 最短长度 {best if best <= len(nums) else 0}")

    print("\n全部断言通过 ✓")
