"""
02 · 字典与哈希表 —— 异位词对计数 & 公共子串判定

═══════════════════════════════════════════════════════════════
【题目】 HackerRank "Sherlock and Anagrams"（统计互为异位词的子串对数）
═══════════════════════════════════════════════════════════════

给一个字符串 s，统计有多少「对」子串互为异位词（anagram，即字母
构成完全相同、只是顺序可能不同）。子串按「位置」区分，内容相同但
位置不同也算不同的子串。

    s = "abba"
    互为异位词的子串对：
      a & a          （两个单独的 'a'）
      b & b
      ab & ba
      abb & bba
    答案 = 4

═══════════════════════════════════════════════════════════════
【什么时候想到这个套路】
═══════════════════════════════════════════════════════════════

触发信号（哈希表做「签名分桶」）：
  - 「异位词 / 字母重排 / 组成相同」——顺序无关，只看字母多重集。
  - 关键动作：把每个对象压成一个「与顺序无关的签名」，再用哈希表
    按签名分桶。同一桶里的元素两两皆可配对。
  - 签名怎么造？排序后的字符串，或「字母计数元组」，都行。

触发信号（组合计数 C(k,2)）：
  - 一旦「同一类里任意两个都能配成一对」，答案就是 Σ C(k,2)，
    其中 k 是每一类的元素个数，C(k,2)=k*(k-1)/2。

═══════════════════════════════════════════════════════════════
【思路一】枚举所有子串 -> 排序得签名 -> 哈希表分桶 -> 累加 C(k,2)
═══════════════════════════════════════════════════════════════

    s = "abba"，逐个子串取「排序后签名」：

      子串   签名(sorted)
      a      "a"
      b      "b"
      b      "b"
      a      "a"
      ab     "ab"
      bb     "bb"
      ba     "ab"     <- 和 "ab" 同签名！
      abb    "abb"
      bba    "abb"    <- 和 "abb" 同签名！
      abba   "aabb"

    分桶后各签名出现次数：
      "a":2  "b":2  "ab":2  "bb":1  "abb":2  "aabb":1

    对数 = C(2,2)+C(2,2)+C(2,2)+C(1,2)+C(2,2)+C(1,2)
         =   1  +  1  +  1  +  0  +  1  +  0   = 4

═══════════════════════════════════════════════════════════════
【思路二】公共子串判定（Two Strings）：只需看有没有公共「单字符」
═══════════════════════════════════════════════════════════════

  关键洞察：两串若有任意公共子串，那这个子串里的「每一个字符」本身
  就已经是长度为 1 的公共子串。所以问题退化成：
      两串的字符集合是否相交？
  用 set 求交集，非空即 "YES"。不用真的去枚举子串。

═══════════════════════════════════════════════════════════════
【复杂度】
═══════════════════════════════════════════════════════════════

  异位词对：子串共 O(n²) 个，每个排序签名 O(n) -> 时间 O(n³)、空间 O(n²)。
            （对 HackerRank 数据范围足够；追求更快可用「计数元组」签名。）
  公共子串：时间 O(|s1|+|s2|)，空间 O(字符集大小)。
"""
from __future__ import annotations

import io
from collections import Counter


# ────────────────────────────────────────────────────────────
# HackerRank 输入格式备忘
#   Sherlock and Anagrams：
#     第一行：q          （查询组数）
#     接下来 q 行：每行一个字符串 s
#   Two Strings：
#     第一行：q
#     接下来每 2 行一组：s1、s2
# 下面的 parse 用 io.StringIO 模拟 stdin，可运行可断言。
# ────────────────────────────────────────────────────────────

def parse_multi_strings(fake_stdin: str) -> list[str]:
    """把 'q\\n s1\\n s2\\n ...' 解析成 q 个字符串的列表。"""
    reader = io.StringIO(fake_stdin)
    q = int(reader.readline().strip())              # 先读查询组数，别漏
    return [reader.readline().strip() for _ in range(q)]


# ────────────────────────────────────────────────────────────
# 主例：异位词子串对计数（HackerRank Sherlock and Anagrams）
# ────────────────────────────────────────────────────────────

def sherlock_anagrams(s: str) -> int:
    """统计 s 中互为异位词的子串对数。"""
    n = len(s)
    buckets: Counter[str] = Counter()       # 键=排序后签名，值=该签名出现的子串数
    # 枚举所有子串 s[i:j]：i 是起点，j 是终点（不含）
    for i in range(n):
        for j in range(i + 1, n + 1):
            # 排序后的字符序列与「原顺序」无关，正好当异位词的统一签名
            signature = "".join(sorted(s[i:j]))
            buckets[signature] += 1

    # 同一签名下有 k 个子串，就能两两配 C(k,2)=k*(k-1)/2 对
    return sum(k * (k - 1) // 2 for k in buckets.values())


# ────────────────────────────────────────────────────────────
# 第二例：判断两串是否有公共子串（HackerRank Two Strings）
# ────────────────────────────────────────────────────────────

def two_strings(s1: str, s2: str) -> str:
    """两串若存在公共子串返回 'YES'，否则 'NO'。"""
    # 有公共子串 <=> 有公共单字符，所以直接看字符集合是否相交
    if set(s1) & set(s2):                   # & 求交集，非空即真
        return "YES"
    return "NO"


# ────────────────────────────────────────────────────────────
# 主程序：断言 + 可读演示
# ────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("=" * 63)
    print("第 02 章：字典与哈希表 —— Dictionaries & Hashmaps")
    print("=" * 63)

    # ---- 断言：异位词对计数（HackerRank 官方样例）----
    assert sherlock_anagrams("abba") == 4
    assert sherlock_anagrams("abcd") == 0        # 没有任何两个子串同字母构成
    assert sherlock_anagrams("kkkk") == 10       # 全同字符，配对最多
    assert sherlock_anagrams("cdcd") == 5
    assert sherlock_anagrams("ifailuhkqq") == 3

    # ---- 断言：stdin 解析 + 端到端 ----
    strs = parse_multi_strings("2\nabba\nabcd\n")
    assert [sherlock_anagrams(x) for x in strs] == [4, 0]

    # ---- 断言：公共子串判定 ----
    assert two_strings("hello", "world") == "YES"    # 公共字符 'l'/'o'
    assert two_strings("hi", "world") == "NO"        # 无任何公共字符
    assert two_strings("a", "a") == "YES"
    assert two_strings("", "abc") == "NO"            # 空串不可能有公共子串

    # ---- 演示轨迹：abba 的分桶过程 ----
    print("\n【异位词对】s='abba' 的签名分桶")
    s = "abba"
    buckets: Counter[str] = Counter()
    for i in range(len(s)):
        for j in range(i + 1, len(s) + 1):
            sig = "".join(sorted(s[i:j]))
            buckets[sig] += 1
    for sig, k in buckets.items():
        pairs = k * (k - 1) // 2
        mark = f"-> C({k},2)={pairs}" if pairs else "-> (只1个，不成对)"
        print(f"  签名 {sig!r:>7}  出现 {k} 次  {mark}")
    print(f"  => 总对数 {sherlock_anagrams(s)}")

    # ---- 演示轨迹：公共子串判定 ----
    print("\n【公共子串】判定两串是否相交")
    for a, b in [("hello", "world"), ("hi", "world")]:
        common = set(a) & set(b)
        print(f"  {a!r} vs {b!r}: 公共字符={sorted(common) or '无'} -> {two_strings(a, b)}")

    print("\n全部断言通过 ✅")
