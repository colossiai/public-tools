"""
08 · 链表 —— 反转链表

═══════════════════════════════════════════════════════════════
【题目】 LeetCode 206. 反转链表
═══════════════════════════════════════════════════════════════

给单链表的头节点 head，把它整条反转，返回新的头节点。

例子：

    1 → 2 → 3 → 4 → 5 → None
    反转后：
    5 → 4 → 3 → 2 → 1 → None

═══════════════════════════════════════════════════════════════
【什么时候想到这个套路】
═══════════════════════════════════════════════════════════════

链表题的信号词：反转、合并、去重、找中点、判环、找环入口、删倒数第 K 个。
两大法宝：
  - **dummy 头节点**：统一处理「头节点也可能被删/被换」的边界。
  - **快慢指针**：一个走一步、一个走两步，用来找中点、判环、找倒数第 K。

═══════════════════════════════════════════════════════════════
【思路】三指针原地反转，逐个「掉头」
═══════════════════════════════════════════════════════════════

维护三个指针：prev（已反转部分的头）、cur（正在处理）、下一个 nxt。
每一步把 cur 的 next 指向 prev（掉头），再整体右移一格：

    prev=None   cur=1 → 2 → 3 → 4 → 5

    步骤（把 cur.next 指向 prev，然后 prev、cur 都往右挪）：
      nxt = cur.next          先存住后继，别弄丢链子
      cur.next = prev         掉头：1 指向 None
      prev = cur              prev 前进到 1
      cur = nxt               cur 前进到 2

    None ← 1   cur=2 → 3 → 4 → 5
    None ← 1 ← 2   cur=3 → ...
    ...
    None ← 1 ← 2 ← 3 ← 4 ← 5   cur=None，结束
    prev 此时正是新头 5。

关键：**先用 nxt 存好 cur.next，再改指针**，否则掉头后就找不到剩下的链子了。

═══════════════════════════════════════════════════════════════
【附例 1】 LeetCode 141. 环形链表 —— 快慢指针判环
═══════════════════════════════════════════════════════════════

判断链表是否有环。快指针每次走 2 步，慢指针走 1 步：
  - 无环 → 快指针先到 None，返回 False；
  - 有环 → 快指针会在环里「套圈」追上慢指针，两者相遇，返回 True。

为什么一定相遇？进入环后，快相对慢每步逼近 1 格，距离必然归零，不会跨越。

═══════════════════════════════════════════════════════════════
【附例 2】 链表中点 —— 快慢指针
═══════════════════════════════════════════════════════════════

快走 2、慢走 1，快到尾时慢正好在中点。
偶数个节点时，用 while fast and fast.next 会让慢指针停在「后一个中点」
（如 1→2→3→4 停在 3），这是最常用的约定（配合归并排序/回文判断）。

═══════════════════════════════════════════════════════════════
【复杂度】
═══════════════════════════════════════════════════════════════

  LC206 : 时间 O(n)  空间 O(1)   （原地反转，只用三个指针）
  LC141 : 时间 O(n)  空间 O(1)
  中点  : 时间 O(n)  空间 O(1)
"""
from __future__ import annotations

from typing import Optional


# ────────────────────────────────────────────────────────────
# 链表节点定义 + 测试辅助函数
# ────────────────────────────────────────────────────────────

class ListNode:
    """单链表节点。"""

    def __init__(self, val: int = 0, next: "Optional[ListNode]" = None) -> None:
        self.val = val
        self.next = next

    def __repr__(self) -> str:
        return f"ListNode({self.val})"


def build_list(values: list[int]) -> Optional[ListNode]:
    """由 Python 列表构造链表，返回头节点（空列表返回 None）。"""
    dummy = ListNode()          # 用 dummy 简化「往尾部接节点」的逻辑
    tail = dummy
    for v in values:
        tail.next = ListNode(v)
        tail = tail.next
    return dummy.next


def to_pylist(head: Optional[ListNode]) -> list[int]:
    """把链表还原成 Python 列表，便于断言与打印。"""
    out: list[int] = []
    node = head
    while node:
        out.append(node.val)
        node = node.next
    return out


# ────────────────────────────────────────────────────────────
# 主例：LC206 反转链表（三指针原地反转）
# ────────────────────────────────────────────────────────────

def reverse_list(head: Optional[ListNode]) -> Optional[ListNode]:
    """原地反转链表，返回新头节点。"""
    prev: Optional[ListNode] = None     # 已反转部分的头，初始为空
    cur = head
    while cur:
        nxt = cur.next          # 先存住后继，避免改指针后丢失剩余链子
        cur.next = prev         # 掉头：当前节点指向前一个
        prev = cur              # prev 前进
        cur = nxt               # cur 前进
    return prev                 # cur 走到 None 时，prev 即新头


# ────────────────────────────────────────────────────────────
# 附例 1：LC141 环形链表（快慢指针判环）
# ────────────────────────────────────────────────────────────

def has_cycle(head: Optional[ListNode]) -> bool:
    """判断链表是否有环。"""
    slow = fast = head
    while fast and fast.next:
        slow = slow.next            # 慢指针走 1 步
        fast = fast.next.next       # 快指针走 2 步
        if slow is fast:            # 相遇 → 有环
            return True
    return False                    # 快指针触底 → 无环


# ────────────────────────────────────────────────────────────
# 附例 2：链表中点（快慢指针）
# ────────────────────────────────────────────────────────────

def middle_node(head: Optional[ListNode]) -> Optional[ListNode]:
    """返回链表中间节点；偶数个节点时返回靠后的那个中点。"""
    slow = fast = head
    # 快指针每次走 2 步，走到尽头时慢指针恰在中点
    while fast and fast.next:
        slow = slow.next
        fast = fast.next.next
    return slow


# ────────────────────────────────────────────────────────────
# 自测 + 演示
# ────────────────────────────────────────────────────────────

if __name__ == "__main__":
    # ---- 辅助函数自测 ----
    assert to_pylist(build_list([1, 2, 3])) == [1, 2, 3]
    assert to_pylist(build_list([])) == []

    # ---- LC206 正确性 ----
    assert to_pylist(reverse_list(build_list([1, 2, 3, 4, 5]))) == [5, 4, 3, 2, 1]
    assert to_pylist(reverse_list(build_list([1]))) == [1]
    assert to_pylist(reverse_list(build_list([]))) == []

    # ---- LC141 正确性 ----
    assert has_cycle(build_list([1, 2, 3, 4])) is False
    assert has_cycle(None) is False
    # 手动造一个环：4 的 next 指回 2
    a, b, c, d = ListNode(1), ListNode(2), ListNode(3), ListNode(4)
    a.next, b.next, c.next, d.next = b, c, d, b
    assert has_cycle(a) is True

    # ---- 中点正确性 ----
    assert middle_node(build_list([1, 2, 3, 4, 5])).val == 3        # 奇数 → 正中
    assert middle_node(build_list([1, 2, 3, 4, 5, 6])).val == 4     # 偶数 → 靠后中点
    assert middle_node(build_list([1])).val == 1

    print("=" * 63)
    print("LC206 · 反转链表（三指针原地反转）")
    print("=" * 63)
    src = [1, 2, 3, 4, 5]
    head = build_list(src)
    print(f"  原链表   : {' → '.join(map(str, to_pylist(head)))} → None")
    rev = reverse_list(head)
    print(f"  反转后   : {' → '.join(map(str, to_pylist(rev)))} → None")

    print("\n" + "=" * 63)
    print("LC141 · 环形链表（快慢指针判环）")
    print("=" * 63)
    print(f"  [1,2,3,4] 无环 → has_cycle = {has_cycle(build_list([1, 2, 3, 4]))}")
    print(f"  4→回指2  有环 → has_cycle = {has_cycle(a)}")

    print("\n" + "=" * 63)
    print("链表中点（快慢指针）")
    print("=" * 63)
    for vals in ([1, 2, 3, 4, 5], [1, 2, 3, 4, 5, 6]):
        mid = middle_node(build_list(vals))
        parity = "奇数→正中" if len(vals) % 2 else "偶数→靠后中点"
        print(f"  {vals} 中点 = {mid.val}   （{parity}）")
