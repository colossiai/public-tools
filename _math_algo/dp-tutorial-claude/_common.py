"""共享工具：matplotlib 中文字体配置 + 输出目录 + CLI 参数解析。

这是底层基础设施，不属于"知识点"。读者可以跳过本文件，直接看 01_*.py 开始。

CLI 行为（每个章节脚本统一）：
  - 默认（不带任何参数）：只在终端打印讲解和 DP 表，不画图也不存图。
  - `--plot`：弹出 matplotlib 窗口显示图。
  - `--save`：把图保存到 ./plots/ 目录。
  - 两个参数可以一起用。
"""
from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

import matplotlib
import matplotlib.pyplot as plt


_PROJECT_ROOT = Path(__file__).resolve().parent
PLOTS_DIR = _PROJECT_ROOT / "plots"

# 由 parse_plot_args() 在每个脚本启动时填入。
_PLOT_ENABLED = False
_SAVE_ENABLED = False


def _pick_chinese_font() -> str | None:
    """挑一个系统里能渲染中文的字体。优先 macOS 内置字体。"""
    candidates = [
        "PingFang SC",
        "Heiti SC",
        "Hiragino Sans GB",
        "Arial Unicode MS",
        "STHeiti",
        "Songti SC",
        "Microsoft YaHei",
        "SimHei",
        "Noto Sans CJK SC",
        "WenQuanYi Zen Hei",
    ]
    from matplotlib import font_manager

    available = {f.name for f in font_manager.fontManager.ttflist}
    for name in candidates:
        if name in available:
            return name
    return None


def setup_chinese_font() -> None:
    """让 matplotlib 能正确显示中文与负号。"""
    font = _pick_chinese_font()
    if font:
        matplotlib.rcParams["font.family"] = font
    matplotlib.rcParams["axes.unicode_minus"] = False


def parse_plot_args(description: str = "DP 入门教程章节脚本") -> tuple[bool, bool]:
    """解析 --plot / --save 开关。两个 flag 默认都为 False。

    在 main() 顶部调用一次即可：

        plot, save = parse_plot_args()

    之后 visualize() 内部的 save_and_show() 会读取这两个开关。
    """
    parser = argparse.ArgumentParser(
        description=description,
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "示例：\n"
            "  python 08_knapsack_01.py              # 只打印讲解\n"
            "  python 08_knapsack_01.py --plot       # 打印 + 弹窗显示图\n"
            "  python 08_knapsack_01.py --save       # 打印 + 保存图到 ./plots/\n"
            "  python 08_knapsack_01.py --plot --save  # 全开"
        ),
    )
    parser.add_argument("--plot", action="store_true",
                        help="弹出 matplotlib 窗口显示图（默认关闭）")
    parser.add_argument("--save", action="store_true",
                        help="把图保存到 ./plots/ 目录（默认关闭）")
    args = parser.parse_args()

    global _PLOT_ENABLED, _SAVE_ENABLED
    _PLOT_ENABLED = args.plot
    _SAVE_ENABLED = args.save

    if not (args.plot or args.save):
        print("[提示] 当前未启用 --plot / --save，只打印讲解。"
              "想看图请加 --plot 或 --save（或两个一起加）。\n")

    return _PLOT_ENABLED, _SAVE_ENABLED


def save_and_show(filename: str, *, dpi: int = 150) -> Path | None:
    """根据 --plot / --save 开关决定保存与显示。

    - --save 给定：保存到 PLOTS_DIR/filename
    - --plot 给定：plt.show()（headless 环境会被静默跳过）
    - 两者都未给：什么都不做（依然 plt.close 释放内存）
    """
    saved_path: Path | None = None

    if _SAVE_ENABLED:
        PLOTS_DIR.mkdir(parents=True, exist_ok=True)
        saved_path = PLOTS_DIR / filename
        plt.savefig(saved_path, dpi=dpi, bbox_inches="tight")
        print(f"[图已保存] {saved_path}")

    if _PLOT_ENABLED:
        headless = (
            os.environ.get("DP_TUTORIAL_HEADLESS") == "1"
            or os.environ.get("MPLBACKEND", "").lower() == "agg"
            or not sys.stdout.isatty()
        )
        if not headless:
            try:
                plt.show()
            except Exception as exc:
                print(f"[plt.show 跳过] {exc}")
        else:
            print("[--plot 已启用但当前是 headless / 无 TTY 环境，跳过弹窗]")

    plt.close("all")
    return saved_path


setup_chinese_font()
