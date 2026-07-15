"""
05 · 贪心 —— 排序后按局部最优取舍

═══════════════════════════════════════════════════════════════
【题目】 三道 HackerRank 贪心经典题
═══════════════════════════════════════════════════════════════

① Luck Balance（主）
   有 n 场比赛，每场给 (luck, importance)：
     - importance = 0 表示「不重要」，你可以随便输，输了运气值 +luck；
     - importance = 1 表示「重要」，最多只能输 k 场（其余必须赢，赢则 -luck）。
   赢一场会失去它的运气值；输一场会获得它的运气值。求能保留的最大运气总和。

     k=2, 比赛=[(5,1),(1,1),(4,0),(10,0),(5,0)]  -> 25
     解释：不重要的三场(4,10,5)随便输全拿 = 19；重要的两场运气 (5,1) 只有
          两场、未超过 k=2，两场都可以输 -> 再拿 6。合计 19+6 = 25。
          若重要场超过 k 场，就得赢掉运气最小的那些（赢即减运气）。

② Greedy Florist
   n 朵花，k 个朋友一起买。第 i 次「一个人已经买过的花数」为 prev，
   则这次买价格为 c 的花要花 (prev+1)*c。求买下所有花的最小总花费。
   贪心：越贵的花越要「早买」（让它乘的倍数越小），且让 k 人轮流分摊倍数。

     c=[2,5,6], k=3  -> 13   （三人各买一朵，倍数都是 1）
     c=[1,3,5,7,9], k=3 -> 29

③ Max Min（Angry Children）
   从 n 个数里选 k 个，使这 k 个数的「极差(max-min)」最小。
   贪心：排序后，答案一定来自「连续的 k 个」，滑窗取最小差。

     arr=[10,100,300,200,1000,20,30], k=3 -> 20  （选 10,20,30）
     arr=[1,2,3,4,10,20,30,40,100,200], k=4 -> 3  （选 1,2,3,4）

═══════════════════════════════════════════════════════════════
【什么时候想到这个套路】
═══════════════════════════════════════════════════════════════

  - 「使某个总和最大/最小」，且每一步的最优选择不会毁掉后续——> 贪心。
  - 关键前置动作往往是「排序」：让最优候选排到一起，再顺序取舍。
  - 判断贪心是否正确：能不能证明「交换论证」——把非贪心解里的某一步
    换成贪心选择，结果不会变差。能证明就放心用。
  - 「选连续 k 个使极差最小」是排序+滑窗的经典信号（有序后极差=窗口两端差）。

═══════════════════════════════════════════════════════════════
【思路】
═══════════════════════════════════════════════════════════════

① Luck Balance：
     - 不重要的比赛：全部输掉，运气全拿（无约束，白给）。
     - 重要的比赛：按 luck 降序，前 k 场（运气最大的）也输掉拿分，
       剩下的必须赢 -> 减去它们的运气。

② Greedy Florist：
     - 把价格从大到小排序：越贵越先买，吃到最低倍数。
     - 第 i 朵（0-based）的倍数 = i // k + 1
       （k 个人轮流，买满一轮 k 朵后倍数才 +1）

         c 降序: 9  7  5  3  1     k=3
         倍数:   1  1  1  2  2
         花费: 9 + 7 + 5 + 2*3 + 2*1 = 29

③ Max Min：
     - 排序后极差只由窗口两端决定：sorted[i+k-1] - sorted[i]
     - 滑动 i，取最小值。

         arr 排序: 10 20 30 100 200 300 1000   k=3
                   └──窗口──┘  差=20  <- 最小
                      └──窗口──┘ 差=80
                         ...

═══════════════════════════════════════════════════════════════
【复杂度】
═══════════════════════════════════════════════════════════════
  ① Luck Balance    时间 O(n log n)   空间 O(n)
  ② Greedy Florist  时间 O(n log n)   空间 O(1)
  ③ Max Min         时间 O(n log n)   空间 O(1)
                    （瓶颈都在排序；排序后的一趟扫描是 O(n)）
"""
from __future__ import annotations

import io


# ────────────────────────────────────────────────────────────
# 主例：Luck Balance —— 重要场里放掉运气最大的 k 场
# ────────────────────────────────────────────────────────────

def luck_balance(k: int, contests: list[tuple[int, int]]) -> int:
    """contests 为 (luck, importance) 列表，返回可保留的最大运气总和。"""
    total = 0
    important = []

    for luck, importance in contests:
        if importance == 0:
            # 不重要：无约束，输掉直接白拿运气
            total += luck
        else:
            # 重要：先记下来，稍后统一决定输/赢
            important.append(luck)

    # 重要场按运气「降序」——我们最舍得输掉的是运气最大的那些
    important.sort(reverse=True)

    for i, luck in enumerate(important):
        if i < k:
            total += luck   # 前 k 场允许输，拿到运气
        else:
            total -= luck   # 超出配额的必须赢，赢就失去这份运气
    return total


# ────────────────────────────────────────────────────────────
# 第二例：Greedy Florist —— 贵的先买吃低倍数
# ────────────────────────────────────────────────────────────

def get_min_cost(k: int, prices: list[int]) -> int:
    """k 个朋友买下 prices 里所有花，返回最小总花费。"""
    # 价格从大到小：越贵越先买，让它乘到的倍数尽量小
    prices_desc = sorted(prices, reverse=True)

    cost = 0
    for i, price in enumerate(prices_desc):
        # k 人轮流：买满一整轮 k 朵，人均已购数才 +1，倍数随之 +1
        multiplier = i // k + 1
        cost += multiplier * price
    return cost


# ────────────────────────────────────────────────────────────
# 第三例：Max Min —— 排序后滑窗取最小极差
# ────────────────────────────────────────────────────────────

def max_min(k: int, arr: list[int]) -> int:
    """从 arr 里选 k 个，返回最小可能的极差 (max-min)。"""
    arr = sorted(arr)                 # 排序后，最优 k 个必是连续的一段
    best = float("inf")
    # 窗口右端到不了越界：i 最多到 len-k
    for i in range(len(arr) - k + 1):
        spread = arr[i + k - 1] - arr[i]   # 有序段的极差就是两端之差
        best = min(best, spread)
    return int(best)


# ────────────────────────────────────────────────────────────
# HackerRank stdin 解析示范（用 io.StringIO 模拟，可运行可断言）
# ────────────────────────────────────────────────────────────

def parse_luck_balance(readline) -> tuple[int, list[tuple[int, int]]]:
    """
    Luck Balance 真实输入：
        n k
        L[0] T[0]
        ...          （共 n 行，每行 luck 与 importance）
    """
    n, k = map(int, readline().split())
    contests = []
    for _ in range(n):
        luck, importance = map(int, readline().split())
        contests.append((luck, importance))
    return k, contests


def parse_max_min(readline) -> tuple[int, list[int]]:
    """
    Max Min 真实输入：
        n
        k
        然后 n 行、每行一个整数
    """
    n = int(readline().strip())
    k = int(readline().strip())
    arr = [int(readline().strip()) for _ in range(n)]
    return k, arr


def _reader(text: str):
    """把字符串包装成「像 stdin 一样能 readline」的读取函数。"""
    return io.StringIO(text).readline


# ────────────────────────────────────────────────────────────
# 主程序：断言 + 可读演示
# ────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("=" * 63)
    print("第 05 章：贪心 —— Greedy")
    print("=" * 63)

    # ---- 断言：Luck Balance ----
    assert luck_balance(2, [(5, 1), (1, 1), (4, 0), (10, 0), (5, 0)]) == 25
    assert luck_balance(3, [(5, 1), (2, 1), (1, 1), (8, 1), (10, 0), (5, 0)]) == 29
    assert luck_balance(0, [(5, 1), (4, 0)]) == -1   # 重要场全赢：4 - 5

    # ---- 断言：Greedy Florist ----
    assert get_min_cost(3, [2, 5, 6]) == 13
    assert get_min_cost(2, [2, 5, 6]) == 15         # 6+5+2*2 = 15
    assert get_min_cost(3, [1, 3, 5, 7, 9]) == 29
    assert get_min_cost(1, [1, 3, 5, 7, 9]) == 55   # 一个人全买：1*9+2*7+3*5+4*3+5*1

    # ---- 断言：Max Min ----
    assert max_min(3, [10, 100, 300, 200, 1000, 20, 30]) == 20
    assert max_min(2, [1, 2, 3, 4, 10, 20, 30, 40, 100, 200]) == 1
    assert max_min(4, [1, 2, 3, 4, 10, 20, 30, 40, 100, 200]) == 3   # 窗口[1,2,3,4]
    assert max_min(6, [1, 2, 3, 4, 10, 20, 30, 40, 100, 200]) == 19  # 窗口[1..20]

    # ---- 断言：stdin 解析 ----
    assert parse_luck_balance(_reader("2 1\n5 1\n1 0\n")) == (1, [(5, 1), (1, 0)])
    assert parse_max_min(_reader("3\n2\n5\n1\n9\n")) == (2, [5, 1, 9])

    # ---- 演示①：Luck Balance 的输/赢决策 ----
    print("\n【Luck Balance】k=2, 重要场按运气降序取舍")
    contests = [(5, 1), (2, 1), (1, 1), (8, 1)]
    imp = sorted((l for l, t in contests if t == 1), reverse=True)
    k = 2
    print(f"  重要场运气(降序)={imp}, 允许输前 {k} 场")
    for i, luck in enumerate(imp):
        action = "输(+)" if i < k else "赢(-)"
        print(f"    第{i+1}大 luck={luck:>2} -> {action}")

    # ---- 演示②：Greedy Florist 的倍数分配 ----
    print("\n【Greedy Florist】c=[1,3,5,7,9], k=3   贵的先买")
    prices = sorted([1, 3, 5, 7, 9], reverse=True)
    kk, total = 3, 0
    for i, p in enumerate(prices):
        mult = i // kk + 1
        total += mult * p
        print(f"    第{i+1}朵 price={p} 倍数={mult} -> +{mult*p} (累计 {total})")
    print(f"  => 最小花费 {total}")

    # ---- 演示③：Max Min 的滑窗 ----
    print("\n【Max Min】选 3 个使极差最小   arr=[10,100,300,200,1000,20,30]")
    a = sorted([10, 100, 300, 200, 1000, 20, 30])
    kk = 3
    print(f"  排序后={a}")
    best, best_win = float("inf"), None
    for i in range(len(a) - kk + 1):
        win = a[i:i + kk]
        spread = win[-1] - win[0]
        mark = ""
        if spread < best:
            best, best_win = spread, win
            mark = "  <- 当前最优"
        print(f"    窗口 {win} 极差={spread}{mark}")
    print(f"  => 最小极差 {best}，取自 {best_win}")

    print("\n全部断言通过 ✅")
