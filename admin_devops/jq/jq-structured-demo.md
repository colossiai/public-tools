# jq 处理结构化数据示例

示例数据是同目录下的 `quotes.json`，在该目录下执行即可。下面每条都在 jq 1.7.1 上实际跑过，`→` 后面是实际输出。

```json
{
    "code": 0,
    "data": [
        {"symbol": "GOOG.US", "last":300.0},
        {"symbol": "AAPL.US", "last":280.0},
        {"symbol": "ANT.US", "last":90.0}
    ]
}
```

## 读取

```bash
# 检查返回码，code 为 0 时退出码为 0
jq -e '.code == 0' quotes.json                    # → true

# 取出所有 symbol
jq -r '.data[].symbol' quotes.json                # → GOOG.US  AAPL.US  ANT.US

# 列出所有叶子字段的路径（不清楚结构时先看这个）
jq -c '[paths(scalars)] | .[0:3]' quotes.json
# → [["code"],["data",0,"symbol"],["data",0,"last"]]
```

## 筛选、排序、统计

```bash
jq -c '.data[] | select(.last > 100)' quotes.json             # 价格 > 100
jq -c '.data[] | select(.symbol | test("^A"))' quotes.json     # 代码以 A 开头
jq -c '.data | sort_by(.last) | map(.symbol)' quotes.json      # → ["ANT.US","AAPL.US","GOOG.US"]
jq -c '.data | max_by(.last)' quotes.json                      # → {"symbol":"GOOG.US","last":300.0}
jq '.data | map(.last) | add / length' quotes.json             # 均价 → 223.33333333333334
```

## 重组结构

```bash
# 数组转成 symbol → last 的字典
jq -c '.data | map({(.symbol): .last}) | add' quotes.json
jq -c '.data | INDEX(.symbol) | map_values(.last)' quotes.json   # 另一种写法
# → {"GOOG.US":300.0,"AAPL.US":280.0,"ANT.US":90.0}

# 拆字段：GOOG.US → code=GOOG, market=US
jq -c '.data | map(.code = (.symbol | split(".")[0]) | .market = (.symbol | split(".")[1]))' quotes.json

# 按价格分档
jq -c '.data | map(. + {tier: (if .last >= 200 then "high" elif .last >= 100 then "mid" else "low" end)})' quotes.json

# 生成汇总对象
jq -c '{total: (.data | length), symbols: [.data[].symbol], top: (.data | max_by(.last).symbol)}' quotes.json
# → {"total":3,"symbols":["GOOG.US","AAPL.US","ANT.US"],"top":"GOOG.US"}
```

## 修改，并保留外层结构

`|=` 只改 `.data` 这一部分，`code` 等其它字段原样保留：

```bash
# 每条加一个字段
jq -c '.data |= map(.last_x2 = .last * 2)' quotes.json

# 删除某一条
jq -c '.data |= map(select(.symbol != "ANT.US"))' quotes.json
jq -c 'del(.data[] | select(.last < 100))' quotes.json            # 另一种写法

# 追加一条
jq -c '.data += [{"symbol":"TSLA.US","last":400.0}]' quotes.json

# 按条件改某一条的值
jq -c '(.data[] | select(.symbol=="AAPL.US") | .last) = 285.5' quotes.json

# 写回文件（会改动 quotes.json，先备份）
jq '.data |= map(select(.symbol != "ANT.US"))' quotes.json > tmp.json && mv tmp.json quotes.json
```

## 导出

```bash
jq -r '.data[] | [.symbol, .last] | @tsv' quotes.json
jq -r '.data[] | "\(.symbol)\t\(.last)"' quotes.json     # 字符串插值，效果相同
```

## 注意

- **不允许结尾逗号**：数组或对象最后一个元素后面多一个逗号，jq 会报错 `parse error: Expected another array element`。
- **`.data | map(...)` 和 `.data |= map(...)` 不一样**：前者只输出数组本身，外层的 `code` 丢掉了；后者输出完整对象，只替换 `.data`。
- **`300.0` 会变成 `300`**：jq 原样读入时会保留 `300.0`，一旦参与计算（比如 `* 2`、`round`），结果就输出成 `300`。
