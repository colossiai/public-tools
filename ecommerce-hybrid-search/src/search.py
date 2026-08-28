"""端到端检索 CLI —— 把六层逐层打印出来。

    uv run python -m src.search "适合扁平足的轻量跑步鞋，500元以内"
    uv run python -m src.search "..." --no-llm          # 强制走规则解析
    uv run python -m src.search "..." --reranker none   # 关掉重排看差别
    uv run python -m src.search "..." --explain         # 打印各路名次

这个脚本的目的不是「返回结果」，而是**让每一层做了什么变得可见**。
尤其值得看的两处：

  1. L1 解析出来的 JSON —— 「适合扁平足」怎么变成 support_type=稳定支撑 的
  2. L4 重排前后的 Top-10 对比 —— 交叉编码器到底改了什么
"""

from __future__ import annotations

import argparse
import json
import os
import time
from dataclasses import asdict

from .config import RECALL_LIMIT, RERANK_LIMIT, TOP_K
from .db import apply_session_tuning, connect, detect_capabilities
from .embedding import backend as embed_backend
from .l1_query_understanding import understand
from .l2_recall import fetch_products, recall
from .l3_fusion import DEFAULT_WEIGHTS, explain, rrf
from .l4_rerank import rerank, resolve_backend as resolve_reranker
from .l5_business_rank import business_rank


def _fmt_row(i: int, d: dict, score_key: str | None = None) -> str:
    attrs = []
    if d.get("support_type"):
        attrs.append(d["support_type"])
    if d.get("weight_grams"):
        attrs.append(f"{d['weight_grams']}g")
    if d.get("width") and d["width"] != "标准":
        attrs.append(d["width"])
    attr_s = "/".join(attrs) or "-"
    score_s = f"{d[score_key]:.4f}" if score_key and score_key in d else ""
    return (f"  {i:>2}. [{d['id']:>3}] {d['product_name'][:30]:<30} "
            f"¥{float(d['price']):>7.0f}  {attr_s:<20} {score_s}")


def main() -> int:
    ap = argparse.ArgumentParser(description="电商混合检索端到端 demo")
    ap.add_argument("query", nargs="?", default="适合扁平足的轻量跑步鞋，500元以内")
    ap.add_argument("--no-llm", action="store_true", help="跳过 Claude，强制规则解析")
    ap.add_argument("--reranker", choices=["auto", "local", "claude", "none"], default="auto")
    ap.add_argument("--explain", action="store_true", help="打印各路召回名次")
    ap.add_argument("--top", type=int, default=TOP_K)
    args = ap.parse_args()

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

    print("=" * 78)
    print(f"Query: {args.query}")
    print(f"后端: 词汇={lexical_mode}  向量={embed_backend()}  "
          f"重排={args.reranker if args.reranker != 'auto' else resolve_reranker()}")
    print("=" * 78)

    t_all = time.perf_counter()

    # ---------------- L1 ----------------
    pq = understand(args.query, use_llm=not args.no_llm, verbose=True)
    print(f"\n【L1】Query 理解  ({pq.source}, {pq.latency_ms:.0f}ms)")
    print(f"  硬过滤   : {pq.hard_filters_summary()}")
    print(f"  软属性   : {pq.soft_attrs_summary()}")
    print(f"  语义残余 : {pq.residual_semantic}")
    print(f"  检索词   : {' '.join(pq.keywords[:12])}")
    if pq.support_type:
        print(f"  ↑ 注意：「{args.query[:12]}…」里的诉求已经被翻译成了 "
              f"support_type={pq.support_type}，这一步之后它就是个 WHERE 条件了。")

    # ---------------- L2 ----------------
    t0 = time.perf_counter()
    rec = recall(conn, pq, lexical_mode=lexical_mode, limit=RECALL_LIMIT)
    l2_ms = (time.perf_counter() - t0) * 1000
    print(f"\n【L2】多路召回  ({l2_ms:.0f}ms)")
    for path, ids in rec.paths.items():
        print(f"  {path:<11}: {len(ids):>3} 条   {rec.timings_ms[path]:>6.1f}ms")
    print(f"  并集候选   : {len(rec.candidate_ids())} 条")

    # ---------------- L3 ----------------
    fused = rrf(rec.paths, DEFAULT_WEIGHTS)
    print(f"\n【L3】RRF 融合  → {len(fused)} 条")
    if args.explain:
        for e in explain(rec.paths, fused, top=10):
            r = e["ranks"]
            print(f"  [{e['id']:>3}] rrf={e['score']:.5f}  "
                  f"语义#{r.get('semantic') or '-':<4} "
                  f"词汇#{r.get('lexical') or '-':<4} "
                  f"结构#{r.get('structured') or '-'}")

    cand_ids = [doc_id for doc_id, _ in fused[:RERANK_LIMIT]]
    products = fetch_products(conn, cand_ids)
    docs = [products[i] for i in cand_ids if i in products]

    print("\n  融合后 Top-10（重排之前）:")
    for i, d in enumerate(docs[:10], 1):
        print(_fmt_row(i, d))

    # ---------------- L4 ----------------
    t0 = time.perf_counter()
    reranked = rerank(args.query, docs,
                      backend=None if args.reranker == "auto" else args.reranker)
    l4_ms = (time.perf_counter() - t0) * 1000
    print(f"\n【L4】Cross-Encoder 重排  ({l4_ms:.0f}ms, {len(docs)} 个候选)")

    before = {d["id"]: i for i, d in enumerate(docs, 1)}
    print("  重排后 Top-10（括号内是重排前的名次）:")
    for i, (d, s) in enumerate(reranked[:10], 1):
        moved = before.get(d["id"], "?")
        arrow = "  " if moved == i else ("↑" if isinstance(moved, int) and moved > i else "↓")
        print(_fmt_row(i, d) + f"  {arrow}(#{moved})")

    # ---------------- L5 ----------------
    final = business_rank(reranked, top_k=args.top)
    print(f"\n【L5】业务排序 + 店铺打散  → 最终 {len(final)} 条")
    for i, d in enumerate(final, 1):
        print(_fmt_row(i, d, "_final_score") + f"  {d['shop_name'][:12]}")

    print(f"\n端到端耗时: {(time.perf_counter() - t_all) * 1000:.0f}ms")
    conn.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
