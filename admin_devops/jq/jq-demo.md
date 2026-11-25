# jq 实现 SQL 功能示例

下面的例子都在 jq 1.7.1 上实际跑过。样例数据 `tx.json`、`users.json` 与本文件在同一目录，在该目录下执行即可。

## 基础查询

```bash
# 1. SELECT sn, sym, amt FROM tx
jq -c '.[] | {sn, sym, amt}' tx.json

# 2. WHERE mkt='HK' AND amt<0
jq -c '.[] | select(.mkt=="HK" and .amt<0)' tx.json
# 注意：null < 0 在 jq 里为 true，所以 s7（amt 为 null）也会被选出来。要排除就写 select(.amt != null and .amt < 0)

# 3. WHERE code IN ('BUY','SELL')
jq -c '.[] | select(.code | IN("BUY","SELL")) | .sn' tx.json

# 4. WHERE sym LIKE '00%.HK'（用正则）
jq -r '.[] | select(.sym | test("^00.*\\.HK$")) | .sym' tx.json

# 5. WHERE amt IS NULL
jq -r '.[] | select(.amt == null) | .sn' tx.json
# → s7
```

## 排序、分页、去重

```bash
# 6. ORDER BY amt DESC LIMIT 3（null 当 0）
jq -c 'sort_by(.amt // 0) | reverse | .[:3] | .[] | {sn, amt}' tx.json

# 7. ORDER BY mkt ASC, ts DESC（数字字段可以取负号实现降序）
jq -c 'sort_by(.mkt, -.ts) | .[] | [.mkt, .ts, .sn]' tx.json

# 8. SELECT DISTINCT sym
jq -c '[.[].sym] | unique' tx.json
# → ["00005.HK","00700.HK","09988.HK","AAPL.US","TSLA.US"]
```

## 聚合

```bash
# 9. SELECT COUNT(*) WHERE mkt='HK'
jq '[.[] | select(.mkt=="HK")] | length' tx.json
# → 4

# 10. SELECT ccy, COUNT(*), SUM(amt), MIN(amt), MAX(amt) GROUP BY ccy
jq -c 'group_by(.ccy) | map({ccy: .[0].ccy, cnt: length, total: (map(.amt // 0) | add), min: (map(.amt // 0) | min), max: (map(.amt // 0) | max)}) | .[]' tx.json
# → {"ccy":"HKD","cnt":4,"total":3802,"min":-31798,"max":44400}
#   {"ccy":"USD","cnt":3,"total":2809.5,"min":-2310.5,"max":5120}

# 11. SELECT AVG(amt)（跳过 null）
jq 'map(.amt // empty) | add / length' tx.json

# 12. GROUP BY uid HAVING 港股、美股都有
jq -c 'group_by(.uid) | map({uid: .[0].uid, n: length, hk: (map(select(.mkt=="HK")) | length), us: (map(select(.mkt=="US")) | length)}) | map(select(.hk>0 and .us>0)) | .[]' tx.json
```

## CASE WHEN

```bash
# 13. CASE WHEN amt<0 THEN '流出' ...
jq -r '.[] | [.sn, (if .amt == null or .amt == 0 then "无资金" elif .amt < 0 then "流出" else "流入" end)] | @tsv' tx.json
```

## JOIN（两个文件）

```bash
# 14. INNER JOIN users ON uid
jq -c --slurpfile u users.json '($u[0] | INDEX(.uid)) as $m | .[] | select($m[.uid|tostring]) | {sn, uid, name: $m[.uid|tostring].name}' tx.json

# 15. LEFT JOIN（匹配不上时 name 为 null）
jq -c --slurpfile u users.json '($u[0] | INDEX(.uid)) as $m | .[] | {sn, uid, name: ($m[.uid|tostring].name // null)}' tx.json

# 16. WHERE NOT EXISTS (SELECT 1 FROM users WHERE uid = tx.uid)
jq -c --slurpfile u users.json '[$u[0][].uid] as $ids | [.[] | select(.uid as $x | $ids | index($x) | not) | .uid] | unique' tx.json
# → [1003]

# 17. SELECT uid FROM tx UNION SELECT uid FROM users
jq -c -s '.[0] + .[1] | map(.uid) | unique' tx.json users.json
# → [1001,1002,1003,1004]
```

## 子查询与窗口函数

```bash
# 18. WHERE amt > (SELECT AVG(amt) FROM tx)
jq -c '(map(.amt // 0) | add / length) as $avg | .[] | select((.amt // 0) > $avg) | {sn, amt}' tx.json

# 19. ROW_NUMBER() OVER (PARTITION BY uid ORDER BY ts DESC) = 1（每个用户最新一条）
jq -c 'group_by(.uid) | map(sort_by(-.ts) | to_entries | map(.value + {rn: (.key+1)})) | flatten | .[] | select(.rn==1) | {uid, sn, ts}' tx.json

# 20. SUM(amt) OVER (ORDER BY ts)（累计和）
jq -c 'sort_by(.ts) | reduce .[] as $r ([]; . + [{sn: $r.sn, amt: ($r.amt // 0), cum: ((.[-1].cum // 0) + ($r.amt // 0))}]) | .[]' tx.json
```

## 改数据、透视、导出

```bash
# 21. UPDATE tx SET amt=0 WHERE amt IS NULL
jq -c 'map(if .amt == null then .amt = 0 else . end) | .[-1]' tx.json

# 22. DELETE FROM tx WHERE code='TRANSFER'
jq -c 'map(select(.code != "TRANSFER")) | length' tx.json
# 要写回文件：jq '...' tx.json > tmp && mv tmp tx.json

# 23. 行转列：每个用户各市场的条数
jq -c 'group_by(.uid) | map({uid: .[0].uid} + (group_by(.mkt) | map({key: .[0].mkt, value: length}) | from_entries)) | .[]' tx.json
# → {"uid":1001,"HK":2,"US":1} ...

# 24. 导出 CSV（带表头）
jq -r '(["sn","sym","amt"] | @csv), (.[] | [.sn, .sym, .amt] | @csv)' tx.json

# 25. WHERE ts >= ... 并把时间戳格式化（UTC）
jq -r '.[] | select(.ts >= 1795200000) | [(.ts | strftime("%F %T")), .sn] | @tsv' tx.json
```

## 容易出错的地方

- **null 参与排序**：排序字段里有 null 时，取负号会报错 `null cannot be negated`。先用 `// 0` 补默认值，再用 `reverse` 实现降序（例 6）。
- **null 参与比较**：在 jq 里 `null < 0` 为 true，按数值筛选前要先排除 null（例 2）。
- **数字是字符串**：金额等数字字段如果是字符串，比较前要先 `tonumber`。
- **时区**：`strftime` 按 UTC 输出，要本地时间就改用 `strflocaltime`。
- **`@tsv` / `@csv` 只接受数组**：对对象使用会报错 `object (...) cannot be tsv-formatted, only array`。先把字段取成数组，再配合 `-r` 输出（用 `-c` 会输出带引号的 JSON 字符串，Tab 显示成 `\t`）：

  ```bash
  # 错误：jq -c '.[] | {sn, sym, amt} | @tsv' tx.json
  jq -r '.[] | [.sn, .sym, .amt] | @tsv' tx.json
  # 带表头
  jq -r '(["sn","sym","amt"] | @tsv), (.[] | [.sn, .sym, .amt] | @tsv)' tx.json
  # 保留对象写法，按值的顺序转成数组
  jq -r '.[] | {sn, sym, amt} | to_entries | map(.value) | @tsv' tx.json
  ```
- **比较用 `==`，不是 `=`**：`=` 是赋值，`select(.sym = "AAPL.US")` 的条件得到的是赋值后的对象，对象恒为真，所以每一行都被选中；而 `select` 输出的是原始输入，看起来就像筛选没有生效：

  ```bash
  # 错误：7 条全部输出，sym 还是原值
  jq -c '.[] | select(.sym = "AAPL.US") | {sym, amt}' tx.json
  # 正确
  jq -c '.[] | select(.sym == "AAPL.US") | {sym, amt}' tx.json
  # → {"sym":"AAPL.US","amt":-2310.5}
  #   {"sym":"AAPL.US","amt":0}
  ```
