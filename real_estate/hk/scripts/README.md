# 中原成交数据抓取与分析脚本

所有脚本都要在本目录下执行。脚本之间用相对路径读写 JSON。

- `q.sh '<json body>'`：调用一次中原的成交搜索 API（`POST /findproperty/api/Transaction/Search`）。
- `fetch.py '<json body>' out.json`：按每页 100 条翻页抓取，失败会重试。API 的 offset 最多只到 10,000，结果超过时要用 `nUnitPriceRange` 把价格拆成几段分别抓。
- `hist.py`：把 `cands.json` 里每个屋苑近 3 年的成交，抓到 `hist/`。
- `sino.py`：用发展商代码 `de098`（信置）抓近 3 年的成交，分 4 个价格段，存到 `sino/`。
- `agg.py`：读入 `band.json`，列出尺价落在领都 ±5% 区间内的屋苑，输出 `result.csv`。`band.json` 是近 12 个月尺价 8,000–13,500 的成交，按价格段抓回来后合并成一个文件。
- `trend.py`：读入 `hist/`，计算按年、对两年前、近 6 月环比的变化，输出 `trend_*.json` 和 `trend_*.csv`。
- `sino_agg.py`：读入 `sino/all.json`，输出 `sino/sino_estates.csv`。
- `areas.json`：中原的地区代码对应各分区名称，来自 `/api/Place/GetHmaPlaces`。
- `cands.json`：候选屋苑清单，格式是 `(分区, 屋苑名)`。

常用参数：
- `day`：`Day365` 或 `Day1095`，不支持 `Day730`。
- `postType`：`Sale`。
- `developers`：例如 `["de098"]`。
- `nUnitPriceRange`：`{"min":..,"max":..}`。
- 地区筛选在 API 端不起作用，要抓回来后用 `districtName` 在本地过滤。
