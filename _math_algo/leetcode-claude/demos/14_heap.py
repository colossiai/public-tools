"""
14 · 堆 / 优先队列 —— 第 K 大 & 前 K 高频 & 动态中位数

═══════════════════════════════════════════════════════════════
【题目】 LeetCode 215 数组中第 K 个最大元素 / LeetCode 347 前 K 个高频元素
═══════════════════════════════════════════════════════════════

LC215：无序数组，返回第 k 大的元素（不是第 k 大的不同元素）。

    nums = [3, 2, 1, 5, 6, 4], k = 2  ->  5

LC347：返回出现频率前 k 高的元素（顺序不限）。

    nums = [1, 1, 1, 2, 2, 3], k = 2  ->  [1, 2]

附加：用「双堆」在数据流中动态维护中位数（LC295 思路）。

═══════════════════════════════════════════════════════════════
【什么时候想到这个套路】
═══════════════════════════════════════════════════════════════

信号：Top-K、第 K 大 / 小、合并 K 个有序序列、动态中位数、
「一边不断进数据一边要最值」。核心能力是 O(log n) 拿到并弹出极值。

Python 的 heapq 是「最小堆」：堆顶永远是最小值。想要最大堆，
把值取负数放进去即可。

═══════════════════════════════════════════════════════════════
【思路】
═══════════════════════════════════════════════════════════════

  LC215：维护一个大小恰为 K 的「最小堆」。遍历所有数，堆没满就塞，
        满了就跟堆顶比——比堆顶大才替换。扫完后堆里就是最大的 K 个数，
        而堆顶（最小的那个）正是第 K 大。
        为什么用大小 K 的最小堆而不是排序？排序 O(n log n)，
        这里是 O(n log k)，当 k 远小于 n 时更省。

  LC347：先用哈希表统计频率，再用堆挑出频率最高的 K 个。
        同样用大小 K 的最小堆（按频率比较），只保留频率最高的 K 个。

  双堆中位数：左半用最大堆、右半用最小堆，保持两堆大小差 ≤ 1。
        中位数就在一个或两个堆顶，取值 O(1)。

═══════════════════════════════════════════════════════════════
【复杂度】
═══════════════════════════════════════════════════════════════

  LC215：时间 O(n log k)，空间 O(k)。
  LC347：时间 O(n log k)，空间 O(n)（哈希表 + 堆）。
  双堆：每次插入 O(log n)，取中位数 O(1)。
"""
from __future__ import annotations

import heapq
from collections import Counter


# ────────────────────────────────────────────────────────────
# LC215 第 K 个最大元素：大小为 K 的最小堆
# ────────────────────────────────────────────────────────────

def find_kth_largest(nums: list[int], k: int) -> int:
    """返回第 k 大的元素。"""
    heap: list[int] = []  # 最小堆，只保留「目前见过的最大的 K 个数」
    for x in nums:
        if len(heap) < k:
            # 堆还没满，直接放入。
            heapq.heappush(heap, x)
        elif x > heap[0]:
            # 堆满了：堆顶是这 K 个里最小的。若 x 比它大，
            # 说明堆顶不该继续留在「最大 K 个」里，弹出旧堆顶换成 x。
            heapq.heapreplace(heap, x)  # 一步完成 pop + push，比分开写更快
    # 堆里正好是最大的 K 个数，堆顶（最小值）就是第 K 大。
    return heap[0]


# ────────────────────────────────────────────────────────────
# LC347 前 K 个高频元素
# ────────────────────────────────────────────────────────────

def top_k_frequent(nums: list[int], k: int) -> list[int]:
    """返回频率前 k 高的元素。"""
    freq = Counter(nums)  # 元素 -> 出现次数

    # 维护大小 K 的最小堆，元素是 (频率, 值)；按频率比较。
    heap: list[tuple[int, int]] = []
    for val, cnt in freq.items():
        if len(heap) < k:
            heapq.heappush(heap, (cnt, val))
        elif cnt > heap[0][0]:
            # 堆顶是当前 K 个里频率最低的；来了更高频的就替换掉它。
            heapq.heapreplace(heap, (cnt, val))

    # 堆里剩下的就是频率最高的 K 个（顺序无所谓，题目不要求排序）。
    return [val for _, val in heap]


# ────────────────────────────────────────────────────────────
# 附加：双堆求数据流中位数（LC295 思路）
# ────────────────────────────────────────────────────────────

class MedianFinder:
    """用两个堆把数据流一分为二，随时 O(1) 取中位数。

    small：最大堆（存较小的一半，堆顶是这半里的最大值）。
           heapq 只有最小堆，所以存入相反数来模拟最大堆。
    large：最小堆（存较大的一半，堆顶是这半里的最小值）。
    约定：len(small) 与 len(large) 相等，或 small 比 large 多 1。
    """

    def __init__(self) -> None:
        self.small: list[int] = []  # 最大堆（存负数）
        self.large: list[int] = []  # 最小堆

    def add_num(self, num: int) -> None:
        # 先无脑丢进 small，再把 small 的最大值挪给 large，
        # 保证「small 的所有元素 <= large 的所有元素」这个分界不乱。
        heapq.heappush(self.small, -num)
        heapq.heappush(self.large, -heapq.heappop(self.small))

        # 再平衡大小：只允许 small 比 large 多 1。
        if len(self.large) > len(self.small):
            heapq.heappush(self.small, -heapq.heappop(self.large))

    def find_median(self) -> float:
        if len(self.small) > len(self.large):
            # 总数为奇数：中位数就是较大一半那个多出来的堆顶。
            return float(-self.small[0])
        # 总数为偶数：取两个堆顶的平均。
        return (-self.small[0] + self.large[0]) / 2


# ────────────────────────────────────────────────────────────
# 主程序：断言正确性 + 打印可读轨迹
# ────────────────────────────────────────────────────────────

if __name__ == "__main__":
    # ---- LC215 ----
    assert find_kth_largest([3, 2, 1, 5, 6, 4], 2) == 5
    assert find_kth_largest([3, 2, 3, 1, 2, 4, 5, 5, 6], 4) == 4
    assert find_kth_largest([1], 1) == 1
    assert find_kth_largest([2, 1], 2) == 1  # 第 2 大 = 最小值

    # ---- LC347 ----
    assert sorted(top_k_frequent([1, 1, 1, 2, 2, 3], 2)) == [1, 2]
    assert top_k_frequent([1], 1) == [1]
    assert sorted(top_k_frequent([4, 4, 5, 5, 6], 2)) == [4, 5]

    # ---- 双堆中位数 ----
    mf = MedianFinder()
    stream = [5, 15, 1, 3]
    expected = [5.0, 10.0, 5.0, 4.0]  # 逐个加入后的中位数
    for x, exp in zip(stream, expected):
        mf.add_num(x)
        assert mf.find_median() == exp

    print("=" * 60)
    print("14 · 堆 / 优先队列")
    print("=" * 60)

    print("\n【LC215 第 K 大】大小为 K 的最小堆，堆顶即答案")
    nums, k = [3, 2, 1, 5, 6, 4], 2
    print(f"  nums = {nums}, k = {k} -> 第 {k} 大 = {find_kth_largest(nums, k)}")

    print("\n【LC347 前 K 高频】先计数再用堆挑 Top-K")
    nums, k = [1, 1, 1, 2, 2, 3], 2
    print(f"  nums = {nums}, k = {k}")
    print(f"  频率 = {dict(Counter(nums))}")
    print(f"  前 {k} 高频 = {sorted(top_k_frequent(nums, k))}")

    print("\n【双堆动态中位数】数据流逐个加入")
    mf = MedianFinder()
    for x in [5, 15, 1, 3]:
        mf.add_num(x)
        print(f"  加入 {x:>2} -> 当前中位数 = {mf.find_median()}")

    print("\n全部断言通过 ✅")
