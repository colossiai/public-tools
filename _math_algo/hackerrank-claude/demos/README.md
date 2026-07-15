# HackerRank 模式速成 · 可运行示例

配套文档：[`../summary.md`](../summary.md)（系统性解题方法论）。

这里把 summary 里的每一类「套路」都落成一个**独立可运行**的 Python 文件：
真实 HackerRank 例题 + 逐行中文注释 + `assert` 自测 + 打印演示轨迹。

和 LeetCode 版最大的不同——**第 00 章专讲 I/O**：HackerRank 判的是整段程序，
你得自己读 stdin、写 stdout，所以每个文件都顺带演示了该题的输入解析方式。

## 怎么用

```bash
# 只用标准库，无需安装依赖
python3 00_io_template.py     # 跑单个
for f in *.py; do python3 "$f"; done   # 全部跑一遍
```

每个文件结尾都有 `if __name__ == "__main__"`：先用 `assert` 证明正确性，
再打印一段可读的过程演示。看到「全部断言通过 ✅」即代表通过。

## 目录

| # | 文件 | Domain / 模式 | HackerRank 例题 |
| -- | ---- | ---- | ---- |
| 00 | [`00_io_template.py`](00_io_template.py) | **I/O 生存指南** | 六种 stdin 格式 + 函数桩 / OUTPUT_PATH + 快速 I/O |
| 01 | [`01_arrays.py`](01_arrays.py) | 数组处理 · Arrays | Left Rotation、2D Array - DS（沙漏） |
| 02 | [`02_hashmaps.py`](02_hashmaps.py) | 哈希表 · Dictionaries & Hashmaps | Sherlock and Anagrams、Two Strings |
| 03 | [`03_sorting.py`](03_sorting.py) | 排序 · Sorting | Counting Inversions（归并）、Mark and Toys |
| 04 | [`04_string_manipulation.py`](04_string_manipulation.py) | 字符串处理 · String Manipulation | Valid String、Alternating Characters、Common Child (LCS) |
| 05 | [`05_greedy.py`](05_greedy.py) | 贪心 · Greedy | Luck Balance、Greedy Florist、Max Min |
| 06 | [`06_search.py`](06_search.py) | 查找 · Search | Pairs（差为 K）、Ice Cream Parlor |
| 07 | [`07_dp.py`](07_dp.py) | 动态规划 · Dynamic Programming | Max Array Sum、Abbreviation |
| 08 | [`08_stacks_queues.py`](08_stacks_queues.py) | 栈 / 队列 · Stacks & Queues | Balanced Brackets、Largest Rectangle |
| 09 | [`09_graphs.py`](09_graphs.py) | 图 · Graphs | Roads and Libraries（并查集）、BFS Shortest Reach |
| 10 | [`10_trees.py`](10_trees.py) | 树 · Trees | Height of a Binary Tree、BST 插入、BST 的 LCA |
| 11 | [`11_linked_list.py`](11_linked_list.py) | 链表 · Linked Lists | 反转链表、环检测、合并两有序链表 |
| 12 | [`12_recursion.py`](12_recursion.py) | 递归 / 回溯 · Recursion | Recursive Digit Sum、Davis' Staircase |
| 13 | [`13_bit_manipulation.py`](13_bit_manipulation.py) | 位运算 · Bit Manipulation | Lonely Integer、Maximizing XOR |
| 14 | [`14_math.py`](14_math.py) | 数学 · Mathematics | 快速幂、GCD/LCM、质数筛、模逆元 |

> 建议顺序：先啃 **00（I/O）**，再按 Interview Preparation Kit 的编号一路打通。

## 进阶

动态规划想深挖的，去看仓库里更完整的图解教程：
[`../../dp-tutorial-claude/`](../../dp-tutorial-claude/)（从递归树到状态压缩）。

想对照 LeetCode 版的同类模式，见隔壁：
[`../leetcode-claude/`](../leetcode-claude/)。
