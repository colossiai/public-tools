"""L2：多路召回。

三路并行，各取 Top-N，硬过滤全部下推到每一路里面：

    词汇召回   BM25 —— 精确匹配、品牌型号、长尾
    向量召回   HNSW —— 语义残余部分
    结构化召回 B-tree —— L1 已经解析出明确属性约束时的兜底

这里为了可读性是顺序执行的，真实服务应该三路并发（asyncio / 线程池 / 或者
干脆写成 sql/02_hybrid_search.sql 里那条单条 SQL，让 PG 自己去并行）。
顺序执行的好处是能分别计时，看清每一路的延迟构成。

关于「硬过滤下推」有个常见误解要澄清：
把 WHERE 加到向量召回里，**不会**让向量搜索变快。pgvector 的 HNSW 是后过滤，
加了过滤只会让它更难凑够 LIMIT。下推的真正目的是让三路看到同一个候选空间，
融合出来的排名才有意义。
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field

import psycopg

from .config import RECALL_LIMIT
from .embedding import embed_one, to_pgvector
from .l1_query_understanding import ParsedQuery


@dataclass
class RecallResult:
    """每一路的召回结果：有序的 id 列表 + 耗时。"""
    paths: dict[str, list[int]] = field(default_factory=dict)
    timings_ms: dict[str, float] = field(default_factory=dict)
    # 词汇路的原始分数，naive_weighted 基线要用（正常管线用不到）
    lexical_scores: dict[int, float] = field(default_factory=dict)
    semantic_scores: dict[int, float] = field(default_factory=dict)

    def candidate_ids(self) -> list[int]:
        seen, out = set(), []
        for ids in self.paths.values():
            for i in ids:
                if i not in seen:
                    seen.add(i)
                    out.append(i)
        return out


def _hard_filter_sql(pq: ParsedQuery, alias: str = "p") -> tuple[str, dict]:
    """把 L1 解析出的硬过滤翻译成 SQL 片段 + 参数。"""
    clauses, params = [], {}
    if pq.in_stock:
        clauses.append(f"{alias}.stock > 0")
    if pq.category:
        clauses.append(f"{alias}.category = %(f_category)s")
        params["f_category"] = pq.category
    if pq.price_max is not None:
        clauses.append(f"{alias}.price <= %(f_price_max)s")
        params["f_price_max"] = pq.price_max
    if pq.price_min is not None:
        clauses.append(f"{alias}.price >= %(f_price_min)s")
        params["f_price_min"] = pq.price_min
    return (" AND ".join(clauses) or "TRUE"), params


def recall_semantic(conn, pq: ParsedQuery, limit: int) -> tuple[list[int], dict[int, float]]:
    """向量召回。只编码 residual_semantic —— 数值约束不该进 embedding。"""
    qv = to_pgvector(embed_one(pq.residual_semantic or pq.raw, is_query=True))
    where, params = _hard_filter_sql(pq)
    params["qv"] = qv
    params["lim"] = limit

    sql = f"""
        SELECT p.id, 1 - (p.embedding <=> %(qv)s::vector) AS sim
        FROM products p
        WHERE {where} AND p.embedding IS NOT NULL
        ORDER BY p.embedding <=> %(qv)s::vector
        LIMIT %(lim)s
    """
    with conn.cursor() as cur:
        cur.execute(sql, params)
        rows = cur.fetchall()
    return [r[0] for r in rows], {r[0]: float(r[1]) for r in rows}


def _segment_terms(terms: list[str]) -> list[str]:
    """tsrank 降级路径专用：把检索词按 jieba 再切一遍。

    因为 seg_text 是 jieba 切出来的，查询词也必须切成同样粒度才能匹配上。
    「稳定支撑」在索引里可能是「稳定」+「支撑」两个 lexeme。
    """
    import jieba

    out, seen = [], set()
    for t in terms:
        for w in jieba.cut(t):
            w = w.strip()
            if len(w) >= 1 and w not in seen and w.isalnum():
                seen.add(w)
                out.append(w)
    return out


def recall_lexical(conn, pq: ParsedQuery, limit: int, mode: str
                   ) -> tuple[list[int], dict[int, float]]:
    """词汇召回。mode = bm25（pg_search）| tsrank（PG 内置，无 IDF）。

    注意是 **OR 语义**。原方案用 plainto_tsquery 的 AND 语义，
    要求商品同时包含所有查询词，召回直接崩掉。
    """
    if not pq.keywords:
        return [], {}

    where, params = _hard_filter_sql(pq)
    params["lim"] = limit

    if mode == "bm25":
        params["qtext"] = " OR ".join(pq.keywords)
        sql = f"""
            SELECT p.id, paradedb.score(p.id) AS score
            FROM products p
            WHERE p.search_text @@@ %(qtext)s AND {where}
            ORDER BY score DESC
            LIMIT %(lim)s
        """
    else:
        toks = _segment_terms(pq.keywords)
        if not toks:
            return [], {}
        params["qtext"] = " | ".join(toks)
        sql = f"""
            SELECT p.id, ts_rank_cd(p.seg_tsv, to_tsquery('simple', %(qtext)s)) AS score
            FROM products p
            WHERE p.seg_tsv @@ to_tsquery('simple', %(qtext)s) AND {where}
            ORDER BY score DESC
            LIMIT %(lim)s
        """

    with conn.cursor() as cur:
        cur.execute(sql, params)
        rows = cur.fetchall()
    return [r[0] for r in rows], {r[0]: float(r[1]) for r in rows}


def recall_structured(conn, pq: ParsedQuery, limit: int) -> list[int]:
    """结构化召回：完全靠 L1 解析出的属性约束。

    如果 L1 什么属性都没解析出来，这一路退化成「按销量取热门」，
    仍然有价值——它保证了候选集里一定有一批基本盘商品。
    """
    where, params = _hard_filter_sql(pq)
    clauses = [where]
    if pq.support_type:
        clauses.append("p.support_type = %(f_support)s")
        params["f_support"] = pq.support_type
    if pq.weight_grams_max is not None:
        clauses.append("p.weight_grams <= %(f_weight_max)s")
        params["f_weight_max"] = pq.weight_grams_max
    if pq.width:
        clauses.append("p.width = %(f_width)s")
        params["f_width"] = pq.width
    if pq.has_carbon_plate:
        clauses.append("p.has_carbon_plate")
    if pq.min_cushion is not None:
        clauses.append("p.cushion_level >= %(f_cushion)s")
        params["f_cushion"] = pq.min_cushion
    params["lim"] = limit

    sql = f"""
        SELECT p.id
        FROM products p
        WHERE {' AND '.join(clauses)}
        ORDER BY p.sales_30d DESC, p.rating DESC
        LIMIT %(lim)s
    """
    with conn.cursor() as cur:
        cur.execute(sql, params)
        return [r[0] for r in cur.fetchall()]


def recall(conn: psycopg.Connection, pq: ParsedQuery, *, lexical_mode: str,
           limit: int = RECALL_LIMIT, paths: tuple[str, ...] = ("semantic", "lexical", "structured"),
           ) -> RecallResult:
    res = RecallResult()

    if "semantic" in paths:
        t0 = time.perf_counter()
        ids, scores = recall_semantic(conn, pq, limit)
        res.paths["semantic"] = ids
        res.semantic_scores = scores
        res.timings_ms["semantic"] = (time.perf_counter() - t0) * 1000

    if "lexical" in paths:
        t0 = time.perf_counter()
        ids, scores = recall_lexical(conn, pq, limit, lexical_mode)
        res.paths["lexical"] = ids
        res.lexical_scores = scores
        res.timings_ms["lexical"] = (time.perf_counter() - t0) * 1000

    if "structured" in paths:
        t0 = time.perf_counter()
        res.paths["structured"] = recall_structured(conn, pq, limit)
        res.timings_ms["structured"] = (time.perf_counter() - t0) * 1000

    return res


def fetch_products(conn: psycopg.Connection, ids: list[int]) -> dict[int, dict]:
    """一次性把候选商品的字段捞回来。"""
    if not ids:
        return {}
    sql = """
        SELECT id, product_name, brand, category, description, price, stock,
               shop_id, shop_name, rating, sales_30d, image_url,
               support_type, weight_grams, width, pronation_fit,
               has_carbon_plate, cushion_level
        FROM products WHERE id = ANY(%s)
    """
    with conn.cursor() as cur:
        cur.execute(sql, (ids,))
        cols = [d.name for d in cur.description]
        return {r[0]: dict(zip(cols, r)) for r in cur.fetchall()}
