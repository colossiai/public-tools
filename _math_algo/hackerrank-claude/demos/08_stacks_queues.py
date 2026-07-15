"""
08 · 栈与队列 —— Stacks & Queues

═══════════════════════════════════════════════════════════════
【题目】 本文件用两道 HackerRank 题覆盖「普通栈」与「单调栈」
═══════════════════════════════════════════════════════════════

主例 —— Balanced Brackets (HackerRank)：
    给一串只含 ()[]{} 的括号，判断是否「完全匹配」：
    每个右括号都能和最近的、同类型的左括号配上，且不交叉。

        "{[()]}"  → YES   一层层正确嵌套
        "{[(])}"  → NO    ] 想配 [，却先撞上没关的 (
        "{{[[(())]]}}" → YES

配菜 —— Largest Rectangle (HackerRank)：
    给一排紧挨着、宽都为 1 的柱子，高度是 heights[i]。
    求能从这些柱子里「切」出的最大矩形面积（矩形高 = 覆盖到的
    连续柱子里最矮的那根）。

        heights = [3, 2, 3]
        以高度 2 铺满 3 根柱子 => 面积 2×3 = 6  ← 最优

        heights = [1, 2, 3, 4, 5]
        以高度 3 覆盖最后 3 根 => 3×3 = 9  ← 最优

═══════════════════════════════════════════════════════════════
【什么时候想到这个套路】
═══════════════════════════════════════════════════════════════

  - 「配对 / 嵌套 / 最近一个未匹配的 X」→ 栈（后进先出正好对应
    「最近打开的最先关闭」）。括号、标签、表达式求值都属此类。
  - 「对每根柱子，找左右第一个比它矮 / 高的」→ 单调栈。
    保持栈内元素单调递增/递减，弹栈的瞬间就确定了边界。
  - 直方图最大矩形、每日温度、下一个更大元素 → 单调栈家族。

═══════════════════════════════════════════════════════════════
【思路】
═══════════════════════════════════════════════════════════════

① Balanced Brackets（普通栈）：
   从左往右扫，遇左括号压栈；遇右括号就看栈顶——
   栈顶必须是「与它配对的左括号」，否则立刻判 NO。
   扫完后栈必须为空（没有落单的左括号）。

       {[()]}
       { -> 栈[{]
       [ -> 栈[{ []
       ( -> 栈[{ [ (]
       ) -> 弹出 ( 匹配 ✅   栈[{ []
       ] -> 弹出 [ 匹配 ✅   栈[{]
       } -> 弹出 { 匹配 ✅   栈[] 空 => YES

② Largest Rectangle（单调栈 · 存下标）：
   维护一个「高度单调递增」的下标栈。当新柱子比栈顶矮，说明
   栈顶那根柱子「向右扩展到此为止」，把它弹出并结算它当高的矩形：
       高 = heights[弹出的下标]
       宽 = 当前下标 - 新栈顶下标 - 1   （左右两侧第一个更矮的之间）
   末尾追加一根高度 0 的哨兵，逼着把栈里剩下的全部结算掉。

       heights = [3, 2, 3]  (末尾补哨兵 0)
       i=0 h=3 压栈            栈下标[0]
       i=1 h=2 < 3 弹0：高3宽1 面积3   压1  栈[1]
       i=2 h=3 压栈            栈[1,2]
       i=3 h=0 弹2：高3宽1 面积3
                 弹1：高2宽3 面积6 ← 最大
       => 6

═══════════════════════════════════════════════════════════════
【复杂度】
═══════════════════════════════════════════════════════════════

  - Balanced Brackets：每个字符进出栈一次，O(n) 时间、O(n) 空间。
  - Largest Rectangle：每根柱子恰好入栈、出栈各一次，O(n) 时间。
"""
from __future__ import annotations

import io


# ────────────────────────────────────────────────────────────
# 主例：Balanced Brackets —— 普通栈做括号匹配
# ────────────────────────────────────────────────────────────

def is_balanced(s: str) -> bool:
    # 右括号 -> 它期望配对的左括号，方便弹栈时一步比对
    pairs = {")": "(", "]": "[", "}": "{"}
    stack: list[str] = []
    for ch in s:
        if ch in "([{":
            stack.append(ch)          # 左括号先记下，等它的另一半
        else:
            # 遇右括号：栈必须非空，且栈顶正好是配对的左括号
            if not stack or stack.pop() != pairs[ch]:
                return False          # 空栈 / 类型不匹配 → 立刻失败
    # 扫完还剩左括号说明有没关上的，栈必须为空才算平衡
    return not stack


# ────────────────────────────────────────────────────────────
# 配菜：Largest Rectangle —— 单调栈求直方图最大矩形
# ────────────────────────────────────────────────────────────

def largest_rectangle(heights: list[int]) -> int:
    best = 0
    # 栈里存「下标」，且保证对应高度单调递增
    stack: list[int] = []
    # 末尾补一根高度 0 的哨兵：确保循环结束前把栈清空结算
    for i, h in enumerate(heights + [0]):
        # 新柱子比栈顶矮：栈顶柱子无法再向右延伸，结算它当高的矩形
        while stack and heights[stack[-1]] >= h:
            height = heights[stack.pop()]      # 被弹出的柱子作为矩形的高
            # 宽度 = 右边界(i) 到 左边界(新栈顶) 之间的柱子数
            # 栈空说明左侧没有更矮的，可一路铺到最左，宽 = i
            width = i if not stack else i - stack[-1] - 1
            best = max(best, height * width)
        stack.append(i)               # 当前下标入栈，维持单调递增
    return best


# ────────────────────────────────────────────────────────────
# HackerRank stdin 解析：两题的真实输入格式（用 StringIO 模拟）
# ────────────────────────────────────────────────────────────

def parse_balanced_brackets(text: str) -> list[str]:
    """
    Balanced Brackets 输入格式：
        第一行 n（字符串条数）
        接下来 n 行，每行一个括号串
    """
    r = io.StringIO(text)
    n = int(r.readline().strip())
    return [r.readline().strip() for _ in range(n)]


def parse_largest_rectangle(text: str) -> list[int]:
    """
    Largest Rectangle 输入格式：
        第一行 n
        第二行 n 个柱子高度
    """
    r = io.StringIO(text)
    n = int(r.readline().strip())
    heights = list(map(int, r.readline().split()))
    assert len(heights) == n, f"说好 {n} 根柱子，实际读到 {len(heights)} 根"
    return heights


# ────────────────────────────────────────────────────────────
# 主程序：assert 验证 + 可读演示
# ────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("=" * 63)
    print("第 08 章：栈与队列 —— Stacks & Queues")
    print("=" * 63)

    # ---- Balanced Brackets ----
    assert is_balanced("{[()]}") is True
    assert is_balanced("{[(])}") is False        # 交叉，配错类型
    assert is_balanced("{{[[(())]]}}") is True
    assert is_balanced("(") is False             # 落单的左括号
    assert is_balanced(")") is False             # 空栈遇右括号
    assert is_balanced("") is True               # 空串视为平衡
    assert is_balanced("([{}])") is True
    # 验证 stdin 解析后接算法
    cases = parse_balanced_brackets("3\n{[()]}\n{[(])}\n()\n")
    assert cases == ["{[()]}", "{[(])}", "()"]
    assert [("YES" if is_balanced(c) else "NO") for c in cases] == ["YES", "NO", "YES"]

    print("\n[Balanced Brackets · 普通栈]")
    for s in ["{[()]}", "{[(])}", "{{[[(())]]}}"]:
        print(f"  {s:14} → {'YES' if is_balanced(s) else 'NO'}")

    # ---- Largest Rectangle ----
    assert largest_rectangle([3, 2, 3]) == 6
    assert largest_rectangle([1, 2, 3, 4, 5]) == 9         # 高3宽3
    assert largest_rectangle([5, 4, 3, 2, 1]) == 9         # 对称，也是 9
    assert largest_rectangle([2, 1, 5, 6, 2, 3]) == 10     # 高5宽2 (5,6)
    assert largest_rectangle([4]) == 4
    assert largest_rectangle([1, 1, 1, 1]) == 4            # 铺满
    # 验证 stdin 解析后接算法
    hs = parse_largest_rectangle("6\n2 1 5 6 2 3\n")
    assert largest_rectangle(hs) == 10

    print("\n[Largest Rectangle · 单调栈]")
    for hs in [[3, 2, 3], [1, 2, 3, 4, 5], [2, 1, 5, 6, 2, 3]]:
        print(f"  heights={str(hs):22} → 最大矩形面积 = {largest_rectangle(hs)}")

    print("\n全部断言通过 ✅")
