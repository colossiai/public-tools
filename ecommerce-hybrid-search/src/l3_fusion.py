"""L3：融合。

两个实现放在一起，方便直接对比：

    rrf()            —— 正确做法：并集 + Reciprocal Rank Fusion
    naive_weighted() —— 复现原文的写法：交集 + 未归一化加权和

bench 里两者都会跑，让「原文那个写法为什么差」变成可复现的数字。
"""

from __future__ import annotations

from .config import RRF_K

# 三路的默认权重。
# 词汇路最高，是因为电商 query 里精确匹配（品牌、型号、品类词）的权重
# 天然高于语义。这个比例应该用点击日志调，不该拍脑袋。
DEFAULT_WEIGHTS = {"semantic": 0.35, "lexical": 0.40, "structured": 0.25}


def rrf(paths: dict[str, list[int]],
        weights: dict[str, float] | None = None,
        k: int = RRF_K) -> list[tuple[int, float]]:
    """Reciprocal Rank Fusion。

        score(d) = Σ_i  w_i / (k + rank_i(d))

    只看**名次**，不看分数。这是它相对加权和的核心优势：

      余弦相似度 ∈ [0,1]，命中时普遍 0.7~0.9；
      BM25 分数无上界，量级随语料和 query 变化。
      这两个数直接加权求和，权重表达的根本不是你以为的意思。
      要修就得先归一化，而归一化又依赖当前 query 的分数分布，
      换个 query 就要重调。

    RRF 天生无量纲，所以 weights 里写的 0.4 就真的是 0.4。
    k=60 出自 Cormack 2009 那篇论文，Elasticsearch / OpenSearch 沿用为默认值。
    k 越大，头部名次之间的差距被压得越平，融合越「民主」。

    只被一路召回到的文档，其他路自然没有贡献——这就是并集语义：
    进不进候选集是一票赞成，不是一票否决。
    """
    weights = weights or DEFAULT_WEIGHTS
    scores: dict[int, float] = {}
    for path, ids in paths.items():
        w = weights.get(path, 0.0)
        if w == 0.0:
            continue
        for rank, doc_id in enumerate(ids, start=1):
            scores[doc_id] = scores.get(doc_id, 0.0) + w / (k + rank)
    return sorted(scores.items(), key=lambda kv: -kv[1])


def naive_weighted(semantic_scores: dict[int, float],
                   lexical_scores: dict[int, float],
                   w_semantic: float = 0.4,
                   w_lexical: float = 0.6) -> list[tuple[int, float]]:
    """复现原文的融合方式，用来量化它到底差在哪。

        final = 0.4 * (1 - cosine_distance) + 0.6 * ts_rank

    两个 bug 同时存在：

    ① **交集**：原文外层写的是 `WHERE ... @@ tsquery`，
       只有同时被两路命中的文档才能留下。这里用 dict 求交集来复现。
       后果：真正适合扁平足、但文案里没写「扁平足」的鞋，全被砍掉。

    ② **量纲不统一**：semantic ~0.8，ts_rank ~0.05。
       代入 0.4×0.8 + 0.6×0.05 = 0.32 + 0.03，
       语义项贡献了 91%。注释说「关键词权重更高」，代码做的正好相反。

    这个函数是**反面教材**，不要照抄。
    """
    common = set(semantic_scores) & set(lexical_scores)
    out = [
        (doc_id,
         w_semantic * semantic_scores[doc_id] + w_lexical * lexical_scores[doc_id])
        for doc_id in common
    ]
    return sorted(out, key=lambda kv: -kv[1])


def explain(paths: dict[str, list[int]], fused: list[tuple[int, float]],
            top: int = 10) -> list[dict]:
    """给每个融合结果标注它在各路里的名次，方便肉眼看融合是否合理。"""
    rank_of = {
        path: {doc_id: r for r, doc_id in enumerate(ids, start=1)}
        for path, ids in paths.items()
    }
    out = []
    for doc_id, score in fused[:top]:
        out.append({
            "id": doc_id,
            "score": score,
            "ranks": {p: rank_of[p].get(doc_id) for p in paths},
        })
    return out
