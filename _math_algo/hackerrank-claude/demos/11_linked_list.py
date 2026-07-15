"""
11 · 链表 —— 反转 / 判环 / 合并两有序链表

═══════════════════════════════════════════════════════════════
【题目】 HackerRank 三连（Data Structures › Linked Lists）
═══════════════════════════════════════════════════════════════

① Reverse a linked list —— 反转单链表
       1 -> 2 -> 3 -> None
   反转后：3 -> 2 -> 1 -> None

② Cycle Detection —— 判断单链表是否有环（快慢指针）
   1 -> 2 -> 3 -> 4
             ^         \
             └──────────┘   有环 -> True

③ Merge two sorted linked lists —— 合并两条有序链表
   1 -> 3 -> 5   与   2 -> 4 -> 6
   合并 -> 1 -> 2 -> 3 -> 4 -> 5 -> 6

═══════════════════════════════════════════════════════════════
【什么时候想到这个套路】
═══════════════════════════════════════════════════════════════

  - 「反转 / 就地调整指针方向」→ 三指针 prev/cur/nxt 迭代，
    每步先存后继、再掉头、再整体右移，O(1) 空间。
  - 「判环 / 找环入口 / 找中点」→ 快慢指针（Floyd）：
    快指针每次两步、慢指针一步，能相遇即有环。
  - 「合并有序序列 / 归并」→ 双指针各领一条，谁小接谁，
    用哑结点（dummy）省掉「头节点特判」。

═══════════════════════════════════════════════════════════════
【思路】
═══════════════════════════════════════════════════════════════

反转（三指针迭代）：
    prev=None   cur=1 -> 2 -> 3
    每步： nxt = cur.next        # ① 先记住后继，别弄丢
           cur.next = prev       # ② 掉头指向前一个
           prev = cur; cur = nxt # ③ 双双右移
    cur 走到 None 时，prev 即新头。

判环（快慢指针）：
    slow 每次 +1，fast 每次 +2。
    无环 -> fast 先到 None；有环 -> fast 在环里追上 slow（相遇）。

合并（哑结点 + 双指针）：
    dummy -> ?          tail 始终指向已合并部分的尾
    比较 a.val 与 b.val，把小的接到 tail 后面并推进该指针；
    有一条走完，把另一条整段接上即可。

═══════════════════════════════════════════════════════════════
【复杂度】
═══════════════════════════════════════════════════════════════

  反转：时间 O(n)  空间 O(1)
  判环：时间 O(n)  空间 O(1)
  合并：时间 O(m+n) 空间 O(1)（只重接指针，不新建节点）
"""
from __future__ import annotations

import io
from typing import Optional


# ────────────────────────────────────────────────────────────
# 数据结构 & 辅助构造器：让断言自包含、可复现
# ────────────────────────────────────────────────────────────

class Node:
    """单链表节点。"""

    def __init__(self, val: int) -> None:
        self.val = val
        self.next: Optional[Node] = None


def build_list(values: list[int]) -> Optional[Node]:
    """从 Python 列表建一条单链表，返回头节点。"""
    dummy = Node(0)                    # 哑结点：免去「第一个节点特殊处理」
    tail = dummy
    for v in values:
        tail.next = Node(v)
        tail = tail.next
    return dummy.next


def to_pylist(head: Optional[Node]) -> list[int]:
    """把链表转回 Python 列表，方便断言（仅对无环链表使用）。"""
    out = []
    cur = head
    while cur is not None:
        out.append(cur.val)
        cur = cur.next
    return out


# ────────────────────────────────────────────────────────────
# 主例：Reverse a linked list —— 三指针迭代反转
# ────────────────────────────────────────────────────────────

def reverse_list(head: Optional[Node]) -> Optional[Node]:
    """反转单链表，返回新头节点。"""
    prev: Optional[Node] = None        # 反转后 prev 侧是「已掉头」的部分
    cur = head
    while cur is not None:
        nxt = cur.next                 # ① 先存后继，否则改指针后就找不到它了
        cur.next = prev                # ② 掉头：当前节点指向前一个
        prev = cur                     # ③ prev、cur 一起右移一格
        cur = nxt
    # cur 到 None 时，prev 停在原来的最后一个节点，即新头
    return prev


# ────────────────────────────────────────────────────────────
# 第二例：Cycle Detection —— 快慢指针（Floyd 判环）
# ────────────────────────────────────────────────────────────

def has_cycle(head: Optional[Node]) -> bool:
    """判断链表是否有环：快慢指针相遇即有环。"""
    slow = fast = head
    # fast 每次跳两步，所以要保证 fast 和 fast.next 都存在
    while fast is not None and fast.next is not None:
        slow = slow.next               # 慢指针 +1
        fast = fast.next.next          # 快指针 +2
        if slow is fast:               # 在环内追上了（比较身份而非值）
            return True
    # fast 冲出末尾（碰到 None）说明是直链，无环
    return False


# ────────────────────────────────────────────────────────────
# 第三例：Merge two sorted linked lists —— 哑结点 + 双指针
# ────────────────────────────────────────────────────────────

def merge_sorted(a: Optional[Node], b: Optional[Node]) -> Optional[Node]:
    """合并两条升序链表，返回合并后升序链表的头（原地重接指针）。"""
    dummy = Node(0)                    # 哑结点做「起跑线」，返回时取 dummy.next
    tail = dummy                       # tail 永远指向已合并部分的最后一个
    while a is not None and b is not None:
        # 谁的头更小就把谁接到 tail 后面，并推进那条链
        if a.val <= b.val:
            tail.next = a
            a = a.next
        else:
            tail.next = b
            b = b.next
        tail = tail.next
    # 必有一条已走完；把还剩的那条整段接上（它本身已有序）
    tail.next = a if a is not None else b
    return dummy.next


# ────────────────────────────────────────────────────────────
# HackerRank 输入解析：链表题怎么从 stdin 读出节点值
#   Reverse 典型格式：第一行 n，接下来 n 行每行一个值。
#   Merge   典型格式：先读 llist1（n 与 n 个值），再读 llist2。
# ────────────────────────────────────────────────────────────

def parse_one_list(readline) -> Optional[Node]:
    """读「n + n 行值」建一条链表（HackerRank 反转题的读法）。"""
    n = int(readline().strip())
    vals = [int(readline().strip()) for _ in range(n)]
    return build_list(vals)


def parse_two_lists(readline):
    """读两条链表（HackerRank 合并题的读法），返回 (head1, head2)。"""
    a = parse_one_list(readline)
    b = parse_one_list(readline)
    return a, b


def _reader(text: str):
    """把字符串包装成「像 stdin 一样能 readline」的 readline。"""
    return io.StringIO(text).readline


# ────────────────────────────────────────────────────────────
# 主程序：断言 + 可读演示
# ────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("=" * 63)
    print("第 11 章：链表 —— Linked Lists")
    print("=" * 63)

    # ---- ① 反转：断言 ----
    assert to_pylist(reverse_list(build_list([1, 2, 3]))) == [3, 2, 1]
    assert to_pylist(reverse_list(build_list([1]))) == [1]
    assert to_pylist(reverse_list(build_list([]))) == []      # 空链表
    assert to_pylist(reverse_list(build_list([5, 4, 3, 2, 1]))) == [1, 2, 3, 4, 5]

    # ---- ② 判环：断言 ----
    assert has_cycle(build_list([1, 2, 3])) is False          # 直链
    assert has_cycle(None) is False                            # 空链表
    # 手工造环：末尾指回第二个节点
    head = build_list([1, 2, 3, 4])
    tail = head
    while tail.next:
        tail = tail.next
    tail.next = head.next                                      # 4 -> 2 成环
    assert has_cycle(head) is True

    # ---- ③ 合并：断言 ----
    m = merge_sorted(build_list([1, 3, 5]), build_list([2, 4, 6]))
    assert to_pylist(m) == [1, 2, 3, 4, 5, 6]
    assert to_pylist(merge_sorted(build_list([]), build_list([1, 2]))) == [1, 2]
    assert to_pylist(merge_sorted(build_list([1, 1]), build_list([1]))) == [1, 1, 1]

    # ---- HackerRank 输入解析：断言 ----
    lst = parse_one_list(_reader("3\n1\n2\n3\n"))
    assert to_pylist(lst) == [1, 2, 3]
    a, b = parse_two_lists(_reader("3\n1\n3\n5\n3\n2\n4\n6\n"))
    assert to_pylist(merge_sorted(a, b)) == [1, 2, 3, 4, 5, 6]

    # ---- 演示：反转的三指针轨迹 ----
    print("\n【反转】链表 1 -> 2 -> 3")
    prev, cur, step = None, build_list([1, 2, 3]), 1
    while cur is not None:
        nxt = cur.next
        cur.next = prev
        done = []
        p = cur
        while p:                       # 打印当前已反转的前缀
            done.append(p.val)
            p = p.next
        print(f"  step{step}: 掉头节点 {cur.val}，已反转前缀 = {done}")
        prev, cur = cur, nxt
        step += 1
    print(f"  => 新头 = {prev.val}，整体 = {to_pylist(prev)}")

    # ---- 演示：快慢指针在环里相遇 ----
    print("\n【判环】1 -> 2 -> 3 -> 4 -> (回到 2)")
    slow = fast = head                 # 复用上面造好的环
    step = 1
    while fast and fast.next:
        slow, fast = slow.next, fast.next.next
        met = "相遇！有环" if slow is fast else "未相遇"
        print(f"  step{step}: slow={slow.val} fast={fast.val} -> {met}")
        if slow is fast:
            break
        step += 1

    # ---- 演示：合并的谁小接谁 ----
    print("\n【合并】1 -> 3 -> 5   +   2 -> 4 -> 6")
    a, b = build_list([1, 3, 5]), build_list([2, 4, 6])
    dummy = Node(0)
    tail = dummy
    while a and b:
        if a.val <= b.val:
            print(f"  取左 {a.val}（{a.val} <= {b.val}）")
            tail.next, a = a, a.next
        else:
            print(f"  取右 {b.val}（{b.val} < {a.val}）")
            tail.next, b = b, b.next
        tail = tail.next
    tail.next = a if a else b
    print(f"  => 合并结果 = {to_pylist(dummy.next)}")

    print("\n全部断言通过 ✅")
