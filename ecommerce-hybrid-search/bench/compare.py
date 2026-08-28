"""L6：评估闭环 —— 六种检索方案的横向对比。

    uv run python bench/compare.py
    uv run python bench/compare.py --no-llm      # 不调 Claude，全走规则解析
    uv run python bench/compare.py --no-rerank   # 跳过重排（省时间）

对比的六种方案：

    bm25_only       纯词汇检索，无 query 理解
    vector_only     纯向量检索，无 query 理解
    naive_weighted  **复现原文的写法**：交集 + 未归一化加权和
    rrf             并集 + RRF，但仍然没有 query 理解
    rrf_qu          + L1 query 理解（硬过滤 + 结构化召回）
    rrf_qu_rerank   + L4 cross-encoder 重排

指标：NDCG@10（分级相关性）、Recall@50、延迟 p50/p95。

⚠️ 关于这些数字的效力，请先读最后打印的「局限」一节再引用。
"""

from __future__ import annotations

import argparse
import json
import math
import os
import statistics
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.config import DATA_DIR, RECALL_LIMIT, RERANK_LIMIT  # noqa: E402
from src.db import apply_session_tuning, connect, detect_capabilities  # noqa: E402
from src.embedding import backend as embed_backend  # noqa: E402
from src.l1_query_understanding import ParsedQuery, parse_rule_based, understand  # noqa: E402
from src.l2_recall import fetch_products, recall  # noqa: E402
from src.l3_fusion import naive_weighted, rrf  # noqa: E402
from src.l4_rerank import rerank, resolve_backend as resolve_reranker  # noqa: E402


# ---------------------------------------------------------------------------
# 指标
# ---------------------------------------------------------------------------

def dcg(gains: list[float]) -> float:
    return sum(g / math.log2(i + 2) for i, g in enumerate(gains))


def ndcg_at_k(ranked_ids: list[int], rels: dict[str, int], k: int = 10) -> float:
    """分级相关性的 NDCG。增益用 2^rel - 1，让 grade 2 的价值明显高于 grade 1。"""
    gains = [2 ** rels.get(str(i), 0) - 1 for i in ranked_ids[:k]]
    ideal = sorted((2 ** v - 1 for v in rels.values()), reverse=True)[:k]
    idcg = dcg(ideal)
    return dcg(gains) / idcg if idcg > 0 else 0.0


def recall_at_k(ranked_ids: list[int], rels: dict[str, int], k: int = 50) -> float:
    if not rels:
        return 0.0
    hit = sum(1 for i in ranked_ids[:k] if str(i) in rels)
    return hit / len(rels)


# ---------------------------------------------------------------------------
# 各方案
# ---------------------------------------------------------------------------

def bare_query(raw: str) -> ParsedQuery:
    """没有 query 理解时的「解析」结果：只切词，不做任何约束翻译。

    这是为了公平——bm25_only / vector_only / rrf 三个基线都不该享受
    L1 带来的硬过滤和属性映射。
    """
    pq = parse_rule_based(raw)
    return ParsedQuery(
        raw=raw,
        category=None, price_min=None, price_max=None, in_stock=True,
        residual_semantic=raw,
        keywords=pq.keywords,
        source="none",
    )


def run_variant(conn, name: str, raw: str, lexical_mode: str,
                use_llm: bool, do_rerank: bool) -> tuple[list[int], float]:
    """跑一种方案，返回 (排序后的 id 列表, 耗时 ms)。"""
    t0 = time.perf_counter()

    if name in ("bm25_only", "vector_only", "naive_weighted", "rrf"):
        pq = bare_query(raw)
    else:
        pq = understand(raw, use_llm=use_llm)

    if name == "bm25_only":
        rec = recall(conn, pq, lexical_mode=lexical_mode,
                     limit=RECALL_LIMIT, paths=("lexical",))
        ids = rec.paths["lexical"]

    elif name == "vector_only":
        rec = recall(conn, pq, lexical_mode=lexical_mode,
                     limit=RECALL_LIMIT, paths=("semantic",))
        ids = rec.paths["semantic"]

    elif name == "naive_weighted":
        # 复现原文：向量召回 + 词汇**交集** + 未归一化加权和
        rec = recall(conn, pq, lexical_mode=lexical_mode,
                     limit=RECALL_LIMIT, paths=("semantic", "lexical"))
        fused = naive_weighted(rec.semantic_scores, rec.lexical_scores,
                               w_semantic=0.4, w_lexical=0.6)
        ids = [i for i, _ in fused]

    elif name == "rrf":
        rec = recall(conn, pq, lexical_mode=lexical_mode,
                     limit=RECALL_LIMIT, paths=("semantic", "lexical"))
        ids = [i for i, _ in rrf(rec.paths, {"semantic": 0.45, "lexical": 0.55})]

    else:  # rrf_qu / rrf_qu_rerank
        rec = recall(conn, pq, lexical_mode=lexical_mode, limit=RECALL_LIMIT)
        ids = [i for i, _ in rrf(rec.paths)]

        if name == "rrf_qu_rerank" and do_rerank:
            head = ids[:RERANK_LIMIT]
            products = fetch_products(conn, head)
            docs = [products[i] for i in head if i in products]
            reranked = rerank(raw, docs)
            ids = [d["id"] for d, _ in reranked] + ids[RERANK_LIMIT:]

    return ids, (time.perf_counter() - t0) * 1000


VARIANTS = [
    ("bm25_only",      "纯 BM25，无 query 理解"),
    ("vector_only",    "纯向量，无 query 理解"),
    ("naive_weighted", "原文写法：交集 + 未归一化加权和"),
    ("rrf",            "并集 + RRF，仍无 query 理解"),
    ("rrf_qu",         "+ L1 query 理解"),
    ("rrf_qu_rerank",  "+ L4 cross-encoder 重排"),
]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--no-llm", action="store_true")
    ap.add_argument("--no-rerank", action="store_true")
    args = ap.parse_args()

    qrels_path = os.path.join(DATA_DIR, "qrels.json")
    if not os.path.exists(qrels_path):
        print("找不到 qrels.json，先跑：python3 data/gen_products.py", file=sys.stderr)
        return 1
    with open(qrels_path, encoding="utf-8") as f:
        qrels = json.load(f)

    conn = connect()
    caps = detect_capabilities(conn)
    apply_session_tuning(conn, caps)

    caps_file = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                             ".cache_caps.json")
    lexical_mode = caps.lexical
    if os.path.exists(caps_file):
        try:
            with open(caps_file) as f:
                lexical_mode = json.load(f).get("lexical", lexical_mode)
        except (OSError, json.JSONDecodeError):
            pass

    rr = resolve_reranker() if not args.no_rerank else "none"
    print(f"后端：词汇={lexical_mode}  向量={embed_backend()}  重排={rr}")
    print(f"评测集：{len(qrels)} 个 query\n")

    results: dict[str, dict] = {}
    for name, _desc in VARIANTS:
        ndcgs, recalls, lats = [], [], []
        for qid, entry in qrels.items():
            ids, ms = run_variant(conn, name, entry["query"], lexical_mode,
                                  use_llm=not args.no_llm, do_rerank=not args.no_rerank)
            ndcgs.append(ndcg_at_k(ids, entry["relevance"], 10))
            recalls.append(recall_at_k(ids, entry["relevance"], 50))
            lats.append(ms)
        results[name] = {
            "ndcg10": statistics.mean(ndcgs),
            "recall50": statistics.mean(recalls),
            "p50": statistics.median(lats),
            "p95": sorted(lats)[max(0, int(len(lats) * 0.95) - 1)],
            "per_query_ndcg": dict(zip(qrels.keys(), ndcgs)),
        }
        print(f"  {name:<16} 跑完")

    # ---- 汇总表 ----
    base = results["bm25_only"]["ndcg10"]
    print()
    print(f"{'方案':<16} {'NDCG@10':>9} {'vs BM25':>9} {'Recall@50':>10} "
          f"{'p50(ms)':>9} {'p95(ms)':>9}   说明")
    print("-" * 108)
    for name, desc in VARIANTS:
        r = results[name]
        delta = (r["ndcg10"] - base) / base * 100 if base > 0 else 0.0
        print(f"{name:<16} {r['ndcg10']:>9.4f} {delta:>8.1f}% {r['recall50']:>10.4f} "
              f"{r['p50']:>9.1f} {r['p95']:>9.1f}   {desc}")

    # ---- 逐 query 看 NDCG@10 ----
    print()
    print("逐 query NDCG@10：")
    header = f"{'qid':<5} " + " ".join(f"{n[:13]:>14}" for n, _ in VARIANTS)
    print(header)
    print("-" * len(header))
    for qid, entry in qrels.items():
        row = f"{qid:<5} " + " ".join(
            f"{results[n]['per_query_ndcg'][qid]:>14.4f}" for n, _ in VARIANTS
        )
        print(row)
    print()
    for qid, entry in qrels.items():
        print(f"  {qid} = {entry['query']}")

    # ---- 局限（必读） ----
    print()
    print("=" * 78)
    print("这些数字的局限 —— 引用前请先读完")
    print("=" * 78)
    print("""
1. 数据是合成的。320 条商品、10 个 query，规模比真实电商小四五个数量级。
   这里能说明的是**方案之间的相对趋势**，不是任何意义上的行业基准。
   任何把这种规模的数字包装成「召回率提升 37%」发出去的做法，都不可信——
   包括本项目自己的数字。

2. 合成数据对结构化召回有系统性偏袒。qrels 的判据是商品的真实属性，
   而 rrf_qu 这一路正好是按属性过滤的。为了削弱这层循环论证，
   L0 抽取被刻意做成有噪声的（文案没写克重就抽不出来，
   营销话术会误导 support_type），但偏袒依然存在，没有消除。

3. 用 hash 伪向量跑的话，vector_only 和 bm25_only 会高度相关，
   混合检索的增益会被严重低估。要看有意义的数字必须 `uv sync --extra local`。

4. 真实系统里还有两块这里完全没有的东西：用户行为召回（i2i / u2i）
   和 CTR/CVR 预估。在成熟电商里，这两块对最终转化的影响
   通常大于本项目讨论的全部检索技巧之和。

5. 延迟数字是单机、小数据、无并发下测的，不能外推到生产。
   尤其 L1 走 Claude 时的延迟高度依赖缓存命中率，
   而缓存命中率取决于真实 query 分布——合成评测集里每个 query 只跑一次，
   反映不出生产环境 80%+ 的命中率。
""")

    conn.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
