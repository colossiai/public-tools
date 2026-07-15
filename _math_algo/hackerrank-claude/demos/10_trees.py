r"""
10 · 树 —— 二叉树高度 / BST 插入 / BST 最近公共祖先

═══════════════════════════════════════════════════════════════
【题目】 HackerRank 三连（Data Structures › Trees）
═══════════════════════════════════════════════════════════════

① Tree: Height of a Binary Tree —— 求二叉树高度（边数口径）
       3
      / \
     5   2
    / \   \
   1   4   6
   高度 = 2（根到最深叶子经过的「边」数；只有根时高度 0）

② Binary Search Tree: Insertion —— 往 BST 里插入一个值
   依 BST 性质：小的往左、大的往右，一路下滑到空位挂上去。

③ Binary Search Tree: Lowest Common Ancestor —— BST 上找 LCA
   给两个节点值 v1、v2，返回它们最近的公共祖先节点。
   利用 BST 有序性：从根出发，两值都比当前小就往左，
   都比当前大就往右，一旦「分叉」（一左一右或命中当前）即为 LCA。

═══════════════════════════════════════════════════════════════
【什么时候想到这个套路】
═══════════════════════════════════════════════════════════════

  - 「高度 / 深度 / 直径」类问题 → 后序递归：先问孩子要答案，
    再合并成自己的答案（自底向上）。
  - 「BST 插入 / 查找 / 删除」→ 永远盯着「当前值与目标的大小关系」
    决定往左还是往右，天然是 O(h)。
  - 「两节点的 LCA」→ 普通二叉树要递归回溯；但只要是 BST，
    就能用有序性一路下探，O(h) 秒解，无需回溯。

═══════════════════════════════════════════════════════════════
【思路】
═══════════════════════════════════════════════════════════════

高度（后序递归）：
    height(node):
        空树 -> -1        # 用 -1 是为了让「单个节点」的高度恰好是 0
        否则  -> 1 + max(height(左), height(右))

    height(叶子) = 1 + max(-1, -1) = 0   ← 对齐「边数」口径

BST 插入：从根开始比较，val < node.val 走左、否则走右，
          碰到空指针就把新节点挂上。

BST 找 LCA（v1 <= v2 已排序处理）：
        node=6
        /    \
      ...    ...
    - v1、v2 都 < node.val  → LCA 在左子树，node = node.left
    - v1、v2 都 > node.val  → LCA 在右子树，node = node.right
    - 否则（node.val 落在 [v1, v2] 之间或等于其一）→ 当前 node 就是 LCA

═══════════════════════════════════════════════════════════════
【复杂度】
═══════════════════════════════════════════════════════════════

  高度：时间 O(n)，空间 O(h)（递归栈）。
  BST 插入 / LCA：时间 O(h)，平衡时 O(log n)，退化成链时 O(n)。
"""
from __future__ import annotations

import io
from typing import Optional


# ────────────────────────────────────────────────────────────
# 数据结构 & 辅助构造器：让断言自包含、可复现
# ────────────────────────────────────────────────────────────

class TreeNode:
    """最朴素的二叉树节点。"""

    def __init__(self, val: int) -> None:
        self.val = val
        self.left: Optional[TreeNode] = None
        self.right: Optional[TreeNode] = None


def bst_insert(root: Optional[TreeNode], val: int) -> TreeNode:
    """
    ② BST 插入：返回插入后的根。
    这是 HackerRank「BST: Insertion」的标准答案本体。
    """
    # 空位到了：新建节点，递归会把它一层层「接」回父指针上
    if root is None:
        return TreeNode(val)
    if val < root.val:
        # 比当前小 -> 去左子树找空位（BST 左小右大）
        root.left = bst_insert(root.left, val)
    else:
        # 比当前大（或相等）-> 去右子树
        root.right = bst_insert(root.right, val)
    return root


def build_bst(values: list[int]) -> Optional[TreeNode]:
    """把一串值按「依次插入」建成一棵 BST——顺带复用上面的插入逻辑。"""
    root: Optional[TreeNode] = None
    for v in values:
        root = bst_insert(root, v)
    return root


def build_tree_from_level(values: list[Optional[int]]) -> Optional[TreeNode]:
    r"""
    按「层序（BFS）+ None 占位」建任意二叉树，方便造非 BST 的测试树。
    例：[3,5,2,1,4,None,6] ->
              3
             / \
            5   2
           / \   \
          1   4   6
    """
    if not values or values[0] is None:
        return None
    root = TreeNode(values[0])
    queue = [root]                     # 待挂孩子的父节点队列
    i = 1
    while queue and i < len(values):
        node = queue.pop(0)
        # 依次尝试挂左孩子、右孩子
        if i < len(values) and values[i] is not None:
            node.left = TreeNode(values[i])   # type: ignore[arg-type]
            queue.append(node.left)
        i += 1
        if i < len(values) and values[i] is not None:
            node.right = TreeNode(values[i])  # type: ignore[arg-type]
            queue.append(node.right)
        i += 1
    return root


# ────────────────────────────────────────────────────────────
# 主例：Tree: Height of a Binary Tree —— 后序递归求高度（边数口径）
# ────────────────────────────────────────────────────────────

def height(root: Optional[TreeNode]) -> int:
    """返回二叉树高度（以「边数」计；空树 -1，单节点 0）。"""
    # 空树给 -1：这样叶子 = 1 + max(-1,-1) = 0，正好是 HackerRank 的口径
    if root is None:
        return -1
    # 后序：先拿到左右子树高度，再 +1 合并成自己的高度
    return 1 + max(height(root.left), height(root.right))


# ────────────────────────────────────────────────────────────
# 第三例：BST: Lowest Common Ancestor —— 用有序性一路下探
# ────────────────────────────────────────────────────────────

def bst_lca(root: Optional[TreeNode], v1: int, v2: int) -> Optional[TreeNode]:
    """在 BST 中返回值 v1、v2 的最近公共祖先节点。"""
    # 先规整成 lo <= hi，省去分左右两种写法
    lo, hi = (v1, v2) if v1 <= v2 else (v2, v1)
    node = root
    while node is not None:
        if hi < node.val:
            # 两个值都比当前小 -> LCA 必在左子树
            node = node.left
        elif lo > node.val:
            # 两个值都比当前大 -> LCA 必在右子树
            node = node.right
        else:
            # 出现「分叉」：lo <= node.val <= hi
            # 说明一个在左侧一个在右侧（或恰好命中），当前即最近公共祖先
            return node
    return None


# ────────────────────────────────────────────────────────────
# HackerRank 输入解析：树题怎么从 stdin 把结构读出来
#   典型格式：第一行 n，第二行 n 个数，按「依次插入 BST」建树。
#   （高度题同样给这一串，构造出的 BST 就是待测树。）
# ────────────────────────────────────────────────────────────

def parse_and_build_bst(readline) -> Optional[TreeNode]:
    """
    读 HackerRank 常见的「n + n 个待插入值」，返回建好的 BST 根。
    真实提交时把 readline 换成 input 或 sys.stdin.readline 即可。
    """
    n = int(readline().strip())
    vals = list(map(int, readline().split()))
    assert len(vals) == n, f"说好 {n} 个，实际 {len(vals)} 个"
    return build_bst(vals)


def _reader(text: str):
    """把字符串包装成「像 stdin 一样能 readline」的 readline。"""
    return io.StringIO(text).readline


def inorder(root: Optional[TreeNode]) -> list[int]:
    """中序遍历：对 BST 而言输出恰好升序，用于断言结构正确。"""
    if root is None:
        return []
    return inorder(root.left) + [root.val] + inorder(root.right)


# ────────────────────────────────────────────────────────────
# 主程序：断言 + 可读演示
# ────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("=" * 63)
    print("第 10 章：树 —— Trees")
    print("=" * 63)

    # ---- ① 高度：断言（边数口径） ----
    #        3
    #       / \
    #      5   2
    #     / \   \
    #    1   4   6      高度 = 2
    t = build_tree_from_level([3, 5, 2, 1, 4, None, 6])
    assert height(t) == 2
    assert height(None) == -1                  # 空树
    assert height(TreeNode(42)) == 0           # 单节点
    assert height(build_tree_from_level([1, 2, None, 3])) == 2  # 左斜链

    # ---- ② BST 插入：断言（中序应升序，且形状可预期） ----
    bst = build_bst([4, 2, 6, 1, 3, 5, 7])
    assert inorder(bst) == [1, 2, 3, 4, 5, 6, 7]
    assert bst.val == 4 and bst.left.val == 2 and bst.right.val == 6
    # 往里再插一个 0，应挂到最左下
    bst_insert(bst, 0)
    assert bst.left.left.left.val == 0

    # ---- ③ BST 找 LCA：断言 ----
    #            4
    #          /   \
    #         2     6
    #        / \   / \
    #       1   3 5   7
    lca_tree = build_bst([4, 2, 6, 1, 3, 5, 7])
    assert bst_lca(lca_tree, 1, 3).val == 2    # 分居 2 的左右
    assert bst_lca(lca_tree, 5, 7).val == 6
    assert bst_lca(lca_tree, 1, 7).val == 4    # 跨越整棵树 -> 根
    assert bst_lca(lca_tree, 2, 3).val == 2    # 一个是另一个的祖先

    # ---- HackerRank 输入解析：断言 ----
    built = parse_and_build_bst(_reader("7\n4 2 6 1 3 5 7\n"))
    assert inorder(built) == [1, 2, 3, 4, 5, 6, 7]

    # ---- 演示：高度的后序递归轨迹 ----
    print("\n【求高度】树 [3,5,2,1,4,_,6]（边数口径）")
    def _trace_height(node, depth=0):
        if node is None:
            return -1
        h = 1 + max(_trace_height(node.left, depth + 1),
                    _trace_height(node.right, depth + 1))
        print(f"  {'  ' * depth}节点{node.val}: 高度={h}")
        return h
    print(f"  => 整棵树高度 = {_trace_height(t)}")

    # ---- 演示：BST 插入的下滑路径 ----
    print("\n【BST 插入】依次插入 [4,2,6,1,3,5,7]")
    demo = None
    for v in [4, 2, 6, 1, 3, 5, 7]:
        demo = bst_insert(demo, v)
        print(f"  插入 {v} 后，中序 = {inorder(demo)}")

    # ---- 演示：BST 找 LCA 的下探轨迹 ----
    print("\n【BST 找 LCA】在 [4,2,6,1,3,5,7] 中找 (5, 7) 的 LCA")
    node, lo, hi = lca_tree, 5, 7
    while node:
        if hi < node.val:
            print(f"  在 {node.val}：两值都更小 -> 往左")
            node = node.left
        elif lo > node.val:
            print(f"  在 {node.val}：两值都更大 -> 往右")
            node = node.right
        else:
            print(f"  在 {node.val}：分叉/命中 -> LCA = {node.val}")
            break

    print("\n全部断言通过 ✅")
