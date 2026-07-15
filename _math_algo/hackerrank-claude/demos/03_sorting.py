"""
03 · 排序 —— 归并排序数逆序对 & 贪心买玩具

═══════════════════════════════════════════════════════════════
【题目】 HackerRank "Merge Sort: Counting Inversions"（数逆序对）
═══════════════════════════════════════════════════════════════

给一个数组，问需要多少次「相邻元素交换」才能把它排成升序。这个次数
恰好等于数组的「逆序对」数目：满足 i < j 但 a[i] > a[j] 的下标对个数。

    a = [2, 1, 3, 1, 2]
    逆序对：(2,1)(2,1)(3,1)(3,2)      答案 = 4
      对应下标：(0,1)(0,3)(2,3)(2,4)

═══════════════════════════════════════════════════════════════
【什么时候想到这个套路】
═══════════════════════════════════════════════════════════════

触发信号（归并排序顺带计数）：
  - 「逆序对 / 需要多少次相邻交换排好序 / 有多少对前大后小」。
  - 暴力两重循环数逆序对是 O(n²)，n 到 10⁵ 就爆。
  - 归并排序天生「一边合并一边能数出跨越左右两半的逆序对」，把
    计数搭在归并的「合并」步骤里，白嫖出 O(n log n)。

触发信号（排序 + 贪心）：
  - 「预算 / 容量有限，问最多能拿几个」，且「拿哪个不影响别的价值」。
  - 先排序，再从最便宜（最小代价）的开始拿，能拿就拿。

═══════════════════════════════════════════════════════════════
【思路一】归并排序：合并两个有序半区时，数「左边还剩几个」
═══════════════════════════════════════════════════════════════

  归并把数组分成左右两半，各自递归排好序，再「合并」。
  合并时用两个指针 i(左)、j(右)，每次取较小的往结果里放：

    左半 [2, 3]      右半 [1, 2]        （已各自有序）
          i↑              j↑

    比较 左[i]=2 与 右[j]=1：右边更小，先放 1。
    关键：此刻左半从 i 起「还没放出去」的每个元素都 > 这个 1，
          它们的下标都比 1 小 —— 于是一次性 +（左半剩余个数）个逆序对！

  只有「右元素被优先取出」时才产生跨半逆序对，且一次补齐一整段，
  这正是 O(n log n) 的来源。

═══════════════════════════════════════════════════════════════
【思路二】买玩具：价格升序排序后，从最便宜的贪心地买
═══════════════════════════════════════════════════════════════

    prices = [1, 12, 5, 111, 200, 1000, 10], k = 50
    排序 -> [1, 5, 10, 12, 111, 200, 1000]
    依次累加：1(累1) 5(累6) 10(累16) 12(累28) | 111 -> 累139 > 50 停
    能买 4 个。

  为什么贪心对？要「个数最多」，那把预算花在越便宜的上越划算，
  buy 便宜的绝不会挤掉「原本能买的更贵的」——因为个数才是目标。

═══════════════════════════════════════════════════════════════
【复杂度】
═══════════════════════════════════════════════════════════════

  逆序对：  时间 O(n log n)   空间 O(n)（归并需要临时数组）
  买玩具：  时间 O(n log n)（瓶颈是排序）  空间 O(1) 额外
"""
from __future__ import annotations

import io


# ────────────────────────────────────────────────────────────
# HackerRank 输入格式备忘
#   Counting Inversions（多测试用例）：
#     第一行：t            （用例组数）
#     每组两行：n / 该数组的 n 个整数
#   Mark and Toys：
#     第一行：n k          （玩具数 n，预算 k）
#     第二行：n 个价格
# 下面的 parse 用 io.StringIO 模拟 stdin，可运行可断言。
# ────────────────────────────────────────────────────────────

def parse_inversion_cases(fake_stdin: str) -> list[list[int]]:
    """把 't\\n n\\n arr\\n ...' 解析成若干个数组。"""
    reader = io.StringIO(fake_stdin)
    t = int(reader.readline().strip())              # 先读用例组数 t
    cases = []
    for _ in range(t):
        n = int(reader.readline().strip())          # 每组第一行是长度 n
        arr = list(map(int, reader.readline().split()))
        assert len(arr) == n, f"说好 {n} 个，实际 {len(arr)} 个"
        cases.append(arr)
    return cases


def parse_toys(fake_stdin: str) -> tuple[list[int], int]:
    """把 'n k\\n p0 p1 ...' 解析成 (价格数组, 预算 k)。"""
    reader = io.StringIO(fake_stdin)
    n, k = map(int, reader.readline().split())      # 第一行：玩具数 n、预算 k
    prices = list(map(int, reader.readline().split()))
    assert len(prices) == n, f"说好 {n} 个，实际 {len(prices)} 个"
    return prices, k


# ────────────────────────────────────────────────────────────
# 主例：归并排序数逆序对（HackerRank Counting Inversions）
# ────────────────────────────────────────────────────────────

def count_inversions(a: list[int]) -> int:
    """返回数组 a 的逆序对数目（= 排成升序所需的相邻交换次数）。"""

    def merge_sort(arr: list[int]) -> tuple[list[int], int]:
        """返回 (排好序的新数组, 该段内部的逆序对数)。"""
        if len(arr) <= 1:
            return arr, 0                   # 单个或空段：已有序，0 个逆序对

        mid = len(arr) // 2
        left, inv_l = merge_sort(arr[:mid])    # 递归左半，拿到左半内部逆序对
        right, inv_r = merge_sort(arr[mid:])   # 递归右半

        merged: list[int] = []
        i = j = 0
        inv_cross = 0                       # 跨越左右两半的逆序对
        while i < len(left) and j < len(right):
            if left[i] <= right[j]:
                # 左边更小或相等：正常取左，不产生逆序对
                merged.append(left[i])
                i += 1
            else:
                # 右边更小：left[i:] 里剩下的每个都 > right[j] 且下标更靠前
                # 一次性补上「左半剩余个数」个逆序对
                merged.append(right[j])
                j += 1
                inv_cross += len(left) - i
        # 收尾：把还没取完的那一半直接接上（另一半已空，不再产生逆序对）
        merged.extend(left[i:])
        merged.extend(right[j:])
        return merged, inv_l + inv_r + inv_cross

    _, total = merge_sort(a)
    return total


# ────────────────────────────────────────────────────────────
# 第二例：预算内最多买几个玩具（HackerRank Mark and Toys）
# ────────────────────────────────────────────────────────────

def max_toys(prices: list[int], k: int) -> int:
    """价格升序后从最便宜的贪心地买，返回预算 k 内能买的最多个数。"""
    count = 0
    spent = 0
    for p in sorted(prices):                # 排序：先面对最便宜的玩具
        if spent + p > k:                   # 加上它会超预算，后面只会更贵，收工
            break
        spent += p                          # 买下它，累加花费
        count += 1
    return count


# ────────────────────────────────────────────────────────────
# 主程序：断言 + 可读演示
# ────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("=" * 63)
    print("第 03 章：排序 —— Sorting")
    print("=" * 63)

    # ---- 断言：逆序对（含 HackerRank 官方样例）----
    assert count_inversions([2, 1, 3, 1, 2]) == 4
    assert count_inversions([1, 1, 1, 2, 2]) == 0     # 已升序，0 个
    assert count_inversions([2, 1, 3, 1, 2]) == 4
    assert count_inversions([7, 5, 3, 1]) == 6        # 完全逆序 = C(4,2)
    assert count_inversions([]) == 0                  # 空数组不崩
    # 与暴力法交叉验证
    def brute(a):
        return sum(1 for i in range(len(a)) for j in range(i + 1, len(a)) if a[i] > a[j])
    for arr in ([3, 1, 2], [5, 4, 3, 2, 1], [1, 3, 2, 4, 6, 5]):
        assert count_inversions(arr) == brute(arr)

    # ---- 断言：stdin 解析 + 端到端 ----
    cases = parse_inversion_cases("2\n5\n2 1 3 1 2\n5\n1 1 1 2 2\n")
    assert [count_inversions(c) for c in cases] == [4, 0]

    # ---- 断言：买玩具（HackerRank 官方样例）----
    assert max_toys([1, 12, 5, 111, 200, 1000, 10], 50) == 4
    assert max_toys([1, 2, 3, 4], 7) == 3             # 1+2+3=6，+4=10>7
    assert max_toys([5, 5, 5], 4) == 0                # 一个都买不起
    prices, k = parse_toys("7 50\n1 12 5 111 200 1000 10\n")
    assert max_toys(prices, k) == 4

    # ---- 演示轨迹：合并时如何数跨半逆序对 ----
    print("\n【逆序对】a=[2,1,3,1,2] 的归并计数结果")
    a = [2, 1, 3, 1, 2]
    print(f"  数组 {a} -> 逆序对 {count_inversions(a)}（暴力校验 {brute(a)}）")

    # ---- 演示轨迹：贪心买玩具 ----
    print("\n【买玩具】prices=[1,12,5,111,200,1000,10], 预算 k=50")
    prices, k = [1, 12, 5, 111, 200, 1000, 10], 50
    spent, count = 0, 0
    for p in sorted(prices):
        if spent + p > k:
            print(f"  遇到 {p}：花费将达 {spent + p} > {k}，停止")
            break
        spent += p
        count += 1
        print(f"  买入 {p:>3}，已花 {spent:>3}，共 {count} 个")
    print(f"  => 最多买 {count} 个")

    print("\n全部断言通过 ✅")
