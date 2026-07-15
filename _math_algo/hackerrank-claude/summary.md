# HackerRank 系统性解题方法论

> 目标：把「刷 HackerRank」变成「读懂 I/O + 模式识别 + 复用模板」，而不是靠题海记忆。
> 与 LeetCode 最大的不同——**HackerRank 要你写整段程序**：自己读 stdin、自己写 stdout，
> 而不是填一个函数。搞不定 I/O，算法再对也是 0 分。

---

## 一、总体心法

刷 HackerRank 的本质不是记住每道题，而是：

1. **先过 I/O 关**：HackerRank 判的是「程序」，第一件事永远是**正确解析输入、按格式打印输出**。
2. **模式识别**：看到题目 → 快速映射到某一类「套路」。
3. **模板复用**：每一类套路都有一个可背诵的骨架代码。
4. **约束推断复杂度**：从数据规模反推该用什么复杂度的算法。
5. **刻意练习**：错题重做、限时训练、讲解复盘。

> 一句话：**先解析 I/O，再从 constraints 猜复杂度，从复杂度猜算法，从算法套模板。**

---

## 二、HackerRank ≠ LeetCode：五个关键差异

| 维度       | LeetCode                     | HackerRank                                   |
| -------- | ---------------------------- | -------------------------------------------- |
| 提交形式     | 填一个函数，参数已解析好                  | **写整段程序**：自己读 stdin、写 stdout（或填带 I/O 桩的函数）    |
| 判分       | 用例通过/不通过                      | 用例通过率 + **计分（points / score）**，部分题按通过比例给分     |
| 组织       | 按标签/难度                        | 按 **Domain / Track**（见第三节）+ 技能认证 badge、星级    |
| 面向       | 面试刷题为主                        | 面试 + **技能认证（Skills Certification）** + 公司笔试/竞赛 |
| 内容广度     | 算法 / 数据结构                     | 算法 + **数学 / SQL / 函数式 / 正则 / Shell / AI** 等   |

> 记住：在 HackerRank，「读错一行输入」和「算法写错」扣的是同样的分。**I/O 是一等公民。**

---

## 三、HackerRank 的 Domain / Track 地图

HackerRank 按「领域（Domain）」和「专题（Track）」组织，别乱刷：

- **Problem Solving**（算法 + 数据结构）——面试主战场，含 **Interview Preparation Kit**。
- **Mathematics**——数论、组合、概率、几何，HackerRank 的一大特色（LeetCode 弱项）。
- **SQL / Databases**——技能认证高频考点，Basic → Advanced Join / 窗口函数。
- **Functional Programming**——Haskell/Scala/Erlang，练递归与不可变思维。
- **Regex / Shell / Linux Shell**——工程向，正则和文本处理。
- **Python / Java / C++ / …** 语言专项——练语言特性与标准库。
- **Artificial Intelligence / Databases / Security** 等垂直领域。

> **推荐主线**：Problem Solving 里的 **Interview Preparation Kit** 是一份官方精选清单
> （Warm-up → Arrays → Hash → Sort → String → Greedy → Search → DP → Graph → Tree → …），
> 按它一路打通即可覆盖 90% 面试模式。

---

## 四、I/O 生存指南（HackerRank 的命根子）

HackerRank 常见输入格式与对应的 Python 读法（完整可运行示例见 [`demos/00_io_template.py`](demos/00_io_template.py)）：

### 1. 单行整数 / 一行多个整数
```python
n = int(input())                       # 一行一个整数
a, b = map(int, input().split())       # 一行两个整数
arr = list(map(int, input().split()))  # 一行 n 个整数
```

### 2. 多行 / 矩阵
```python
n = int(input())
grid = [list(map(int, input().split())) for _ in range(n)]
```

### 3. HackerRank 自动生成的函数桩（最常见）
平台常给一段 `if __name__ == '__main__':` 的模板，把参数读好后调用你的函数，
**你只需填函数体**，但要看懂它把哪些变量喂给了你、结果写去了哪：
```python
def solve(n, arr):
    # 你的逻辑；返回值会被写进输出文件
    ...

if __name__ == '__main__':
    fptr = open(os.environ['OUTPUT_PATH'], 'w')   # 结果写到环境变量指定的文件
    n = int(input().strip())
    arr = list(map(int, input().rstrip().split()))
    fptr.write(str(solve(n, arr)) + '\n')
    fptr.close()
```

### 4. 大数据量：换用快速 I/O
`input()` 在读 10⁵~10⁶ 行时很慢，改用 `sys.stdin`：
```python
import sys
input = sys.stdin.readline            # 覆盖内置 input，逐行更快
data = sys.stdin.buffer.read().split()  # 一次性读全部，再按需切片（最快）
```

### 5. 输出
```python
print(ans)                            # 单个结果
print(*arr)                           # 一行空格分隔
sys.stdout.write('\n'.join(map(str, results)) + '\n')  # 大量输出别用多次 print
```

> **五条铁律**：① 用 `.strip()` / `.rstrip()` 防尾部空白；② 行数/组数别读少一行；
> ③ 多测试用例先读 `T`；④ 大输入换 `sys.stdin`；⑤ 输出格式（空格/换行/大小写）对齐题面。

---

## 五、从数据规模反推算法

看到 constraints 里的 `n` 上限，几乎能锁定目标复杂度：

| n 的规模        | 允许的复杂度              | 常见算法                            |
| ------------ | ------------------- | ------------------------------- |
| n ≤ 10~12    | O(n!)、O(2ⁿ · n)     | 全排列、暴力回溯、状态压缩 DP                |
| n ≤ 20       | O(2ⁿ)               | 子集枚举、bitmask                    |
| n ≤ 100      | O(n³)               | Floyd、区间 DP                     |
| n ≤ 1,000    | O(n²)               | 双重循环、朴素 DP                       |
| n ≤ 10⁵~10⁶  | O(n log n)、O(n)     | 排序、二分、双指针、滑窗、单调栈、哈希、堆           |
| n ≥ 10⁷~10⁸  | O(n)、O(log n)、O(1)  | 线性扫描、数学公式、位运算                    |

> 经验值：1 秒约能跑 **10⁸** 次基本运算。HackerRank 各语言时限不同——
> Python 通常放宽到 C 的 **2~5 倍**，但 10⁶ 级别仍需注意常数与快速 I/O。

---

## 六、核心模式与模板速查

按「看到什么 → 想到什么」组织（每类都有配套可运行 demo）：

### 1. 数组处理（Arrays）
- **信号**：旋转、区间批量加、矩阵扫描（沙漏和）、原地重排。
- **要点**：左旋 = 切片拼接 / 取模下标；频繁区间加用**差分数组**。

### 2. 哈希表 / 字典（Dictionaries & Hashmaps）
- **信号**：查重、计数、配对、异位词、三元组计数、频次查询。
- **要点**：空间换时间，O(1) 查找；异位词用「排序后的串」或「字符计数元组」当 key。

### 3. 排序（Sorting）
- **信号**：逆序对计数、按属性排序后贪心、需要稳定性。
- **要点**：归并排序顺带**数逆序对**；很多贪心题「先排序」就赢一半。

### 4. 字符串处理（String Manipulation）
- **信号**：相邻去重、判断能否删一个字符使频次一致、最长公共子序列。
- **要点**：计数 + 分类讨论；LCS / 编辑距离是经典 DP。

### 5. 贪心（Greedy）
- **信号**：局部最优可推全局最优（能证明或造反例验证）。
- **要点**：常配合排序；不确定时先用 DP 保底。

### 6. 查找（Search）
- **信号**：有序找边界、二分答案、两数配对（差为 K）、BFS 最短步数。
- **要点**：`check(mid)` 单调 → 二分；无权图最短路 → BFS。

### 7. 动态规划（Dynamic Programming）
- **信号**：最优子结构 + 重叠子问题；最值 / 计数 / 可行性。
- **五步**：定义状态 → 转移方程 → 初始化 → 遍历顺序 → 返回值。
- **子类**：线性 DP、背包、区间 DP、树形 DP、状态压缩、数位 DP。

### 8. 栈 / 队列（Stacks & Queues）
- **信号**：括号匹配、表达式求值、柱状图最大矩形、双栈实现队列、单调栈/队列。
- **要点**：栈内保持单调，弹出时结算答案。

### 9. 图（Graphs：BFS / DFS / 并查集 / 最短路）
- **信号**：连通性、网格扩散、依赖顺序、最小生成、最短步数。
- **要点**：visited 去重；连通分量用并查集；无权最短路用 BFS。

### 10. 树（Trees）
- **信号**：高度、遍历、BST 插入/查询、最近公共祖先、Huffman 解码。
- **要点**：递归三步——终止条件、单层逻辑、返回值。

### 11. 链表（Linked Lists）
- **信号**：反转、环检测、合并、找中点。
- **要点**：dummy 头节点、快慢指针。

### 12. 递归 / 回溯（Recursion & Backtracking）
- **信号**：数字递归求和、爬楼梯、全排列、填字游戏、分治。
- **要点**：选择 → 递归 → 撤销选择；注意 Python 递归深度（`sys.setrecursionlimit`）。

### 13. 位运算（Bit Manipulation）
- **信号**：只出现一次、区间最大 XOR、状态压缩、博弈奇偶。
- **要点**：`x & -x` 取最低位 1；异或消对；用位掩码表示集合。

### 14. 数学（Mathematics —— HackerRank 特色）
- **信号**：大数取模、GCD/LCM、快速幂、组合数、质数筛、模逆元。
- **要点**：`(a*b) % m` 防溢出（Python 天然大整数，但要练思路）；费马小定理求逆元。

---

## 七、复杂度与性能清单（Python on HackerRank）

- 说清 **时间** 与 **空间** 复杂度，包含递归栈开销。
- 隐藏成本：字符串拼接、切片、`in` 对 list 是 O(n)。
- **Python 专属坑**：默认递归深度 1000，深递归先 `sys.setrecursionlimit(10**6)`；
  10⁶ 级 I/O 必须 `sys.stdin`；大量输出用 `'\n'.join(...)` 一次写出。
- 递归复杂度用「递归树」或「主定理」估算。

---

## 八、按 Track 的推荐学习路径

建议按 **Interview Preparation Kit 的顺序** 成块攻克，而非随机刷：

1. Warm-up Challenges（找规律、基础 I/O）
2. Arrays（旋转、差分、矩阵）
3. Dictionaries & Hashmaps
4. Sorting（含逆序对）
5. String Manipulation
6. Greedy Algorithms
7. Search（二分 / BFS）
8. Dynamic Programming（最难，单独深挖）
9. Stacks & Queues
10. Graphs
11. Trees & Linked Lists
12. Recursion & Backtracking
13. Bit Manipulation
14. Mathematics（HackerRank 加餐，建议穿插练）

> 打法：Interview Preparation Kit 全清 → 各 Domain 拿满 5 星 → 考 **Skills Certification**（Problem Solving / Python / SQL）。

---

## 九、刻意练习方法

| 方法       | 做法                                        |
| -------- | ----------------------------------------- |
| 限时训练     | Easy 15 min / Medium 30 min / Hard 45 min |
| 卡住就看讨论区  | 卡 20~30 分钟无思路 → 看 Editorial / Discussion，**理解后合上重写** |
| 错题本      | 记录：题名、Domain、模式、卡点、正确思路一句话总结              |
| 间隔重做     | 1 天 / 1 周 / 1 月后重做，直到肌肉记忆                  |
| 本地先跑     | 先在本地用样例文件喂 stdin 调通，再提交，省 submission 次数   |
| 讲解复盘     | 用「费曼技巧」把解法讲给别人（或对空气讲）                      |

---

## 十、常见陷阱清单

- **I/O 类**（HackerRank 高发）：少读/多读一行、忘 `.strip()`、多测试用例没读 `T`、输出大小写/空格不符、用 `input()` 读大数据超时。
- 边界：空输入、单元素、全相同、最大/最小值。
- 下标越界、`while` 死循环（二分边界写错）。
- 修改容器时同时遍历。
- 负数取模（Python `%` 结果非负，和 C/Java 不同——跨语言小心）。
- 递归深度过大（Python 默认 1000，改迭代或 `setrecursionlimit`）。
- 没读清输出要求（下标 vs 值、是否去重、精度/保留位数）。

---

## 十一、一页速记

```text
读 I/O 格式 → 解析 stdin → 看 constraints 猜复杂度 → 匹配模式 → 套模板 → 按格式写 stdout → 边界自测
```

**模式触发词速记**：
- 数组旋转 / 区间批量加 → 差分 · 取模下标
- 查重 / 计数 / 配对 / 异位词 → 哈希
- 逆序对 → 归并排序
- 相邻去重 / 最长公共子序列 → 字符串 DP
- 局部最优 → 贪心（先排序）
- 有序找边界 / 二分答案 → 二分
- 无权最短步数 → BFS
- 最值 / 计数 + 重叠子问题 → 动态规划
- 下一个更大/更小 / 最大矩形 → 单调栈
- 连通性 / 分组 → 并查集
- 只出现一次 / 集合枚举 → 位运算
- 大数取模 / GCD / 快速幂 / 质数 → 数学
- **读大数据卡时间 → 换 `sys.stdin`**
