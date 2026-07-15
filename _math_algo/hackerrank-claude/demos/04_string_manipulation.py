"""
04 · 字符串处理 —— 频次统计 · 去重贪心 · 最长公共子序列

═══════════════════════════════════════════════════════════════
【题目】 三道 HackerRank 字符串经典题
═══════════════════════════════════════════════════════════════

① Sherlock and the Valid String（主）
   给定字符串 s，判断它是否「有效」：
     - 要么所有字符出现次数都相同；
     - 要么「删掉恰好一个字符」后，剩下的所有字符次数相同。
   有效返回 "YES"，否则 "NO"。

     s = "aabbcd"    -> "NO"   （a:2 b:2 c:1 d:1，删一个也救不回来）
     s = "aabbccddeefghi" -> "NO"
     s = "abcc"      -> "YES"  （删掉一个 c，变成 a:1 b:1 c:1）

② Alternating Characters
   字符串只含 'A' 'B'，删最少字符使相邻字符都不同（即变成 ABAB… 交替）。
   返回最少删除次数。

     s = "AAAA"   -> 3     s = "AABAAB" -> 2     s = "ABABABAB" -> 0

③ Common Child（最长公共子序列 LCS）
   给两个等长字符串，求它们「公共子序列」的最长长度（子序列可不连续）。

     s1 = "HARRY", s2 = "SALLY"  -> 2   （公共子序列 "AY"）
     s1 = "ABCD",  s2 = "ABDC"   -> 3   （"ABC" 或 "ABD"）

═══════════════════════════════════════════════════════════════
【什么时候想到这个套路】
═══════════════════════════════════════════════════════════════

  - 出现「所有字符次数相同 / 相差 1」——> 先 Counter 统计频次，
    再对「频次的分布」做分类讨论。字符串题很多都退化成「数频次」。
  - 出现「删最少 / 使相邻不同」且只需局部判断——> 贪心，扫一遍相邻对。
  - 出现「两串的公共部分 / 子序列（可不连续）最长」——> 二维 DP（LCS）。
    注意区分：子串(substring)要连续，子序列(subsequence)可跳着选。

═══════════════════════════════════════════════════════════════
【思路】
═══════════════════════════════════════════════════════════════

① Valid String：统计频次后看「频次的频次」freq_of_freq
     - 只有 1 种频次值           -> 本来就全相同，YES
     - 恰好 2 种频次值时，只有两种可救的情况：
         (a) 有个频次是 1 且只出现一次  -> 删掉那个「独苗」字符 -> YES
         (b) 两个频次相差 1 且大的那个只出现一次 -> 删它一次降到小的 -> YES
     - 其它一律 NO

② Alternating：相邻两字符相同就必须删一个，扫一遍计数即可（贪心最优）。

③ LCS：经典二维 DP
       dp[i][j] = s1 前 i 个 与 s2 前 j 个 的 LCS 长度
         s1[i-1] == s2[j-1] :  dp[i][j] = dp[i-1][j-1] + 1   （这对字符配上）
         否则               :  dp[i][j] = max(dp[i-1][j], dp[i][j-1])

              ""  S  A  L  L  Y
          ""   0  0  0  0  0  0
          H    0  0  0  0  0  0
          A    0  0  1  1  1  1
          R    0  0  1  1  1  1
          R    0  0  1  1  1  1
          Y    0  0  1  1  1  2   <- 右下角即答案 2

═══════════════════════════════════════════════════════════════
【复杂度】
═══════════════════════════════════════════════════════════════
  ① Valid String   时间 O(n)      空间 O(字符集)
  ② Alternating    时间 O(n)      空间 O(1)
  ③ Common Child   时间 O(m·n)    空间 O(m·n)（可滚动优化到 O(n)）
"""
from __future__ import annotations

import io
from collections import Counter


# ────────────────────────────────────────────────────────────
# 主例：Sherlock and the Valid String —— 频次的频次分类讨论
# ────────────────────────────────────────────────────────────

def is_valid(s: str) -> str:
    """判断 s 是否有效（最多删一个字符使各字符频次相同）。返回 'YES'/'NO'。"""
    # 第一步：每个字符出现多少次
    freq = Counter(s)

    # 第二步：对「频次」再做一次统计——看有哪些频次值、各出现几次
    # 例如 "aabbc" -> freq={a:2,b:2,c:1} -> freq_of_freq={2:2, 1:1}
    freq_of_freq = Counter(freq.values())

    # 情况 0：只有一种频次值 -> 本来就全部相同，直接有效
    if len(freq_of_freq) == 1:
        return "YES"

    # 情况：超过两种频次值 -> 删一个字符只能改变一个频次，救不回来
    if len(freq_of_freq) > 2:
        return "NO"

    # 到这里恰好是两种频次值。把它们排序：small < large
    (small, cnt_small), (large, cnt_large) = sorted(freq_of_freq.items())

    # 可救情况 (a)：较小的频次就是 1，且只有一个字符是这个频次
    #   -> 直接删掉那个「只出现 1 次」的独苗字符，剩下全相同
    if small == 1 and cnt_small == 1:
        return "YES"

    # 可救情况 (b)：两个频次恰好相差 1，且「较大频次」只对应一个字符
    #   -> 把那个多出来的字符删 1 次，它就降到与其它相同
    if large - small == 1 and cnt_large == 1:
        return "YES"

    return "NO"


# ────────────────────────────────────────────────────────────
# 第二例：Alternating Characters —— 相邻去重贪心
# ────────────────────────────────────────────────────────────

def alternating_characters(s: str) -> int:
    """删最少字符使相邻不同，返回删除次数。"""
    deletions = 0
    # 只需比较每个字符与它的前一个：相同就必须删一个（保留哪个都不影响后续）
    for i in range(1, len(s)):
        if s[i] == s[i - 1]:
            deletions += 1  # 连续相同的一段长 L，会贡献 L-1 次删除，逐对累加即可
    return deletions


# ────────────────────────────────────────────────────────────
# 第三例：Common Child —— 最长公共子序列（二维 DP）
# ────────────────────────────────────────────────────────────

def common_child(s1: str, s2: str) -> int:
    """返回 s1 与 s2 的最长公共子序列长度。"""
    m, n = len(s1), len(s2)
    # dp 多开一行一列当作「空串」边界，全 0，省去繁琐的越界判断
    dp = [[0] * (n + 1) for _ in range(m + 1)]

    for i in range(1, m + 1):
        for j in range(1, n + 1):
            if s1[i - 1] == s2[j - 1]:
                # 末尾这对字符相同：把它接到「各退一格」的最优解后面 +1
                dp[i][j] = dp[i - 1][j - 1] + 1
            else:
                # 不同：只能舍弃某一串的末字符，取两种舍弃里更优的
                dp[i][j] = max(dp[i - 1][j], dp[i][j - 1])

    return dp[m][n]  # 右下角：整个 s1 与整个 s2 的答案


# ────────────────────────────────────────────────────────────
# HackerRank stdin 解析示范（用 io.StringIO 模拟，可运行可断言）
# ────────────────────────────────────────────────────────────

def parse_valid_string(readline) -> str:
    """
    Sherlock and the Valid String 真实输入：单独一行就是字符串 s。
        aabbcd
    """
    return readline().strip()


def parse_common_child(readline) -> tuple[str, str]:
    """
    Common Child 真实输入：两行，各一个字符串。
        HARRY
        SALLY
    """
    s1 = readline().strip()
    s2 = readline().strip()
    return s1, s2


def _reader(text: str):
    """把字符串包装成「像 stdin 一样能 readline」的读取函数。"""
    return io.StringIO(text).readline


# ────────────────────────────────────────────────────────────
# 主程序：断言 + 可读演示
# ────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("=" * 63)
    print("第 04 章：字符串处理 —— String Manipulation")
    print("=" * 63)

    # ---- 断言：Sherlock and the Valid String ----
    assert is_valid("aabbcd") == "NO"
    assert is_valid("aabbccddeefghi") == "NO"
    assert is_valid("abcc") == "YES"
    assert is_valid("aabbcc") == "YES"          # 本来就全相同
    assert is_valid("aaaabbcc") == "NO"         # 频次 {4,2,2}，救不回
    assert is_valid("abccc") == "NO"            # a:1 b:1 c:3，删一个也无法齐
    assert is_valid("aabbc") == "YES"           # 删掉独苗 c -> a:2 b:2
    assert is_valid("a") == "YES"               # 单字符必然有效

    # ---- 断言：Alternating Characters ----
    assert alternating_characters("AAAA") == 3
    assert alternating_characters("AABAAB") == 2
    assert alternating_characters("ABABABAB") == 0
    assert alternating_characters("BBBBB") == 4
    assert alternating_characters("") == 0

    # ---- 断言：Common Child (LCS) ----
    assert common_child("HARRY", "SALLY") == 2
    assert common_child("AA", "BB") == 0
    assert common_child("ABCD", "ABDC") == 3
    assert common_child("SHINCHAN", "NOHARAAA") == 3   # "NHA"

    # ---- 断言：stdin 解析 ----
    assert parse_valid_string(_reader("aabbcd\n")) == "aabbcd"
    assert parse_common_child(_reader("HARRY\nSALLY\n")) == ("HARRY", "SALLY")

    # ---- 演示①：频次的频次如何决定 YES/NO ----
    print("\n【Valid String】看「频次的频次」freq_of_freq")
    for demo in ["aabbcc", "abcc", "aabbcd"]:
        freq = Counter(demo)
        fof = Counter(freq.values())
        print(f"  s={demo!r:<10} freq={dict(freq)}  "
              f"freq_of_freq={dict(fof)} -> {is_valid(demo)}")

    # ---- 演示②：相邻去重的删除位置 ----
    print("\n【Alternating】相邻相同就删一个   s='AABAAB'")
    s = "AABAAB"
    dels = 0
    for i in range(1, len(s)):
        if s[i] == s[i - 1]:
            dels += 1
            print(f"  i={i}: s[{i}]='{s[i]}' == s[{i-1}]='{s[i-1]}' -> 删 (累计 {dels})")
    print(f"  => 最少删除 {dels} 次")

    # ---- 演示③：打印 LCS 的 DP 表 ----
    print("\n【Common Child】LCS 的 DP 表   s1='HARRY', s2='SALLY'")
    a, b = "HARRY", "SALLY"
    m, n = len(a), len(b)
    dp = [[0] * (n + 1) for _ in range(m + 1)]
    for i in range(1, m + 1):
        for j in range(1, n + 1):
            dp[i][j] = (dp[i - 1][j - 1] + 1 if a[i - 1] == b[j - 1]
                        else max(dp[i - 1][j], dp[i][j - 1]))
    header = "      " + "  ".join(['""'] + list(b))
    print("  " + header)
    labels = ['""'] + list(a)
    for i in range(m + 1):
        row = "  ".join(f"{dp[i][j]}" for j in range(n + 1))
        print(f"   {labels[i]:<3}{row}")
    print(f"  => LCS 长度 = {dp[m][n]}")

    print("\n全部断言通过 ✅")
