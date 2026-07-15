"""
12 · 递归与回溯 —— 超级数字（Recursive Digit Sum）/ 爬楼梯（Davis' Staircase）

═══════════════════════════════════════════════════════════════
【题目】 HackerRank 两连（Algorithms › Recursion）
═══════════════════════════════════════════════════════════════

① Recursive Digit Sum —— 超级数字
   给定字符串 n 与重复次数 k：把 n 重复 k 次拼成一个大数，
   反复对各位数字求和，直到结果只剩 1 位（即「数字根」）。
       n = "9875", k = 4
       拼成 9875 9875 9875 9875
       各位和 = (9+8+7+5) * 4 = 29*4 = 116
       116 -> 1+1+6 = 8  -> 8（个位数，停）
       答案 = 8

② Davis' Staircase —— 爬楼梯（一次可走 1 / 2 / 3 级）
   到达第 n 级共有多少种走法？
       n = 4:  {1,1,1,1} {1,1,2} {1,2,1} {2,1,1}
               {2,2} {1,3} {3,1}          共 7 种

═══════════════════════════════════════════════════════════════
【什么时候想到这个套路】
═══════════════════════════════════════════════════════════════

  - 「对结果反复施加同一操作直到收敛」→ 递归到 base case
    （超级数字：一直求位和，直到只剩一位）。
  - 「大数被重复 k 次」别真的拼字符串再求和 —— 位和满足线性，
    直接「单份位和 × k」即可，避免构造超长字符串。
  - 「方案计数 / 走法总数，且每步有固定几种选择」→ 递归 + 记忆化
    或自底向上 DP；递推式天然是「末步的几种可能之和」。

═══════════════════════════════════════════════════════════════
【思路】
═══════════════════════════════════════════════════════════════

超级数字（大数优化）：
    super_digit(n, k):
        base = (n 各位之和) * k        # 关键：不拼 k 份，直接乘 k
        反复对 base 求位和，直到 base < 10
    正确性：把数字重复 k 次，其「所有位」就是原来各位重复 k 次，
            位和自然是「单份位和 × k」。而数字根只依赖位和。

爬楼梯（一次 1/2/3 级）：
    ways(n) = ways(n-1) + ways(n-2) + ways(n-3)
              └最后跨1级┘ └最后跨2级┘ └最后跨3级┘
    base：ways(0)=1（原地不动算 1 种）, 负数 =0。
    加记忆化后每个 n 只算一次；也可自底向上滚动 DP。

═══════════════════════════════════════════════════════════════
【复杂度】
═══════════════════════════════════════════════════════════════

  超级数字：时间 O(位数)（乘 k 后只需常数几轮位和），空间 O(1)。
  爬楼梯：记忆化 / DP 时间 O(n)，空间 O(n)（可优化到 O(1)）。
"""
from __future__ import annotations

import io
from functools import lru_cache


# ────────────────────────────────────────────────────────────
# 主例：Recursive Digit Sum —— 数字根 + 大数优化（先乘 k）
# ────────────────────────────────────────────────────────────

def _digit_sum(x: int) -> int:
    """把一个整数的各位相加，返回位和。"""
    s = 0
    while x > 0:
        s += x % 10                    # 取末位
        x //= 10                       # 去末位
    return s


def super_digit(n: str, k: int) -> int:
    """
    返回「n 重复 k 次」这个大数的超级数字（数字根）。
    关键优化：不真的拼 k 份字符串，先算单份位和再乘 k。
    """
    # ① 单份各位之和；乘 k 相当于「重复 k 次后的总位和」
    base = sum(int(c) for c in n) * k
    # ② 反复求位和，直到收敛成一位数——这一步就是递归/循环的核心
    while base >= 10:
        base = _digit_sum(base)
    return base


def super_digit_recursive(x: int) -> int:
    """纯递归版数字根：演示「递归到 base case」的形态（不含乘 k 优化）。"""
    # base case：已经是一位数，直接返回
    if x < 10:
        return x
    # 递归：对位和继续求超级数字
    return super_digit_recursive(_digit_sum(x))


# ────────────────────────────────────────────────────────────
# 第二例：Davis' Staircase —— 递归+记忆化 与 自底向上 DP 两版
# ────────────────────────────────────────────────────────────

@lru_cache(maxsize=None)
def staircase_memo(n: int) -> int:
    """记忆化递归：一次可走 1/2/3 级，返回到第 n 级的走法数。"""
    if n < 0:
        return 0                       # 越界：这条路走不通，贡献 0
    if n == 0:
        return 1                       # 恰好到底：算作一种完整走法
    # 最后一步跨 1、2 或 3 级，三种情况互斥且穷尽
    return staircase_memo(n - 1) + staircase_memo(n - 2) + staircase_memo(n - 3)


def staircase_dp(n: int) -> int:
    """自底向上 DP：滚动更新，避免递归栈，空间 O(1)。"""
    if n == 0:
        return 1
    # 用 (a, b, c) 滚动表示 (dp[i-3], dp[i-2], dp[i-1])；
    # base：dp[0]=1，dp[负数]=0，所以初值 = (0, 0, 1)
    a, b, c = 0, 0, 1
    for _ in range(n):
        cur = a + b + c                # dp[i] = dp[i-3]+dp[i-2]+dp[i-1]
        a, b, c = b, c, cur            # 窗口整体右移一格
    return c


# ────────────────────────────────────────────────────────────
# HackerRank 输入解析
#   Recursive Digit Sum：一行 "n k"（n 是很长的数字字符串）。
#   Davis' Staircase：第一行 s（用例组数），随后每组一行一个 n。
# ────────────────────────────────────────────────────────────

def parse_super_digit(readline) -> int:
    """读一行 'n k'，直接返回超级数字。"""
    n, k = readline().split()          # n 保持字符串（可能极长），k 转 int
    return super_digit(n, int(k))


def parse_staircase(readline) -> list[int]:
    """读 's' 组用例，每组一行 n，返回每组走法数。"""
    s = int(readline().strip())
    return [staircase_dp(int(readline().strip())) for _ in range(s)]


def _reader(text: str):
    """把字符串包装成「像 stdin 一样能 readline」的 readline。"""
    return io.StringIO(text).readline


# ────────────────────────────────────────────────────────────
# 主程序：断言 + 可读演示
# ────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("=" * 63)
    print("第 12 章：递归与回溯 —— Recursion & Backtracking")
    print("=" * 63)

    # ---- ① 超级数字：断言 ----
    assert super_digit("9875", 4) == 8      # (29*4=116)->8
    assert super_digit("148", 3) == 3       # 官方样例：148*3 位和->...->3
    assert super_digit("9", 1) == 9         # 本就一位
    assert super_digit("10", 1) == 1        # 1+0=1
    # 递归版与「乘 k=1」结果一致（同一个数字根）
    assert super_digit_recursive(9875) == super_digit("9875", 1)

    # ---- ② 爬楼梯：断言（记忆化 与 DP 必须一致） ----
    assert staircase_memo(1) == 1           # {1}
    assert staircase_memo(3) == 4           # {1,1,1}{1,2}{2,1}{3}
    assert staircase_memo(4) == 7
    assert staircase_memo(5) == 13
    for i in range(0, 20):
        assert staircase_memo(i) == staircase_dp(i)

    # ---- HackerRank 输入解析：断言 ----
    assert parse_super_digit(_reader("9875 4\n")) == 8
    assert parse_staircase(_reader("3\n1\n3\n7\n")) == [1, 4, 44]

    # ---- 演示：超级数字的收敛过程（大数优化） ----
    print("\n【超级数字】n=\"9875\", k=4")
    base = sum(int(c) for c in "9875") * 4
    print(f"  单份位和 {sum(int(c) for c in '9875')} × k=4 = {base}（不拼大数）")
    while base >= 10:
        nxt = _digit_sum(base)
        print(f"  {base} 的位和 = {nxt}")
        base = nxt
    print(f"  => 超级数字 = {base}")

    # ---- 演示：爬楼梯的递推表 ----
    print("\n【爬楼梯】一次可走 1/2/3 级，ways(n)=ways(n-1)+ways(n-2)+ways(n-3)")
    for i in range(0, 8):
        print(f"  ways({i}) = {staircase_dp(i)}")

    print("\n全部断言通过 ✅")
