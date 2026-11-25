# jq 命令行参数

基于 jq 1.7.1（`jq --help`）。示例使用同目录下的 `tx.json`、`users.json`，在该目录下执行即可，输出均为实测结果。

用法：

```bash
jq [options] <filter> [file...]
jq [options] --args <filter> [strings...]
jq [options] --jsonargs <filter> [JSON_TEXTS...]
```

不给文件时从标准输入读取。

## 输入控制

| 参数 | 含义 |
|---|---|
| `-n`, `--null-input` | 不读输入，以 `null` 作为唯一输入；可在过滤器里用 `input` / `inputs` 手动读取 |
| `-R`, `--raw-input` | 每行按普通字符串读入，不解析 JSON |
| `-s`, `--slurp` | 把所有输入合并成一个数组，作为唯一输入 |
| `--stream` | 流式解析，把输入拆成 `[路径, 叶子值]` 事件，适合处理超大文件 |
| `--stream-errors` | 同 `--stream`，解析出错时以数组形式报告错误 |
| `--seq` | 按 `application/json-seq`（RFC 7464）格式读写，每条记录以 RS 字符开头 |

```bash
jq -n '1 + 2'                                       # → 3
jq -n '[inputs | .[].uid] | unique' tx.json users.json   # 手动读取多个文件
printf 'a\nb\n' | jq -R .                           # → "a" "b"（每行一个字符串）
printf 'a\nb\n' | jq -Rs .                          # → "a\nb\n"（整体一个字符串）
jq -s 'map(length)' tx.json users.json              # → [7, 3]（两个文件合成一个数组）
echo '{"a":{"b":1}}' | jq -c --stream .             # → [["a","b"],1] [["a","b"]] [["a"]]
```

## 输出格式

| 参数 | 含义 |
|---|---|
| `-c`, `--compact-output` | 每个结果压成一行 |
| `-r`, `--raw-output` | 字符串不带引号、不转义，直接输出 |
| `-j`, `--join-output` | 同 `-r`，且每个结果后不换行 |
| `--raw-output0` | 同 `-r`，每个结果后输出 NUL 字符，配合 `xargs -0` |
| `-a`, `--ascii-output` | 非 ASCII 字符用 `\uXXXX` 转义 |
| `-S`, `--sort-keys` | 输出时对象的 key 按字母排序 |
| `-C`, `--color-output` | 强制彩色输出（管道里默认不着色） |
| `-M`, `--monochrome-output` | 关闭彩色输出 |
| `--tab` | 用 Tab 缩进 |
| `--indent n` | 用 n 个空格缩进（最多 7，`0` 等同于 `-c`） |
| `--unbuffered` | 每输出一个结果就立即刷新，适合 `tail -f` 之类的实时流 |

```bash
jq -c '.[0]' users.json            # → {"uid":1001,"name":"alice","level":"vip1"}
jq -r '.[0].name' users.json       # → alice（不带引号）
jq -j '.[].name' users.json        # → alicebobdave（不换行）
jq --raw-output0 '.[].name' users.json | xargs -0 -n1 echo
echo '{"n":"中"}' | jq -a .        # → {"n": "中"}
jq -S '.[0]' users.json            # key 排序：level, name, uid
jq --indent 4 '.[0]' users.json    # 4 空格缩进
jq -C '.[0]' users.json | less -R  # 管道里保留颜色
```

## 传入变量

| 参数 | 含义 |
|---|---|
| `--arg name value` | 定义字符串变量 `$name` |
| `--argjson name value` | 定义 JSON 变量 `$name`（数字、布尔、对象、数组等） |
| `--slurpfile name file` | 读取文件里的全部 JSON 值，组成数组赋给 `$name` |
| `--rawfile name file` | 把文件全文作为一个字符串赋给 `$name` |
| `--args` | 把剩余命令行参数作为位置参数（字符串），放进 `$ARGS.positional` |
| `--jsonargs` | 把剩余命令行参数作为位置参数（JSON），放进 `$ARGS.positional` |

具名参数（`--arg` 等）也可以从 `$ARGS.named` 里取。

```bash
jq -r --arg m HK '.[] | select(.mkt==$m) | .sn' tx.json          # → s1 s2 s5 s7
jq -c --argjson n 1002 '.[] | select(.uid==$n) | .sn' tx.json    # → "s4" "s5"
jq -n --slurpfile u users.json '$u | length'   # → 1（文件里只有一个 JSON 值：数组；取数据用 $u[0]）
jq -n --rawfile t users.json '$t | length'     # → 138（文件字符数）
jq -n -c '$ARGS.positional' --args a b c       # → ["a","b","c"]
jq -n -c '$ARGS.positional' --jsonargs 1 '{"x":2}'   # → [1,{"x":2}]
jq -n -c --arg a 1 '$ARGS.named'               # → {"a":"1"}
```

注意：`--arg` 传入的永远是字符串，`--arg n 1002` 后 `.uid == $n` 不会成立；比较数字要用 `--argjson`，或在过滤器里写 `($n | tonumber)`。

## 过滤器来源与模块

| 参数 | 含义 |
|---|---|
| `-f file`, `--from-file file` | 从文件读取过滤器，适合较长的表达式 |
| `-L directory` | 添加模块搜索路径，配合 `import` / `include` 使用 |

```bash
echo '.[] | select(.mkt=="HK") | .sn' > hk.jq
jq -r -f hk.jq tx.json             # → s1 s2 s5 s7
```

## 退出码与其他

| 参数 | 含义 |
|---|---|
| `-e`, `--exit-status` | 按输出设置退出码：最后一个输出既不是 `false` 也不是 `null` 时为 0；是 `false` / `null` 时为 1；没有任何输出时为 4 |
| `-V`, `--version` | 显示版本 |
| `--build-configuration` | 显示编译配置 |
| `-h`, `--help` | 显示帮助 |
| `--` | 结束参数解析，之后的内容不再当作选项 |

```bash
jq -e 'length > 0' users.json; echo $?                  # → true，0
jq -e '.[0].x' users.json; echo $?                      # → null，1
jq -e '.[] | select(.uid==9999)' users.json; echo $?    # → （无输出），4

# 在脚本里做断言
if jq -e 'all(.[]; .uid > 0)' tx.json >/dev/null; then echo ok; fi
```

不使用 `-e` 时，只要过滤器没有报错，退出码就是 0；出错时为 5（运行错误）或 2、3（用法或编译错误）。

## 常用组合

| 组合 | 用途 |
|---|---|
| `-r` + `@tsv` / `@csv` | 导出表格 |
| `-c` + `.[]` | 每行一条记录（JSON Lines） |
| `-s` + 多文件 | 把多个文件合并成一个数组再处理 |
| `-n` + `inputs` | 逐个读取输入，不会一次性全部载入 |
| `-R` + `fromjson?` | 处理混有非 JSON 行的日志：`jq -R 'fromjson? // .'` |
| `-e` + `>/dev/null` | 脚本中只看断言结果 |
