# 全港屋苑 3 年表现（2026-10-29）

数据来自中原成交 API，抓取和请求工具在 `../scripts/`（`fetch.py`、`q.sh`）。原始 JSON 不入库，放在 `__temp/hk_real_estate/raw/`。

- `all_hk.py`：抓全港近 3 年（`Day1095`）的成交，按尺价分 46 段，3 个并发，存到 `__temp/hk_real_estate/raw/`。日志在 `fetch.log`。
- `all_hk_rank.py`：`uv run --with numpy python -I all_hk_rank.py [raw目录]`。处理步骤：
  - 合并、去重，只保留二手、非特殊成交，输出 `transactions_secondhand.csv`。
  - 对比 2025-11~2026-10 与 2023-11~2024-10（两期各 ≥`MINN`=20 宗），输出 `estates_3y.csv`（含季度中位尺价）、`top30.csv`、`bottom30.csv`。日志在 `rank.log`。
  - 排序用 `adj_chg`：屋苑内回归 log(尺价) ~ 期间 + 座数 + 楼层 + log面积，扣除成交组合变化。`median_chg` 为直接比较中位数的结果，作参考。
  - 单一尺价占近期成交 ≥30% 的屋苑视为非市场成交，予以剔除。例如宏福苑火灾后的收购，几乎全部是 $8,000 / $10,500 尺。
  - `type` 是按名称猜的：邨→公屋/租置，苑→居屋，不一定准确。
