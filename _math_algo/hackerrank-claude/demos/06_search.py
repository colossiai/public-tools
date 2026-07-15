"""
06 · 搜索 —— 用哈希/双指针把「查找」从 O(n²) 降到 O(n)

═══════════════════════════════════════════════════════════════
【题目】 两道 HackerRank 搜索经典题
═══════════════════════════════════════════════════════════════

① Pairs（主）
   给一个整数数组和差值 k，数出「无序数对 (a,b) 且 a-b == k」的个数
   （元素各不相同）。

     arr=[1,5,3,4,2], k=2  -> 3     （(3,1)(5,3)(4,2)）

② Ice Cream Parlor
   口袋里有 money 元，正好买两种不同口味的冰淇淋（价格数组 cost），
   使两支价格之和恰为 money。返回这两支的下标（1-based，升序）。
   保证有唯一解。

     cost=[1,4,5,3,2], money=4  -> [1, 4]   （1 + 3 = 4）
     cost=[2,2,4,3],   money=4  -> [1, 2]   （2 + 2 = 4）

═══════════════════════════════════════════════════════════════
【什么时候想到这个套路】
═══════════════════════════════════════════════════════════════

  - 「存在/计数 满足某关系的元素对」——> 先问自己：能不能把「另一半」
    预存进哈希集合/字典，从而把「找配对」变成 O(1) 查表？
  - 数「差恰为 k」的对：对每个 x 查 x+k 是否也在集合里（差 <-> 补数）。
  - 数「和恰为 target」的对：对每个 x 查 target-x 是否见过（补数思想）。
  - 若数组「有序」，也可用排序 + 双指针替代哈希（省空间、可去重）。

═══════════════════════════════════════════════════════════════
【思路】
═══════════════════════════════════════════════════════════════

① Pairs —— 两种等价解法：
   (A) 哈希集合：把所有数丢进 set，对每个 x 查 x+k 是否存在。
         seen = {1,5,3,4,2}, k=2
         x=1 找 3? 有 -> +1
         x=3 找 5? 有 -> +1
         x=4 找 6? 无
         x=2 找 4? 有 -> +1     计 3
   (B) 排序 + 双指针：排序后 lo/hi 扫，diff==k 记一对，diff<k 扩大(hi++)，
       diff>k 缩小(lo++)。有序让指针单调移动，O(n)。

         排序: 1 2 3 4 5   k=2
         lo hi 指向的差：目标恰好 2 时计数并双双前进

② Ice Cream Parlor —— 补数哈希：
   边扫边把「值 -> 下标」记进字典。对当前价格 c，先查 money-c 是否
   已经出现过；出现过就凑成一对（先出现的下标在前，保证升序）。
   「先查后存」保证不会把自己和自己配对。

═══════════════════════════════════════════════════════════════
【和「二分 / BFS」的关系】
═══════════════════════════════════════════════════════════════

  「搜索」是个大家族，本章的哈希/双指针只是其中「线性查找的加速」：
    - 二分查找：在「有序」数据里每次砍半，O(log n)。当本章 Pairs 用
      「排序后对每个 x 二分找 x+k」时，就是 O(n log n) 的二分版解法。
    - BFS/DFS：在「图 / 状态空间」里搜索，逐层(BFS)或深入(DFS)扩展。
      哈希集合在这里化身「visited 去重表」，避免重复访问同一状态。
  记忆锚点：哈希=O(1) 查表，二分=有序砍半，BFS=按层扩散。选谁取决于
  数据结构（无序集合 / 有序数组 / 图）。

═══════════════════════════════════════════════════════════════
【复杂度】
═══════════════════════════════════════════════════════════════
  ① Pairs           哈希 O(n) / 双指针 O(n log n)（排序为瓶颈）  空间 O(n)
  ② Ice Cream       时间 O(n)   空间 O(n)
"""
from __future__ import annotations

import io


# ────────────────────────────────────────────────────────────
# 主例 A：Pairs —— 哈希集合，差 <-> 补数
# ────────────────────────────────────────────────────────────

def pairs_hash(k: int, arr: list[int]) -> int:
    """数出差恰为 k 的数对个数（哈希法）。"""
    seen = set(arr)                 # 元素各不相同，直接放进集合便于 O(1) 查
    count = 0
    for x in arr:
        # 若存在 x+k，则 (x+k) - x == k，凑成一对；每对只会在较小的 x 处被数一次
        if x + k in seen:
            count += 1
    return count


# ────────────────────────────────────────────────────────────
# 主例 B：Pairs —— 排序 + 双指针（有序时的等价解）
# ────────────────────────────────────────────────────────────

def pairs_two_pointer(k: int, arr: list[int]) -> int:
    """数出差恰为 k 的数对个数（排序+双指针法）。"""
    a = sorted(arr)                 # 排序后差值随指针单调变化
    lo, hi = 0, 1
    count = 0
    while hi < len(a):
        diff = a[hi] - a[lo]
        if diff == k:
            count += 1
            lo += 1                 # 这对搞定，两端同时前进找下一对
            hi += 1
        elif diff < k:
            hi += 1                 # 差太小：右端右移把差拉大
        else:
            lo += 1                 # 差太大：左端右移把差缩小
            if lo == hi:            # 保证 hi 始终在 lo 右边
                hi += 1
    return count


# ────────────────────────────────────────────────────────────
# 第二例：Ice Cream Parlor —— 补数哈希，先查后存
# ────────────────────────────────────────────────────────────

def icecream_parlor(money: int, cost: list[int]) -> list[int]:
    """买两支价格和为 money 的冰淇淋，返回其 1-based 下标（升序）。"""
    seen: dict[int, int] = {}       # 价格 -> 首次出现的 0-based 下标
    for i, c in enumerate(cost):
        need = money - c            # 想凑够 money，还差一支价格为 need 的
        if need in seen:
            # need 之前就出现过，那个下标更小，放前面 -> 天然升序
            return [seen[need] + 1, i + 1]
        # 先查后存：这样绝不会把当前这一支和它自己配成一对
        seen.setdefault(c, i)       # 用 setdefault 保留「最早」的下标
    return []                       # 题目保证有解，正常不会到这


# ────────────────────────────────────────────────────────────
# HackerRank stdin 解析示范（用 io.StringIO 模拟，可运行可断言）
# ────────────────────────────────────────────────────────────

def parse_pairs(readline) -> tuple[int, list[int]]:
    """
    Pairs 真实输入：
        n k
        a[0] a[1] ... a[n-1]
    """
    n, k = map(int, readline().split())
    arr = list(map(int, readline().split()))
    assert len(arr) == n
    return k, arr


def parse_icecream(readline) -> tuple[int, list[int]]:
    """
    Ice Cream Parlor 单组测试的真实输入：
        money
        n
        c[0] c[1] ... c[n-1]
    （完整题目外层还有一行 T 表示测试组数，这里只解析单组）
    """
    money = int(readline().strip())
    n = int(readline().strip())
    cost = list(map(int, readline().split()))
    assert len(cost) == n
    return money, cost


def _reader(text: str):
    """把字符串包装成「像 stdin 一样能 readline」的读取函数。"""
    return io.StringIO(text).readline


# ────────────────────────────────────────────────────────────
# 主程序：断言 + 可读演示
# ────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("=" * 63)
    print("第 06 章：搜索 —— Search")
    print("=" * 63)

    # ---- 断言：Pairs（两种解法结果必须一致）----
    assert pairs_hash(2, [1, 5, 3, 4, 2]) == 3
    assert pairs_two_pointer(2, [1, 5, 3, 4, 2]) == 3
    assert pairs_hash(1, [1, 2, 3, 4]) == 3
    assert pairs_two_pointer(1, [1, 2, 3, 4]) == 3
    assert pairs_hash(3, [10, 20, 30]) == 0
    assert pairs_two_pointer(3, [10, 20, 30]) == 0
    for kk, data in [(2, [1, 5, 3, 4, 2]), (1, [1, 2, 3, 4]), (5, [1, 3, 5, 8, 6, 4, 2])]:
        assert pairs_hash(kk, data) == pairs_two_pointer(kk, data)

    # ---- 断言：Ice Cream Parlor ----
    assert icecream_parlor(4, [1, 4, 5, 3, 2]) == [1, 4]
    assert icecream_parlor(4, [2, 2, 4, 3]) == [1, 2]
    assert icecream_parlor(6, [1, 3, 4, 5, 6]) == [1, 4]   # 1 + 5

    # ---- 断言：stdin 解析 ----
    assert parse_pairs(_reader("5 2\n1 5 3 4 2\n")) == (2, [1, 5, 3, 4, 2])
    assert parse_icecream(_reader("4\n5\n1 4 5 3 2\n")) == (4, [1, 4, 5, 3, 2])

    # ---- 演示①：Pairs 哈希法查表过程 ----
    print("\n【Pairs · 哈希】arr=[1,5,3,4,2], k=2   对每个 x 查 x+k")
    arr, k = [1, 5, 3, 4, 2], 2
    seen = set(arr)
    cnt = 0
    for x in arr:
        hit = (x + k) in seen
        if hit:
            cnt += 1
        print(f"  x={x} 查 {x+k} in set? {'是 -> 记一对' if hit else '否'} (累计 {cnt})")
    print(f"  => 共 {cnt} 对")

    # ---- 演示②：Pairs 双指针在有序数组上的移动 ----
    print("\n【Pairs · 双指针】排序后 lo/hi 单调移动   k=2")
    a = sorted(arr)
    print(f"  排序后={a}")
    lo, hi, cnt = 0, 1, 0
    while hi < len(a):
        diff = a[hi] - a[lo]
        rel = "==" if diff == k else ("<" if diff < k else ">")
        note = ""
        if diff == k:
            cnt += 1
            note = "  记一对, lo/hi 齐进"
        print(f"  lo={lo}(={a[lo]}) hi={hi}(={a[hi]}) 差={diff} {rel} {k}{note}")
        if diff == k:
            lo += 1
            hi += 1
        elif diff < k:
            hi += 1
        else:
            lo += 1
            if lo == hi:
                hi += 1
    print(f"  => 共 {cnt} 对")

    # ---- 演示③：Ice Cream 补数哈希「先查后存」 ----
    print("\n【Ice Cream】money=4, cost=[1,4,5,3,2]   先查补数再存下标")
    money, cost = 4, [1, 4, 5, 3, 2]
    seen_map: dict[int, int] = {}
    for i, c in enumerate(cost):
        need = money - c
        if need in seen_map:
            print(f"  i={i} c={c} 需补 {need} -> 命中(下标{seen_map[need]}) "
                  f"=> 答案 [{seen_map[need]+1}, {i+1}]")
            break
        print(f"  i={i} c={c} 需补 {need} -> 未见, 存下 {c}->{i}")
        seen_map.setdefault(c, i)

    print("\n全部断言通过 ✅")
