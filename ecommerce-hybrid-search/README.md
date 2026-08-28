# 电商混合检索 —— PostgreSQL 单体参考实现

用一个具体的 query 贯穿始终：

> **「适合扁平足的轻量跑步鞋，500 元以内」**

**先读文章：[ARCHITECTURE.md](ARCHITECTURE.md)** —— 讲清楚这个 query 的难点
为什么不在检索、而在 query 理解，以及一段流传很广的「一个 SQL 干掉三个微服务」
方案错在哪。这里是它的可跑版本。

延伸阅读：[这是RAG吗.md](这是RAG吗.md) —— 这套架构和 RAG 是什么关系，
迁到 RAG 场景要改哪几层。

---

## 五分钟跑起来

```bash
docker compose up -d          # ParadeDB = PostgreSQL + pgvector + pg_search
uv sync --extra local         # 装本地 embedding / 重排模型（首次约 1GB）
python3 data/gen_products.py  # 生成 320 条合成商品 + 10 个 query 的标注
uv run python -m src.l0_ingest
uv run python -m src.search "适合扁平足的轻量跑步鞋，500元以内"
uv run python bench/compare.py
```

**想更快看到东西**（零模型下载、零 API key，秒级启动）：

```bash
uv sync                                    # 不装 --extra local
EMBEDDING_BACKEND=hash uv run python -m src.l0_ingest
EMBEDDING_BACKEND=hash uv run python -m src.search "适合扁平足的轻量跑步鞋，500元以内"
```

管线完整可跑，但向量是哈希伪向量、没有语义，bench 数字没有参考意义。

---

## 六层管线

| 层 | 文件 | 做什么 |
|---|---|---|
| **L0** | [src/l0_ingest.py](src/l0_ingest.py) | 离线把商品文案抽成结构化属性。ROI 最高的一层 |
| **L1** | [src/l1_query_understanding.py](src/l1_query_understanding.py) | 把 query 拆成硬过滤 + 软属性 + 语义残余 + 检索词 |
| **L2** | [src/l2_recall.py](src/l2_recall.py) | 三路召回：BM25 / 向量 / 结构化，硬过滤全部下推 |
| **L3** | [src/l3_fusion.py](src/l3_fusion.py) | RRF 融合（并集）。旁边并排放着原文那个错误写法 |
| **L4** | [src/l4_rerank.py](src/l4_rerank.py) | Cross-Encoder 重排。质量提升最大的一层 |
| **L5** | [src/l5_business_rank.py](src/l5_business_rank.py) | 业务排序 + 同店打散 |
| **L6** | [bench/compare.py](bench/compare.py) | 六种方案的 NDCG@10 / Recall@50 / 延迟对比 |

支撑文件：[src/ontology.py](src/ontology.py)（领域本体，
`扁平足 → 过度内旋 → 稳定支撑` 那条链就写在这里）、
[sql/01_schema.sql](sql/01_schema.sql)、[sql/02_hybrid_search.sql](sql/02_hybrid_search.sql)。

---

## 常用命令

```bash
# 只看 L1 解析出了什么
uv run python -m src.l1_query_understanding "适合扁平足的轻量跑步鞋，500元以内"

# 打印各路召回的名次，看融合是怎么发生的
uv run python -m src.search "..." --explain

# 关掉重排，看 L4 到底贡献了多少
uv run python -m src.search "..." --reranker none

# 强制走规则解析（模拟 LLM 挂掉）
uv run python -m src.search "..." --no-llm

# 用 Claude 做 L0 属性抽取（需要 ANTHROPIC_API_KEY）
uv run python -m src.l0_ingest --extract llm
```

---

## 配置

复制 `.env.example` 为 `.env` 后按需改。全部可选——**什么都不配也能跑**。

| 变量 | 默认 | 说明 |
|---|---|---|
| `EMBEDDING_BACKEND` | `auto` | `local` 真模型 / `hash` 伪向量零下载 |
| `RERANKER_BACKEND` | `auto` | `local` / `claude` / `none` |
| `ANTHROPIC_API_KEY` | 未设 | 不设则 L1 自动走 jieba + 规则解析 |
| `CLAUDE_MODEL` | `claude-opus-5` | 生产的延迟敏感路径通常换 `claude-haiku-4-5` |
| `L1_TIMEOUT_SECONDS` | `1.5` | 超时立刻降级。query 理解不能是可用性硬依赖 |

---

## 降级路径

这个项目刻意做成**任何一个可选依赖缺失都还能跑**，因为这既方便读者，
也是生产架构本身该有的样子：

| 缺什么 | 降级成什么 | 影响 |
|---|---|---|
| `ANTHROPIC_API_KEY` | jieba + 规则解析 | 复杂 query 的解析质量下降，简单 query 基本无损 |
| `sentence-transformers` | 哈希伪向量 + 关闭重排 | **检索质量大幅下降**，只能演示管线 |
| `pg_search`（非 ParadeDB 镜像） | `tsvector` + `ts_rank_cd` | 词汇检索没有 IDF，低频词权重不对 |
| `pgvector < 0.8.0` | 无 `iterative_scan` | 带过滤的向量召回会静默丢结果，只能靠部分索引缓解 |

启动时会打印实际生效的后端组合，不会偷偷降级。

---

## 关于 pg_search 的 DDL

`pg_search` 的 BM25 索引语法（`WITH` 选项、中文分词器名字）在小版本之间变动过。
`src/l0_ingest.py` 会依次尝试 `chinese_compatible` → `chinese_lindera` → `jieba` → `default`，
全部失败就降级到 `tsvector` 路径并明确告知。

如果要 pin 版本，先确认当前语法：

```bash
docker compose exec db psql -U postgres -d ehs -c '\dx'
docker compose exec db psql -U postgres -d ehs -c '\df paradedb.*'
```

---

## 数据是合成的

`data/products.json` 由 `data/gen_products.py` 确定性生成（320 条），
里面刻意埋了三类陷阱来暴露单路检索的失效模式：

- **词汇陷阱** —— 真正适合扁平足的鞋，描述里绝不出现「扁平足」；
  而矫形鞋垫、1680 元的稳定鞋、中性缓震鞋的营销文案反而写了。
  **每一个字面命中「扁平足」的商品，都是 q1 的错误答案。**
- **语义陷阱** —— 鞋垫、运动袜、护踝在 embedding 空间里离「扁平足」很近，但不是鞋。
- **数值陷阱** —— 「轻量」「500 元以内」只能靠 query 理解翻译成 `WHERE`。

商品的**真实属性**在 `_gold` 字段里，只给标注用；管线看不到它，
L0 必须自己从文案里抽——所以文案写得含糊的商品，抽出来就是缺失或错的。
这个抽取噪声是有意保留的：如果 L0 完美，结构化召回会赢得毫无意义。

**bench 的数字只能说明方案之间的相对趋势，不是行业基准。**
跑完会打印一节完整的「局限」，引用前请读完。

---

## 环境要求

- Docker（ParadeDB 镜像）
- Python ≥ 3.10 + [uv](https://docs.astral.sh/uv/)
- `--extra local` 会拉进 torch，首次约 1GB。不想装就用 `EMBEDDING_BACKEND=hash`
