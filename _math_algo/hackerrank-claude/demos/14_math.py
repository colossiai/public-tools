"""
14 · 数学 —— HackerRank 数论工具箱（快速幂 / GCD·LCM / 质数筛 / 逆元）

═══════════════════════════════════════════════════════════════
【题目 / 主题】 HackerRank Mathematics · Number Theory track
═══════════════════════════════════════════════════════════════

数学题是 HackerRank 的招牌强项。这一章不刷单题，而是把「数论赛道」
反复要用到的四件套一次备齐，做成随手可调的工具箱：

  (a) 快速幂取模        power(a, b, m) = a^b mod m
  (b) 欧几里得 GCD/LCM  gcd(a,b) / lcm(a,b)
  (c) 埃氏质数筛        sieve(n) = [2..n 内所有质数]
  (d) 费马小定理逆元     inv(a, p) = a^(p-2) mod p （p 为质数）

一个能立刻感受到威力的例子——组合数取模：
    C(10, 3) mod (10^9+7)
  = 10! / (3! · 7!) mod p
    分母不能直接除，要乘它的「模逆元」，于是 (b)(a)(d) 全用上了。
    答案 = 120

═══════════════════════════════════════════════════════════════
【什么时候想到这些工具】
═══════════════════════════════════════════════════════════════

  - 题面出现「结果对 10^9+7 取模」→ 几乎必然要快速幂 / 逆元。
  - 要算 a^b 且 b 极大（10^18）→ 快速幂，绝不能循环乘。
  - 「化简分数 / 求最小公倍数 / 判互质」→ GCD。
  - 「1..n 内质数、质因数分解预处理」→ 埃氏筛（或线性筛）。
  - 「组合数 C(n,k) mod p / 概率题分母取模」→ 费马小定理求逆元。

注：Python 自带大整数，理论上可以直接 a**b 再 % m；但竞赛/其它语言里
    这么写会溢出或超时。本章坚持用「取模技巧」演示，因为这正是练习的意义
    （而且 b 达到 10^18 时，即便 Python 直接幂也会慢到不可接受）。

═══════════════════════════════════════════════════════════════
【思路】
═══════════════════════════════════════════════════════════════

▶ 快速幂（平方求幂）：把指数看成二进制，逐位平方累乘。

    a^13 = a^(1101₂) = a^8 · a^4 · a^1
    每一步都对 m 取模，中间结果永远不爆。
    13 位数从 O(b) 降到 O(log b)。

▶ 欧几里得：gcd(a, b) = gcd(b, a mod b)，直到余数为 0。
    lcm(a, b) = a / gcd(a, b) * b   （先除再乘，防中间溢出）

▶ 埃氏筛：从 2 开始，把每个质数的倍数标记为合数。

    2  3  4  5  6  7  8  9 10 ...
    ↑ 划掉 4,6,8,10...    ↑ 划掉 9,15,21...
    从 p*p 开始划即可（更小的倍数已被更小质数划过）。

▶ 费马小定理：p 为质数且 a 不被 p 整除时，a^(p-1) ≡ 1 (mod p)，
    两边同除 a 得 a^(p-2) ≡ a^(-1) (mod p)。
    于是「除以 a」等价于「乘 a^(p-2) mod p」，用快速幂算即可。

═══════════════════════════════════════════════════════════════
【复杂度】
═══════════════════════════════════════════════════════════════

  快速幂：   O(log b)
  GCD：      O(log(min(a,b)))
  埃氏筛：   O(n log log n)
  逆元：     O(log p)   （本质是一次快速幂）
"""
from __future__ import annotations

import io

MOD = 10 ** 9 + 7   # 竞赛最常见的质数模


# ────────────────────────────────────────────────────────────
# (a) 快速幂取模：把指数按二进制拆开，逐位平方
# ────────────────────────────────────────────────────────────

def power(a: int, b: int, m: int) -> int:
    """返回 a^b mod m，时间 O(log b)。"""
    result = 1
    a %= m                       # 先把底数收进 [0, m)，避免中途变大
    while b > 0:
        if b & 1:                # 当前二进制最低位是 1，就把这一份 a 乘进结果
            result = result * a % m
        a = a * a % m            # 底数平方，对应指数二进制向左进一位
        b >>= 1                  # 处理完最低位，右移看下一位
    return result


# ────────────────────────────────────────────────────────────
# (b) 欧几里得 GCD / LCM
# ────────────────────────────────────────────────────────────

def gcd(a: int, b: int) -> int:
    """最大公约数：辗转相除，直到余数为 0。"""
    while b:
        # (a, b) -> (b, a mod b)：每步用较小数替换，余数替换较小数
        a, b = b, a % b
    return a


def lcm(a: int, b: int) -> int:
    """最小公倍数：先除以 gcd 再乘，防止 a*b 中间溢出（其它语言里要紧）。"""
    return a // gcd(a, b) * b


# ────────────────────────────────────────────────────────────
# (c) 埃拉托斯特尼质数筛
# ────────────────────────────────────────────────────────────

def sieve(n: int) -> list[int]:
    """返回不超过 n 的所有质数（含 n）。"""
    if n < 2:
        return []
    is_prime = [True] * (n + 1)
    is_prime[0] = is_prime[1] = False   # 0 和 1 不是质数
    p = 2
    while p * p <= n:                    # 只需筛到 √n，之后的合数必有小因子
        if is_prime[p]:
            # 从 p*p 起划掉 p 的倍数：更小的倍数(2p,3p...)已被更小质数处理过
            for multiple in range(p * p, n + 1, p):
                is_prime[multiple] = False
        p += 1
    return [i for i in range(2, n + 1) if is_prime[i]]


# ────────────────────────────────────────────────────────────
# (d) 费马小定理求模逆元
# ────────────────────────────────────────────────────────────

def mod_inverse(a: int, p: int) -> int:
    """当 p 为质数且 a 不被 p 整除时，返回 a 关于模 p 的乘法逆元。"""
    # 费马小定理：a^(p-1) ≡ 1，故 a^(p-2) ≡ a^(-1) (mod p)
    return power(a, p - 2, p)


def comb_mod(n: int, k: int, p: int = MOD) -> int:
    """组合数 C(n, k) mod p 的演示：分母用逆元代替除法。四件套合体。"""
    if k < 0 or k > n:
        return 0
    num = 1                      # 分子 n · (n-1) · ... · (n-k+1)
    den = 1                      # 分母 k!
    for i in range(k):
        num = num * ((n - i) % p) % p
        den = den * ((i + 1) % p) % p
    # 「除以 den」= 「乘 den 的逆元」——这里正是逆元的用武之地
    return num * mod_inverse(den, p) % p


# ────────────────────────────────────────────────────────────
# HackerRank 输入解析：以「多测试用例的幂运算」为例（用 io.StringIO 模拟）
# ────────────────────────────────────────────────────────────
#
# 典型输入（Power / modpow 类题目）：
#     第一行 T
#     接下来 T 行，每行三个整数 a b m，求 a^b mod m
#
# 真实提交时把 reader.readline 换成 sys.stdin.readline 即可。

def parse_power_cases(fake_stdin: str) -> list[int]:
    """解析 T 组 (a, b, m)，逐组返回 a^b mod m。"""
    reader = io.StringIO(fake_stdin)
    t = int(reader.readline().strip())   # 别忘了先读用例组数 T
    out = []
    for _ in range(t):
        a, b, m = map(int, reader.readline().split())
        out.append(power(a, b, m))
    return out


# ────────────────────────────────────────────────────────────
# 主程序：断言 + 可读演示
# ────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("=" * 63)
    print("第 14 章：数学 —— Number Theory 工具箱")
    print("=" * 63)

    # ---- 断言：快速幂 ----
    assert power(2, 10, 1000) == 24        # 1024 mod 1000
    assert power(3, 0, 7) == 1             # 任何数的 0 次方为 1
    assert power(7, 4, 10 ** 9 + 7) == 2401
    assert power(2, 1000, MOD) == pow(2, 1000, MOD)   # 和内置 pow 对拍

    # ---- 断言：GCD / LCM ----
    assert gcd(12, 18) == 6
    assert gcd(17, 5) == 1                 # 互质
    assert lcm(4, 6) == 12
    assert lcm(21, 6) == 42

    # ---- 断言：质数筛 ----
    assert sieve(1) == []
    assert sieve(10) == [2, 3, 5, 7]
    assert sieve(20) == [2, 3, 5, 7, 11, 13, 17, 19]
    assert len(sieve(100)) == 25           # 100 以内共 25 个质数

    # ---- 断言：模逆元 & 组合数 ----
    # a * inv(a) ≡ 1 (mod p)
    assert (10 * mod_inverse(10, MOD)) % MOD == 1
    assert comb_mod(10, 3) == 120
    assert comb_mod(5, 2) == 10
    assert comb_mod(52, 5) == 2598960 % MOD

    # ---- 断言：stdin 解析 ----
    assert parse_power_cases("2\n2 10 1000\n3 4 100\n") == [24, 81]

    # ---- 演示：快速幂如何按二进制逐位平方 ----
    print("\n【快速幂】计算 3^13 mod 1000")
    a, b, m = 3, 13, 1000
    result, base, exp = 1, a % m, b
    step = 1
    while exp > 0:
        bit = exp & 1
        if bit:
            result = result * base % m
        print(f"  step{step}: 指数二进制末位={bit}  "
              f"底数={base:>3}  累积结果={result:>3}")
        base = base * base % m
        exp >>= 1
        step += 1
    print(f"  => 3^13 mod 1000 = {result}   (校验 pow={pow(3, 13, 1000)})")

    # ---- 演示：欧几里得辗转相除 ----
    print("\n【GCD】gcd(48, 36) 的辗转相除轨迹")
    x, y = 48, 36
    while y:
        print(f"  gcd({x}, {y})  ->  {x} mod {y} = {x % y}")
        x, y = y, x % y
    print(f"  => gcd = {x}，  lcm(48,36) = {lcm(48, 36)}")

    # ---- 演示：埃氏筛划去合数 ----
    print("\n【质数筛】30 以内的质数")
    primes = sieve(30)
    print(f"  {primes}")

    # ---- 演示：逆元 + 组合数合体 ----
    print("\n【逆元/组合数】C(10, 3) mod (10^9+7)")
    print(f"  10 的模逆元 = {mod_inverse(10, MOD)}")
    print(f"  C(10, 3) = {comb_mod(10, 3)}   (直觉校验：从 10 选 3 = 120)")

    print("\n全部断言通过 ✅")
