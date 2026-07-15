# LeetCode 15 类模式 · 可运行示例

配套文档：[`../summary.md`](../summary.md)（系统性解题方法论）。

这里把 summary 第四节的每一类「套路」都落成一个**独立可运行**的 Python 文件：
真实 LeetCode 例题 + 逐行中文注释 + `assert` 自测 + 打印演示轨迹。

## 怎么用

```bash
# 只用标准库，无需安装依赖
python3 01_two_pointers.py     # 跑单个
for f in *.py; do python3 "$f"; done   # 全部跑一遍
```

每个文件结尾都有 `if __name__ == "__main__"`：先用 `assert` 证明正确性，
再打印一段可读的过程演示。看到「全部断言通过 ✓」即代表通过。

## 目录

| # | 文件 | 模式 | 例题 |
| -- | ---- | ---- | ---- |
| 01 | [`01_two_pointers.py`](01_two_pointers.py) | 双指针 / 对撞 · 快慢 | 两数之和 II (167)、移动零 (283) |
| 02 | [`02_sliding_window.py`](02_sliding_window.py) | 滑动窗口 | 无重复最长子串 (3)、最短子数组 (209) |
| 03 | [`03_binary_search.py`](03_binary_search.py) | 二分查找 / 二分答案 | lower_bound、爱吃香蕉的珂珂 (875) |
| 04 | [`04_hash_table.py`](04_hash_table.py) | 哈希表 | 两数之和 (1)、字母异位词分组 (49) |
| 05 | [`05_prefix_sum_diff.py`](05_prefix_sum_diff.py) | 前缀和 / 差分 | 和为 K 的子数组 (560)、航班预订 (1109) |
| 06 | [`06_monotonic_stack.py`](06_monotonic_stack.py) | 单调栈 | 每日温度 (739)、柱状图最大矩形 (84) |
| 07 | [`07_stack_queue.py`](07_stack_queue.py) | 栈 / 队列 | 有效括号 (20)、逆波兰 (150)、最小栈 (155) |
| 08 | [`08_linked_list.py`](08_linked_list.py) | 链表 | 反转链表 (206)、环形链表 (141)、找中点 |
| 09 | [`09_tree.py`](09_tree.py) | 树 / 二叉树 · 递归三步法 | 最大深度 (104)、层序遍历 (102)、LCA (236) |
| 10 | [`10_graph.py`](10_graph.py) | 图 · DFS/BFS/拓扑/并查集 | 岛屿数量 (200)、课程表 (207)、Union-Find |
| 11 | [`11_backtracking.py`](11_backtracking.py) | 回溯 | 全排列 (46)、子集 (78)、组合总和 (39) |
| 12 | [`12_dynamic_programming.py`](12_dynamic_programming.py) | 动态规划（入门） | 爬楼梯 (70)、打家劫舍 (198) |
| 13 | [`13_greedy.py`](13_greedy.py) | 贪心 | 跳跃游戏 (55)、分发饼干 (455) |
| 14 | [`14_heap.py`](14_heap.py) | 堆 / 优先队列 | 第 K 大 (215)、前 K 高频 (347)、中位数 (295) |
| 15 | [`15_bit_math.py`](15_bit_math.py) | 位运算 / 数学 | 只出现一次 (136)、快速幂 (50)、位1个数 (191) |

## 进阶

动态规划想深挖的，去看仓库里更完整的图解教程：
[`../../dp-tutorial-claude/`](../../dp-tutorial-claude/)（12 个文件，从递归树到状态压缩）。
