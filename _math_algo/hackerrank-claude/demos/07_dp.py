"""
07 · 动态规划 —— Dynamic Programming

═══════════════════════════════════════════════════════════════
【题目】 本文件用两道 HackerRank DP 题覆盖「线性 DP」与「二维 DP」
═══════════════════════════════════════════════════════════════

主例 —— Max Array Sum (HackerRank)：
    给一个可能含负数的整数数组，选出一个「两两不相邻」的子序列，
    使其元素之和最大。可以一个都不选（此时和为 0）。

        arr = [3, 7, 4, 6, 5]
              ↑     ↑     ↑
        选 3 会挡住 7；更优是选 7 和 6 => 13，
        或选 3、4、5 => 12。最优解 = 13。

        arr = [-2, 1, 3, -4, 5]
        选 1 和 5 => 6，或选 3 和 5 => 8。最优解 = 8。

配菜 —— Abbreviation (HackerRank)：
    给两个字符串 a、b。你能对 a 做两种操作：
      ① 把 a 中某些「小写字母」改成对应大写字母；
      ② 删除 a 中「剩下的小写字母」（大写字母不能删）。
    问能否把 a 变成 b。

        a = "daBcd", b = "ABC"
        d(删) a->A B(留) c->C d(删)  => "ABC" ✅  答案 YES

        a = "AbcDE", b = "AFDE"
        没法把 b c 变出一个 F                     答案 NO

═══════════════════════════════════════════════════════════════
【什么时候想到这个套路】
═══════════════════════════════════════════════════════════════

看到这些信号就往 DP 想：

  - 「最大 / 最小 / 有多少种 / 能否达成」+「每一步有选或不选」
    → 定义状态 dp[i] 表示「考虑到第 i 个为止的最优解」。
  - 相邻限制 / 打家劫舍类（不能选挨着的）→ 经典线性 DP，
    dp[i] = max(不选第 i 个, 选第 i 个 + dp[i-2])。
  - 两个字符串之间「能否变换 / 编辑 / 匹配」→ 二维 DP，
    dp[i][j] 表示「a 前 i 个能否变成 b 前 j 个」。

═══════════════════════════════════════════════════════════════
【思路】
═══════════════════════════════════════════════════════════════

① Max Array Sum（线性 DP · 打家劫舍变体）：
   到第 i 个元素为止，最优和只有两种来路——
       incl = 「选 i」= arr[i] + 「上上一个的最优」(excl_prev)
       excl = 「不选 i」= 上一个的最优 (max(incl_prev, excl_prev))
   因为「选了 i 就不能选 i-1」，所以选 i 时只能接 i-2 的状态。
   全程和不能为负（可以一个都不选），故与 0 取 max。

       arr:   3    7    4    6    5
       incl:  3    7    7   13   12     (选当前时的最大和)
       excl:  0    3    7    7   13     (不选当前时的最大和)
                              ↑
                    答案 = max(incl, excl) = 13

② Abbreviation（二维 DP · 类编辑距离）：
   dp[i][j] = a 的前 i 个字符能否恰好变成 b 的前 j 个字符。
   转移时看 a[i-1]：
     - 若是小写：既可「删掉它」(dp[i-1][j])，
       也可在它变大写后正好等于 b[j-1] 时「留下」(dp[i-1][j-1])。
     - 若是大写：它删不掉，只能硬匹配 b[j-1]，匹配上才 dp[i-1][j-1]。

       b:      ''  A   B   C
       a=''    T   F   F   F
       a=d     T   F   F   F   (d 是小写，删掉)
       a=da    F   T   F   F   (a->A)
       a=daB   F   F   T   F   (B 硬匹配)
       a=daBc  F   F   T   F   (c 小写删掉)
       a=daBcd F   F   F   T   (c->C)  => 右下角 T => YES

═══════════════════════════════════════════════════════════════
【复杂度】
═══════════════════════════════════════════════════════════════

  - Max Array Sum：一遍扫描，O(n) 时间，O(1) 额外空间（滚动变量）。
  - Abbreviation：dp 表 (|a|+1)×(|b|+1)，O(|a|·|b|) 时间与空间。
"""
from __future__ import annotations

import io


# ────────────────────────────────────────────────────────────
# 主例：Max Array Sum —— 线性 DP（不选相邻元素的最大和）
# ────────────────────────────────────────────────────────────

def max_subset_sum(arr: list[int]) -> int:
    # incl：到当前为止、「选了当前元素」时的最大子集和
    # excl：到当前为止、「没选当前元素」时的最大子集和
    incl, excl = 0, 0
    for x in arr:
        # 选 x：不能接上一个 incl（那样就相邻了），只能接上一个 excl
        # 与 0 取 max：若 x 及之前全是负的，宁可一个都不选（子集和 = 0）
        new_incl = max(excl + x, 0)
        # 不选 x：继承上一步两种状态里更大的那个
        new_excl = max(incl, excl)
        incl, excl = new_incl, new_excl
    # 最终答案是「选/不选最后一个」两种收尾里更大的
    return max(incl, excl)


# ────────────────────────────────────────────────────────────
# 配菜：Abbreviation —— 二维 DP（能否把 a 变成 b）
# ────────────────────────────────────────────────────────────

def can_abbreviate(a: str, b: str) -> bool:
    n, m = len(a), len(b)
    # dp[i][j]：a 的前 i 个字符能否恰好变成 b 的前 j 个字符
    dp = [[False] * (m + 1) for _ in range(n + 1)]
    dp[0][0] = True  # 空串变空串，天然成立

    # 边界：a 非空、b 为空时，只有 a 的前 i 个「全是小写」才能删干净变空串
    for i in range(1, n + 1):
        if a[i - 1].islower():
            dp[i][0] = dp[i - 1][0]  # 小写可删，继承上一行
        # 一旦遇到大写（删不掉），dp[i][0] 保持 False（后面也别想再变 True）

    for i in range(1, n + 1):
        for j in range(1, m + 1):
            ch = a[i - 1]
            if ch.islower():
                # 小写有两条路：
                #   ① 删掉它 —— 不消耗 b 的字符，看 dp[i-1][j]
                #   ② 大写化后正好等于 b[j-1] —— 看 dp[i-1][j-1]
                match = ch.upper() == b[j - 1]
                dp[i][j] = dp[i - 1][j] or (match and dp[i - 1][j - 1])
            else:
                # 大写删不掉，只能硬碰硬匹配 b[j-1]
                dp[i][j] = ch == b[j - 1] and dp[i - 1][j - 1]

    return dp[n][m]


# ────────────────────────────────────────────────────────────
# HackerRank stdin 解析：两题的真实输入格式（用 StringIO 模拟）
# ────────────────────────────────────────────────────────────

def parse_max_array_sum(text: str) -> list[int]:
    """
    Max Array Sum 输入格式：
        第一行 n
        第二行 n 个整数
    """
    r = io.StringIO(text)
    n = int(r.readline().strip())
    arr = list(map(int, r.readline().split()))
    assert len(arr) == n, f"说好 {n} 个，实际读到 {len(arr)} 个"
    return arr


def parse_abbreviation(text: str) -> list[tuple[str, str]]:
    """
    Abbreviation 输入格式（多测试用例）：
        第一行 q（询问组数）
        接下来每组两行：第一行 a，第二行 b
    """
    r = io.StringIO(text)
    q = int(r.readline().strip())
    pairs = []
    for _ in range(q):
        a = r.readline().strip()
        b = r.readline().strip()
        pairs.append((a, b))
    return pairs


# ────────────────────────────────────────────────────────────
# 主程序：assert 验证 + 可读演示
# ────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("=" * 63)
    print("第 07 章：动态规划 —— Dynamic Programming")
    print("=" * 63)

    # ---- Max Array Sum ----
    assert max_subset_sum([3, 7, 4, 6, 5]) == 13          # 选 7 + 6
    assert max_subset_sum([-2, 1, 3, -4, 5]) == 8         # 选 3 + 5
    assert max_subset_sum([2, 1, 5, 8, 4]) == 11          # 选 2 + 5 + 4
    assert max_subset_sum([3, 5, -7, 8, 10]) == 15        # 选 5 + 10
    assert max_subset_sum([-1, -2, -3]) == 0              # 全负 → 一个都不选
    assert max_subset_sum([5]) == 5                       # 单元素
    # 验证 stdin 解析后接算法
    got = max_subset_sum(parse_max_array_sum("5\n3 7 4 6 5\n"))
    assert got == 13

    print("\n[Max Array Sum · 线性 DP]")
    demo = [3, 7, 4, 6, 5]
    incl, excl = 0, 0
    print(f"  arr   = {demo}")
    print(f"  {'x':>4} {'incl':>6} {'excl':>6}")
    for x in demo:
        new_incl = max(excl + x, 0)
        new_excl = max(incl, excl)
        incl, excl = new_incl, new_excl
        print(f"  {x:>4} {incl:>6} {excl:>6}")
    print(f"  → 最大不相邻子集和 = {max(incl, excl)}")

    # ---- Abbreviation ----
    assert can_abbreviate("daBcd", "ABC") is True
    assert can_abbreviate("AbcDE", "AFDE") is False
    assert can_abbreviate("AbcDE", "ABDE") is True          # b->B, c 删
    assert can_abbreviate("abc", "") is True                # 全小写可删空
    assert can_abbreviate("Abc", "") is False               # A 大写删不掉
    assert can_abbreviate("beFgH", "EFGH") is True
    assert can_abbreviate("beFgH", "EFH") is True           # 删 b、e->E、删 g
    assert can_abbreviate("beFgH", "EF") is False           # H 是大写删不掉
    # 验证 stdin 解析（多测试用例）
    pairs = parse_abbreviation("2\ndaBcd\nABC\nAbcDE\nAFDE\n")
    assert pairs == [("daBcd", "ABC"), ("AbcDE", "AFDE")]
    assert [can_abbreviate(a, b) for a, b in pairs] == [True, False]

    print("\n[Abbreviation · 二维 DP]")
    for a, b in [("daBcd", "ABC"), ("AbcDE", "AFDE"), ("beFgH", "EFGH")]:
        ans = "YES" if can_abbreviate(a, b) else "NO"
        print(f"  a={a!r:9} b={b!r:7} → {ans}")

    print("\n全部断言通过 ✅")
