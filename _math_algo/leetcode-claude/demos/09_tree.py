"""
09 · 树 / 二叉树 —— 遍历与递归三步法

═══════════════════════════════════════════════════════════════
【题目】 本文件用三道经典题串起「树」这一大类
═══════════════════════════════════════════════════════════════

主例 —— 二叉树的最大深度 (LC104)：
    给一棵二叉树，返回它的最大深度（根到最远叶子节点的节点数）。

        3
       / \\
      9  20
        /  \\
       15   7

    答案 = 3

配菜一 —— 二叉树的层序遍历 (LC102)：
    自顶向下、一层一层地把节点值收集成二维列表。
    上面这棵树 → [[3], [9, 20], [15, 7]]

配菜二 —— 二叉树的最近公共祖先 (LC236)：
    给两个节点 p、q，返回它们最近的公共祖先（LCA）。
    p=9, q=7 → LCA = 3；  p=15, q=7 → LCA = 20。

═══════════════════════════════════════════════════════════════
【什么时候想到这个套路】
═══════════════════════════════════════════════════════════════

看到「树 / 二叉树」，脑子里先冒出两个词：**递归** 和 **BFS**。

  - 求深度、路径、直径、翻转、求某种「子树信息」 → DFS 递归。
  - 求「一层一层」的信息（层序、每层最大值、最短路径步数）→ BFS。

树本身就是递归定义的（左子树、右子树又都是树），所以绝大多数树题
天然适合递归：把大问题拆成「左子树的答案」和「右子树的答案」再合并。

═══════════════════════════════════════════════════════════════
【思路】递归三步法（背下来，套所有树的 DFS）
═══════════════════════════════════════════════════════════════

  1️⃣ 终止条件：走到空节点 None 时返回什么（通常是递归的「地基」）。
  2️⃣ 单层逻辑：假设「左右子树的答案已经算好」，我这一层怎么合并。
  3️⃣ 返回值：这个函数向上一层交付什么。

以「最大深度」为例：
  - 终止条件：空节点深度为 0。
  - 单层逻辑：我的深度 = max(左子树深度, 右子树深度) + 1（+1 是我自己）。
  - 返回值：把这个深度交给父节点。

LCA 的巧思：让递归返回「在我这棵子树里找到了谁」。
  - 如果 p、q 分别落在我的左右两侧，那我自己就是 LCA。
  - 如果都在同一侧，答案就在那一侧，把它往上传。

层序遍历不用递归，用队列（先进先出）：
  每次把「当前整层」出队，同时把它们的孩子入队，形成下一层。

═══════════════════════════════════════════════════════════════
【复杂度】
═══════════════════════════════════════════════════════════════

三道题都要访问每个节点一次：时间 O(n)。
空间：DFS 是递归栈 O(h)（h 为树高，最坏 O(n)）；BFS 是队列 O(n)。
"""
from __future__ import annotations

from collections import deque
from typing import Optional


# ────────────────────────────────────────────────────────────
# 数据结构 + 辅助：从「层序 list」建树
# ────────────────────────────────────────────────────────────

class TreeNode:
    """二叉树节点。val 存值，left/right 指向左右孩子。"""

    def __init__(self, val: int = 0,
                 left: Optional["TreeNode"] = None,
                 right: Optional["TreeNode"] = None) -> None:
        self.val = val
        self.left = left
        self.right = right


def build_tree(level_order: list[Optional[int]]) -> Optional[TreeNode]:
    """从 LeetCode 风格的层序列表建树，None 表示空位。

    例如 [3, 9, 20, None, None, 15, 7] 建出：
            3
           / \\
          9  20
            /  \\
           15   7
    做法：用一个队列存「等待接孩子」的父节点，按层序依次取值挂上去。
    """
    if not level_order or level_order[0] is None:
        return None

    it = iter(level_order)
    root = TreeNode(next(it))          # 第一个值一定是根
    queue: deque[TreeNode] = deque([root])

    while queue:
        node = queue.popleft()
        # 依次尝试给当前父节点接上左孩子、右孩子
        for side in ("left", "right"):
            val = next(it, None)       # 列表可能提前耗尽，用哨兵 None 兜底
            if val is not None:
                child = TreeNode(val)
                setattr(node, side, child)
                queue.append(child)    # 新孩子也要排队等它自己的孩子
    return root


# ────────────────────────────────────────────────────────────
# 主例：最大深度 (LC104) —— 递归三步法样板
# ────────────────────────────────────────────────────────────

def max_depth(root: Optional[TreeNode]) -> int:
    # 1️⃣ 终止条件：空节点没有深度
    if root is None:
        return 0
    # 2️⃣ 单层逻辑：左右子树深度已知，取较大者
    left = max_depth(root.left)
    right = max_depth(root.right)
    # 3️⃣ 返回值：加上我自己这一层的 1，交给父节点
    return max(left, right) + 1


# ────────────────────────────────────────────────────────────
# 配菜一：层序遍历 (LC102) —— BFS + 队列
# ────────────────────────────────────────────────────────────

def level_order(root: Optional[TreeNode]) -> list[list[int]]:
    result: list[list[int]] = []
    if root is None:                   # 空树直接返回空列表
        return result

    queue: deque[TreeNode] = deque([root])
    while queue:
        # 关键：进入循环前先记下「当前这一层有多少个节点」
        # 只处理这么多个，就精确切出了一整层
        size = len(queue)
        level: list[int] = []
        for _ in range(size):
            node = queue.popleft()
            level.append(node.val)
            # 把下一层的节点排进队尾，留给下一轮循环
            if node.left:
                queue.append(node.left)
            if node.right:
                queue.append(node.right)
        result.append(level)
    return result


# ────────────────────────────────────────────────────────────
# 配菜二：最近公共祖先 (LC236) —— 让递归回传「找到了谁」
# ────────────────────────────────────────────────────────────

def lowest_common_ancestor(root: Optional[TreeNode],
                           p: TreeNode, q: TreeNode) -> Optional[TreeNode]:
    # 1️⃣ 终止条件：走到空，或正好撞上 p / q，就把「撞到的这个」往上传
    #    （撞到 p 就说明 p 在这棵子树里，不必再往下找）
    if root is None or root is p or root is q:
        return root

    # 2️⃣ 单层逻辑：分别到左右子树里找 p、q
    left = lowest_common_ancestor(root.left, p, q)
    right = lowest_common_ancestor(root.right, p, q)

    # 3️⃣ 返回值分三种情况：
    if left and right:
        # 左右各找到一个 → p、q 分居两侧 → 我就是最近公共祖先
        return root
    # 否则答案在非空的那一侧（可能是 LCA 本身，也可能只是 p 或 q）
    return left if left else right


def find_node(root: Optional[TreeNode], val: int) -> Optional[TreeNode]:
    """辅助：按值找到节点对象，方便给 LCA 传入真实节点引用。"""
    if root is None:
        return None
    if root.val == val:
        return root
    return find_node(root.left, val) or find_node(root.right, val)


# ────────────────────────────────────────────────────────────
# 主程序：assert 验证 + 可读演示
# ────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("=" * 63)
    print("第 09 章：树 / 二叉树 —— 遍历与递归三步法")
    print("=" * 63)

    # 主例树：[3, 9, 20, None, None, 15, 7]
    root = build_tree([3, 9, 20, None, None, 15, 7])

    # ---- LC104 最大深度 ----
    assert max_depth(root) == 3
    assert max_depth(None) == 0
    assert max_depth(build_tree([1, 2, 3, 4, None, None, 5])) == 3
    print("\n[LC104 最大深度]")
    print(f"  树 [3,9,20,#,#,15,7] 的最大深度 = {max_depth(root)}")

    # ---- LC102 层序遍历 ----
    assert level_order(root) == [[3], [9, 20], [15, 7]]
    assert level_order(None) == []
    print("\n[LC102 层序遍历]")
    for i, lvl in enumerate(level_order(root)):
        print(f"  第 {i} 层: {lvl}")

    # ---- LC236 最近公共祖先 ----
    p, q = find_node(root, 9), find_node(root, 7)
    assert lowest_common_ancestor(root, p, q).val == 3
    p2, q2 = find_node(root, 15), find_node(root, 7)
    assert lowest_common_ancestor(root, p2, q2).val == 20
    print("\n[LC236 最近公共祖先]")
    print(f"  LCA(9, 7)  = {lowest_common_ancestor(root, p, q).val}")
    print(f"  LCA(15, 7) = {lowest_common_ancestor(root, p2, q2).val}")

    print("\n全部断言通过 ✅")
