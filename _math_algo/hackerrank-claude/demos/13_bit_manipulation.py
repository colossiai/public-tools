"""
13 · 位运算 —— XOR 的两个经典应用（Lonely Integer / Maximizing XOR）

═══════════════════════════════════════════════════════════════
【题目】 HackerRank — Lonely Integer（孤独的整数）
═══════════════════════════════════════════════════════════════

给一个数组，除了一个数只出现「一次」，其余每个数都恰好出现「两次」。
找出那个只出现一次的数。

    arr = [1, 2, 3, 4, 3, 2, 1]
    答案 = 4     （1、2、3 各出现两次，只有 4 是单身狗）

配套第二题 —— HackerRank Maximizing XOR（最大化异或）：
    给定 l、r（l ≤ r），在闭区间 [l, r] 内任取两个数 a、b
    （允许 a == b），求 a XOR b 的最大值。

    l = 10, r = 15
    答案 = 7     （例如 11 XOR 12 = 7）

═══════════════════════════════════════════════════════════════
【什么时候想到这个套路】
═══════════════════════════════════════════════════════════════

看到 XOR（异或）就先默念它的三条「护身符」性质：
  - 自反：x ^ x == 0        （同一个数异或自己会抵消）
  - 幺元：x ^ 0 == x        （和 0 异或不变）
  - 交换/结合：顺序随便换    （所以能把整个数组一路异或下来）

触发信号：
  - 「每个数出现偶数次，只有一个例外」→ 全体异或，成对的自动抵消。
  - 「求区间内两数最大异或」→ 从最高位往低位贪心，看能否让该位为 1。
  - 需要「常数额外空间」找重复/缺失/单身元素时，优先想 XOR。

═══════════════════════════════════════════════════════════════
【思路】
═══════════════════════════════════════════════════════════════

▶ Lonely Integer：把所有数异或到一起。

    1 ^ 2 ^ 3 ^ 4 ^ 3 ^ 2 ^ 1
  = (1^1) ^ (2^2) ^ (3^3) ^ 4      # 交换律把相同的凑一起
  =   0   ^   0   ^   0   ^ 4
  =   4                            # 成对全归零，只剩单身的那个

▶ Maximizing XOR：不用真的两两枚举（那是 O(n²)）。
  关键观察：a XOR b 的最高位，取决于 a、b 从高到低「第一个不同的位」。
  在 [l, r] 里，把 l 和 r 异或，其结果的最高有效位以下「全部填 1」
  就是能达到的最大异或值——因为区间足够宽时那些低位都能被独立凑出。

    l = 10 = 0b1010
    r = 15 = 0b1111
    l ^ r  = 0b0101   最高位在第 2 位(值 4)
    => 把第 2 位及以下全填 1 = 0b0111 = 7

═══════════════════════════════════════════════════════════════
【复杂度】
═══════════════════════════════════════════════════════════════

  Lonely Integer：  时间 O(n)      空间 O(1)
  Maximizing XOR：  时间 O(log r)  空间 O(1)   （暴力枚举是 O((r-l)²)）
"""
from __future__ import annotations

import io


# ────────────────────────────────────────────────────────────
# 主例一：Lonely Integer —— 全体异或找单身数
# ────────────────────────────────────────────────────────────

def lonely_integer(arr: list[int]) -> int:
    """返回数组中唯一只出现一次的数（其余都出现两次）。"""
    result = 0
    for x in arr:
        # 成对的数在这里会两两抵消（x ^ x == 0），
        # 与 0 异或又不改变结果（x ^ 0 == x），
        # 所以一路异或下来，最后只剩那个「没有搭档」的数。
        result ^= x
    return result


# ────────────────────────────────────────────────────────────
# 主例二：Maximizing XOR —— 从 l^r 的最高位往下全填 1
# ────────────────────────────────────────────────────────────

def maximizing_xor(l: int, r: int) -> int:
    """在闭区间 [l, r] 内取两数，返回可能的最大异或值。"""
    # xor 记录 l 与 r 第一次「分道扬镳」的位置：它的最高位 1
    # 就是任意两数异或能触及的最高位。
    xor = l ^ r
    result = 0
    # 从这个最高位开始，把它及其以下所有位都点亮成 1。
    # 因为区间跨过了这一位的翻转点，低位可以自由组合出全 1。
    while xor:
        result = (result << 1) | 1   # 每轮在末尾补一个 1
        xor >>= 1                     # 消耗掉一位，直到 l^r 的有效位用完
    return result


def maximizing_xor_bruteforce(l: int, r: int) -> int:
    """暴力版：仅用于给贪心版做对拍验证，区间小时才用。"""
    best = 0
    for a in range(l, r + 1):
        for b in range(a, r + 1):    # b 从 a 起即可，异或满足交换律
            best = max(best, a ^ b)
    return best


# ────────────────────────────────────────────────────────────
# 迷你彩蛋：x & -x 取「最低位的 1」(lowest set bit)
# ────────────────────────────────────────────────────────────

def lowest_set_bit(x: int) -> int:
    """返回 x 二进制中最低位那个 1 所代表的值，例如 12(0b1100)->4。"""
    # -x 在补码下等于「按位取反再 +1」，正好把最低位 1 以下保持、
    # 以上全部翻转，于是 x & -x 只剩最低位那个 1。
    # 这是树状数组(Fenwick Tree)的核心技巧。
    return x & -x


# ────────────────────────────────────────────────────────────
# HackerRank 输入解析：两题的 stdin 格式（用 io.StringIO 模拟）
# ────────────────────────────────────────────────────────────
#
# Lonely Integer 真实输入：
#     第一行 n
#     第二行 n 个整数
#
# Maximizing XOR 真实输入：
#     第一行 l
#     第二行 r
#
# 真实提交时把 reader.readline 换成 input / sys.stdin.readline 即可。

def parse_lonely(fake_stdin: str) -> int:
    """解析 Lonely Integer 输入并求解。"""
    reader = io.StringIO(fake_stdin)
    n = int(reader.readline().strip())
    arr = list(map(int, reader.readline().split()))
    assert len(arr) == n, f"说好 {n} 个，实际 {len(arr)} 个"
    return lonely_integer(arr)


def parse_maximizing_xor(fake_stdin: str) -> int:
    """解析 Maximizing XOR 输入并求解。"""
    reader = io.StringIO(fake_stdin)
    l = int(reader.readline().strip())
    r = int(reader.readline().strip())
    return maximizing_xor(l, r)


# ────────────────────────────────────────────────────────────
# 主程序：断言 + 可读演示
# ────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("=" * 63)
    print("第 13 章：位运算 —— Bit Manipulation")
    print("=" * 63)

    # ---- 断言：Lonely Integer ----
    assert lonely_integer([1, 2, 3, 4, 3, 2, 1]) == 4
    assert lonely_integer([0]) == 0
    assert lonely_integer([7, 7, 9]) == 9
    assert lonely_integer([100, 200, 100]) == 200

    # ---- 断言：Maximizing XOR（贪心 vs 暴力对拍）----
    assert maximizing_xor(10, 15) == 7
    assert maximizing_xor(5, 6) == 3
    assert maximizing_xor(11, 100) == 127
    for lo in range(1, 30):
        for hi in range(lo, 30):
            assert maximizing_xor(lo, hi) == maximizing_xor_bruteforce(lo, hi)

    # ---- 断言：lowest set bit ----
    assert lowest_set_bit(12) == 4      # 0b1100 -> 0b0100
    assert lowest_set_bit(1) == 1
    assert lowest_set_bit(48) == 16     # 0b110000 -> 0b010000

    # ---- 断言：stdin 解析 ----
    assert parse_lonely("7\n1 2 3 4 3 2 1\n") == 4
    assert parse_maximizing_xor("10\n15\n") == 7

    # ---- 演示：Lonely Integer 的异或抵消过程 ----
    print("\n【Lonely Integer】arr = [1, 2, 3, 4, 3, 2, 1]")
    arr = [1, 2, 3, 4, 3, 2, 1]
    acc = 0
    for x in arr:
        acc ^= x
        print(f"  异或 {x:>2}  ->  当前累积 = {acc:>2}  (二进制 {acc:04b})")
    print(f"  => 单身数 = {acc}")

    # ---- 演示：Maximizing XOR 从高位往低位填 1 ----
    print("\n【Maximizing XOR】l = 10, r = 15")
    l, r = 10, 15
    print(f"  l      = {l:>2}  =  0b{l:04b}")
    print(f"  r      = {r:>2}  =  0b{r:04b}")
    print(f"  l ^ r  = {l ^ r:>2}  =  0b{l ^ r:04b}   (最高有效位决定答案上界)")
    print(f"  => 把该位及以下全填 1 = {maximizing_xor(l, r)} "
          f"= 0b{maximizing_xor(l, r):04b}")

    # ---- 演示：x & -x 取最低位 1 ----
    print("\n【彩蛋】x & -x 取最低位的 1（树状数组核心）")
    for v in (12, 40, 1):
        print(f"  x={v:>2} (0b{v:06b})  ->  x&-x = {lowest_set_bit(v):>2} "
              f"(0b{lowest_set_bit(v):06b})")

    print("\n全部断言通过 ✅")
