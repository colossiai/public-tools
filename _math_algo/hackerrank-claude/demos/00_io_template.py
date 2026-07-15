"""
00 · HackerRank I/O 生存指南 —— 先过输入输出关，再谈算法

═══════════════════════════════════════════════════════════════
【为什么单独开一章讲 I/O】
═══════════════════════════════════════════════════════════════

HackerRank 和 LeetCode 最大的区别：
  - LeetCode：参数已经解析好，你只填一个函数体。
  - HackerRank：判的是「整段程序」——你要自己从 stdin 读入、
    自己把答案按格式写到 stdout（或平台给的 OUTPUT_PATH 文件）。

结论：在 HackerRank，「读错一行输入」和「算法写错」扣一样的分。
     I/O 是一等公民，必须先练熟。

本文件不做算法，只演示「各种输入格式怎么解析」，全部用
io.StringIO 模拟 stdin，做到可运行、可断言、可复现。

═══════════════════════════════════════════════════════════════
【六种最常见的 HackerRank 输入格式】
═══════════════════════════════════════════════════════════════

  ① 单行一个整数            n
  ② 一行多个整数            a b c ...
  ③ 第一行 n，第二行 n 个数   （最常见的数组题）
  ④ 矩阵 / 多行              n 行，每行若干数
  ⑤ 多测试用例              第一行 T，然后 T 组
  ⑥ 大数据量                改用 sys.stdin，别用 input()
"""
from __future__ import annotations

import io
import sys


# ────────────────────────────────────────────────────────────
# 六种解析器：每个都接收一个「已经把 stdin 换好的读取函数」readline，
# 这样我们能用 StringIO 喂假输入来测试，而不依赖真实键盘输入。
# 真实提交时，把 readline 换成内置 input 或 sys.stdin.readline 即可。
# ────────────────────────────────────────────────────────────

def parse_single_int(readline) -> int:
    """① 单行一个整数：    5    ->  5"""
    # .strip() 去掉行尾的 '\n' 和可能的空格——HackerRank 尾部空白很常见
    return int(readline().strip())


def parse_int_row(readline) -> list[int]:
    """② 一行多个整数：    3 1 4 1 5   ->  [3, 1, 4, 1, 5]"""
    # split() 不带参数会按任意空白切分并自动忽略多余空格
    return list(map(int, readline().split()))


def parse_n_then_array(readline) -> list[int]:
    """③ 第一行 n，第二行 n 个数（数组题标配）。"""
    n = int(readline().strip())
    arr = list(map(int, readline().split()))
    # 防御性检查：读进来的个数应与声明的 n 一致，否则多半是少读/多读了行
    assert len(arr) == n, f"说好 {n} 个，实际读到 {len(arr)} 个"
    return arr


def parse_matrix(readline) -> list[list[int]]:
    """④ 第一行 n，接下来 n 行、每行若干整数 -> 二维矩阵。"""
    n = int(readline().strip())
    return [list(map(int, readline().split())) for _ in range(n)]


def parse_test_cases(readline) -> list[int]:
    """
    ⑤ 多测试用例：第一行 T，随后每组一行一个整数，返回每组的平方。
       这里用「平方」当占位算法，重点是演示 T 组的读法。
    """
    t = int(readline().strip())            # 千万别忘了先读用例组数 T！
    results = []
    for _ in range(t):
        x = int(readline().strip())
        results.append(x * x)              # 占位：真实题目在这里放你的逻辑
    return results


def parse_fast_bulk(text: str) -> list[int]:
    """
    ⑥ 大数据量（10⁵~10⁶ 行）：一次性读全部再切分，最快。
       真实写法：data = sys.stdin.buffer.read().split()
       这里用参数 text 模拟「整个输入」。
    """
    data = text.split()                    # 一次切好所有 token
    it = iter(data)                        # 用迭代器按需取，避免维护下标
    n = int(next(it))
    return [int(next(it)) for _ in range(n)]


# ────────────────────────────────────────────────────────────
# 平台常见的「函数桩」写法示范（OUTPUT_PATH 模式）
# ────────────────────────────────────────────────────────────

def solve_sum(n: int, arr: list[int]) -> int:
    """一个占位算法：求和。用来演示函数桩把结果写到输出文件。"""
    return sum(arr)


def run_with_output_path(fake_stdin: str) -> str:
    """
    模拟 HackerRank 自动生成的 main：从 stdin 读参数，调用 solve，
    把结果写到 os.environ['OUTPUT_PATH'] 指向的文件。
    这里用 StringIO 同时假扮 stdin 和输出文件，返回写出的内容。
    """
    reader = io.StringIO(fake_stdin)
    out = io.StringIO()                    # 假扮 open(OUTPUT_PATH, 'w')
    n = int(reader.readline().strip())
    arr = list(map(int, reader.readline().rstrip().split()))
    out.write(str(solve_sum(n, arr)) + "\n")   # 别忘了结尾换行
    return out.getvalue()


# ────────────────────────────────────────────────────────────
# 主程序：用 StringIO 喂假输入做断言 + 打印每种格式的解析结果
# ────────────────────────────────────────────────────────────

def _reader(text: str):
    """把一段字符串包装成「像 stdin 一样能 readline」的对象的 readline。"""
    return io.StringIO(text).readline


if __name__ == "__main__":
    print("=" * 63)
    print("第 00 章：HackerRank I/O 生存指南")
    print("=" * 63)

    # ---- ① 单行整数 ----
    assert parse_single_int(_reader("5\n")) == 5
    assert parse_single_int(_reader("  42  \n")) == 42   # 带空格也要能扛住

    # ---- ② 一行多整数 ----
    assert parse_int_row(_reader("3 1 4 1 5\n")) == [3, 1, 4, 1, 5]

    # ---- ③ n + 数组 ----
    assert parse_n_then_array(_reader("4\n10 20 30 40\n")) == [10, 20, 30, 40]

    # ---- ④ 矩阵 ----
    assert parse_matrix(_reader("2\n1 2 3\n4 5 6\n")) == [[1, 2, 3], [4, 5, 6]]

    # ---- ⑤ 多测试用例 ----
    assert parse_test_cases(_reader("3\n2\n3\n5\n")) == [4, 9, 25]

    # ---- ⑥ 快速批量读 ----
    assert parse_fast_bulk("5\n3 1 4 1 5\n") == [3, 1, 4, 1, 5]

    # ---- 函数桩 / OUTPUT_PATH 模式 ----
    assert run_with_output_path("4\n10 20 30 40\n") == "100\n"

    # ---- 演示：把每种格式的解析结果打印出来看 ----
    print("\n① 单行整数      '5'              ->", parse_single_int(_reader("5\n")))
    print("② 一行多整数    '3 1 4 1 5'      ->", parse_int_row(_reader("3 1 4 1 5\n")))
    print("③ n + 数组      '4 / 10 20 30 40'->", parse_n_then_array(_reader("4\n10 20 30 40\n")))
    print("④ 矩阵          '2 / 1 2 3 / ...' ->", parse_matrix(_reader("2\n1 2 3\n4 5 6\n")))
    print("⑤ 多用例(平方)  'T=3 / 2 3 5'    ->", parse_test_cases(_reader("3\n2\n3\n5\n")))
    print("⑥ 快速批量读    '5 / 3 1 4 1 5'  ->", parse_fast_bulk("5\n3 1 4 1 5\n"))
    print("桩/OUTPUT_PATH  求和              ->", run_with_output_path("4\n10 20 30 40\n").strip())

    # ---- 真实提交时的三种加速写法（此处仅打印，不执行） ----
    print("\n【真实提交加速备忘】")
    print("  慢->快 I/O:  input = sys.stdin.readline")
    print("  一次读全:    data = sys.stdin.buffer.read().split()")
    print("  批量输出:    sys.stdout.write('\\n'.join(map(str, ans)) + '\\n')")
    print("  深递归:      sys.setrecursionlimit(10**6)")

    _ = sys  # 引用一下，表明真实场景会用到 sys.stdin/stdout/setrecursionlimit

    print("\n全部断言通过 ✅")
