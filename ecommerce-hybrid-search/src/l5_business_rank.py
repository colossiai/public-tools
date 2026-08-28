"""L5：业务排序 + 多样性打散。

技术文章最常漏掉的一层，但在真实电商里，**它对 GMV 的影响远大于 L2 的召回细节**。

最终顺序不等于相关性顺序：

    final = f(相关性, pCTR, pCVR, 履约时效, 库存深度, 利润率, 广告出价, 新品扶持)
            + 多样性打散

这里只实现一个能跑的简化版：相关性 + 点击先验 + 库存深度，再按店铺打散。
生产里 pCTR / pCVR 是独立训练的模型（LambdaMART 或者 DNN ranker），
广告出价来自另一条链路，权重由 A/B 实验定，不是拍脑袋。

**这一层必须放在重排之后**。顺序反了，商业因子会污染相关性判断，
你会得到一堆「高佣金但不相关」的结果，短期 GMV 好看，长期把用户赶走。
"""

from __future__ import annotations

import math
from collections import defaultdict


def _minmax(values: list[float]) -> list[float]:
    if not values:
        return []
    lo, hi = min(values), max(values)
    if hi - lo < 1e-9:
        return [0.5] * len(values)
    return [(v - lo) / (hi - lo) for v in values]


def click_prior(doc: dict) -> float:
    """pCTR 的穷人版替身：评分 + 销量。

    生产里这里是一个真正的 CTR 预估模型，特征包括用户画像、上下文、
    商品历史表现、query-商品交叉特征等等。
    """
    rating = float(doc.get("rating") or 4.0)
    sales = int(doc.get("sales_30d") or 0)
    # 销量取对数：从 10 到 100 的提升，比从 1000 到 1090 有意义得多
    return (rating - 3.5) / 1.5 * 0.5 + min(math.log1p(sales) / math.log(1000), 1.0) * 0.5


def fulfillment_score(doc: dict) -> float:
    """库存深度。库存 1 件和库存 500 件的转化率完全不同。"""
    stock = int(doc.get("stock") or 0)
    if stock <= 0:
        return 0.0
    return min(math.log1p(stock) / math.log(200), 1.0)


def business_rank(scored: list[tuple[dict, float]],
                  *,
                  top_k: int = 20,
                  w_relevance: float = 0.70,
                  w_click: float = 0.20,
                  w_fulfillment: float = 0.10,
                  max_per_shop: int = 2) -> list[dict]:
    """融合业务因子并按店铺打散，返回最终结果列表。"""
    if not scored:
        return []

    docs = [d for d, _ in scored]
    rel = _minmax([s for _, s in scored])
    clk = _minmax([click_prior(d) for d in docs])
    ful = [fulfillment_score(d) for d in docs]

    ranked = []
    for doc, r, c, f in zip(docs, rel, clk, ful):
        final = w_relevance * r + w_click * c + w_fulfillment * f
        ranked.append({
            **doc,
            "_relevance": r,
            "_click_prior": c,
            "_fulfillment": f,
            "_final_score": final,
        })
    ranked.sort(key=lambda d: -d["_final_score"])

    # 多样性打散：同一店铺优先最多 max_per_shop 个。
    # 不打散的话，头部很容易被一个店铺的同款不同色霸占，
    # 搜索结果页看起来只有两三个选择。
    #
    # 注意这是**软约束**：如果打散之后凑不够 top_k，下面会用被压下去的补齐，
    # 此时单店数量可能超过 max_per_shop。这是有意的——
    # 宁可某个店多占一个坑，也不要给用户一个不满 20 条的结果页。
    picked: list[dict] = []
    overflow: list[dict] = []
    per_shop: dict[str, int] = defaultdict(int)
    for d in ranked:
        shop = d.get("shop_id") or "?"
        if per_shop[shop] < max_per_shop:
            per_shop[shop] += 1
            picked.append(d)
        else:
            overflow.append(d)
        if len(picked) >= top_k:
            break

    # 打散后如果没凑够 top_k，用被压下去的补齐
    if len(picked) < top_k:
        picked.extend(overflow[: top_k - len(picked)])

    return picked[:top_k]
