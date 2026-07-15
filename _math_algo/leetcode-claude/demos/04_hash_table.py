"""
04 · 哈希表 —— 两数之和 与 字母异位词分组

═══════════════════════════════════════════════════════════════
【题目】 LeetCode 1（两数之和） + LeetCode 49（字母异位词分组）
═══════════════════════════════════════════════════════════════

主例 LC1：给定一个整数数组 nums 和目标值 target，返回「和为 target」
          的两个数的下标。数组「无序」，每个输入只有一个答案。

    nums = [2, 7, 11, 15], target = 9   ->  [0, 1]

附例 LC49：把字符串数组里互为字母异位词的分到一组。
           （异位词：字母种类和个数完全相同，只是顺序不同。）

    ["eat","tea","tan","ate","nat","bat"]
    ->  [["eat","tea","ate"], ["tan","nat"], ["bat"]]

═══════════════════════════════════════════════════════════════
【什么时候想到这个套路】
═══════════════════════════════════════════════════════════════

触发信号：
  - 查重 / 计数 / 配对（两数之和），需要 O(1) 判断「见过没」。
  - 数据「无序」而暴力双重循环 O(n²) 太慢。
  - 需要把「某种特征相同」的元素归类——设计一个能代表该特征的 key。
  - 前缀和 + 目标差（进阶）也常配哈希。

核心思想一句话：**空间换时间，把「查找」从 O(n) 降到 O(1)。**

═══════════════════════════════════════════════════════════════
【思路一】两数之和：边遍历边记「我需要的另一半」
═══════════════════════════════════════════════════════════════

不要先建表再查（那样要处理「自己配自己」）。而是一次遍历：

    遍历到 x 时，它需要的另一半是 need = target - x。
    如果 need 之前出现过（在哈希表里），当场配对成功。
    否则把 x 自己记进哈希表，留给后面的数来配。

    nums = [2, 7, 11, 15], target = 9
    x=2  need=7  表里没有 7 -> 记 {2:0}
    x=7  need=2  表里有 2！ -> 返回 [0, 1]

这样每个数只被访问一次，且保证配对的是「之前的」元素，天然不会自配。

═══════════════════════════════════════════════════════════════
【思路二】异位词分组：给每组设计一个「规范化 key」
═══════════════════════════════════════════════════════════════

异位词的共同特征：排序后的字符串相同（"eat"->"aet"，"tea"->"aet"）。
于是用「排序后的字符串」当 key，把原词丢进对应的桶里。

    "eat" -> key "aet"
    "tea" -> key "aet"   同一个桶
    "tan" -> key "ant"
    ...

    key 也可以用「26 个字母的计数元组」，避免 O(k log k) 的排序，
    但排序版本最直观，这里用它。

═══════════════════════════════════════════════════════════════
【复杂度】
═══════════════════════════════════════════════════════════════
  LC1 ：时间 O(n)         空间 O(n)
  LC49：时间 O(n·k log k) 空间 O(n·k)   （n 个词，每词长 k）
"""
from __future__ import annotations

from collections import defaultdict


# ────────────────────────────────────────────────────────────
# 主例：两数之和（LC1）—— 一次遍历，边查边记
# ────────────────────────────────────────────────────────────

def two_sum(nums: list[int], target: int) -> list[int]:
    """返回和为 target 的两个数的下标。"""
    seen: dict[int, int] = {}   # 值 -> 下标，记录「已经走过的数」

    for i, x in enumerate(nums):
        need = target - x       # x 要凑成 target，还差 need
        if need in seen:
            # 之前恰好见过 need，配对成功（seen 只存更早的元素，不会自配）
            return [seen[need], i]
        # 没配上，把 x 自己登记，等后面的数来找它
        seen[x] = i

    return []


# ────────────────────────────────────────────────────────────
# 附例：字母异位词分组（LC49）—— 排序后的串作 key
# ────────────────────────────────────────────────────────────

def group_anagrams(strs: list[str]) -> list[list[str]]:
    """把互为异位词的字符串分到同一组。"""
    buckets: dict[str, list[str]] = defaultdict(list)

    for word in strs:
        # 排序后的字符串是这组异位词的「规范化指纹」
        key = "".join(sorted(word))
        buckets[key].append(word)

    # dict 的插入顺序稳定，返回各桶即为分组结果
    return list(buckets.values())


# ────────────────────────────────────────────────────────────
# 主程序：断言 + 可读演示
# ────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("=" * 60)
    print("04 · 哈希表")
    print("=" * 60)

    # ---- 断言：两数之和 ----
    assert two_sum([2, 7, 11, 15], 9) == [0, 1]
    assert two_sum([3, 2, 4], 6) == [1, 2]
    assert two_sum([3, 3], 6) == [0, 1]

    # ---- 断言：异位词分组（组内、组间顺序无关，转成集合比较）----
    def normalize(groups: list[list[str]]) -> set[frozenset[str]]:
        return {frozenset(g) for g in groups}

    result = group_anagrams(["eat", "tea", "tan", "ate", "nat", "bat"])
    expected = [["eat", "tea", "ate"], ["tan", "nat"], ["bat"]]
    assert normalize(result) == normalize(expected)
    assert group_anagrams([""]) == [[""]]
    assert group_anagrams(["a"]) == [["a"]]

    # ---- 演示轨迹：两数之和的哈希表如何积累 ----
    print("\n【一次遍历配对】两数之和   nums=[2,7,11,15], target=9")
    nums, target = [2, 7, 11, 15], 9
    seen: dict[int, int] = {}
    for i, x in enumerate(nums):
        need = target - x
        hit = need in seen
        print(f"  i={i} x={x:>2} need={need:>2} "
              f"表中有 need? {hit}   当前表={seen}")
        if hit:
            print(f"  => 命中，返回 [{seen[need]}, {i}]")
            break
        seen[x] = i

    # ---- 演示轨迹：异位词如何落桶 ----
    print("\n【规范化 key 归类】异位词分组   ['eat','tea','tan','ate','nat','bat']")
    strs = ["eat", "tea", "tan", "ate", "nat", "bat"]
    buckets: dict[str, list[str]] = defaultdict(list)
    for word in strs:
        key = "".join(sorted(word))
        buckets[key].append(word)
        print(f"  '{word}' -> key '{key}'   桶='{key}'现有 {buckets[key]}")
    print(f"  => 分组 {list(buckets.values())}")

    print("\n全部断言通过 ✓")
