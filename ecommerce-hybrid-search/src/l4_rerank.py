"""L4：Cross-Encoder 重排。

**这一层通常是整条管线里质量提升最大的一层。**

原因是结构性的。召回用的双塔模型（bi-encoder）把 query 和 doc 分别编码成
两个向量，再算余弦——两边在编码时**互相看不见**：

    双塔:   query ──► [编码] ──► vec_q ─┐
                                        ├─► cosine
            doc   ──► [编码] ──► vec_d ─┘

    交叉:   [query, doc] ──► [一起编码] ──► 相关性分数

只有交叉编码器能回答「这双鞋的 TPU 稳定片，是否回应了『适合扁平足』这个诉求」
——因为它同时看到了两边。代价是不能预计算，必须为每个候选跑一次前向，
所以只能放在召回之后，对 Top-50 这个量级做。

三档后端：
    local  —— sentence-transformers 的 CrossEncoder（推荐）
    claude —— 让 LLM 打分。质量最高，延迟和成本也最高，适合头部高价值 query
    none   —— 不重排，直接用 L3 的融合分
"""

from __future__ import annotations

import json
import threading

from .config import MODELS

_model = None
_lock = threading.Lock()


def resolve_backend() -> str:
    want = MODELS.reranker_backend
    if want in ("local", "claude", "none"):
        return want
    try:
        import sentence_transformers  # noqa: F401

        return "local"
    except ImportError:
        return "none"


def _load_local():
    global _model
    with _lock:
        if _model is None:
            from sentence_transformers import CrossEncoder

            _model = CrossEncoder(MODELS.reranker_model)
    return _model


def _doc_text(p: dict) -> str:
    """喂给重排模型的文档表示。

    把结构化属性也拼进去很关键：模型看到「support_type: 稳定支撑」
    比让它从「内侧 TPU 稳定片」这句话里自己推，要可靠得多。
    L0 抽出来的属性在这里第二次发挥价值。
    """
    bits = [p["product_name"]]
    attrs = []
    if p.get("support_type"):
        attrs.append(f"类型{p['support_type']}")
    if p.get("weight_grams"):
        attrs.append(f"重量{p['weight_grams']}克")
    if p.get("width") and p["width"] != "标准":
        attrs.append(f"{p['width']}宽楦")
    if p.get("pronation_fit"):
        attrs.append(f"适合{p['pronation_fit']}")
    if attrs:
        bits.append("，".join(attrs))
    bits.append(f"售价{p['price']}元")
    bits.append(p["description"])
    return "。".join(str(b) for b in bits)


def rerank_local(query: str, docs: list[dict]) -> list[float]:
    model = _load_local()
    pairs = [(query, _doc_text(d)) for d in docs]
    scores = model.predict(pairs, show_progress_bar=False)
    return [float(s) for s in scores]


RERANK_SYSTEM = """你是电商跑鞋搜索的相关性打分器。

给你一个用户 query 和一组候选商品，为每个商品打 0-3 分：
  3 = 完全满足用户的所有诉求
  2 = 满足主要诉求，但某个次要条件不理想
  1 = 沾边，但有明显不匹配
  0 = 不相关

打分要点：
- 用户提的**硬条件**（价格、品类）不满足，最高只能给 1 分。
- 注意区分营销话术和实际结构。文案写「扁平足也能穿」的中性缓震鞋，
  并不真的适合扁平足——扁平足需要的是稳定支撑结构。
- 不是鞋的商品（鞋垫、袜子、护具），对「找鞋」的 query 一律 0 分。

返回一个 JSON 数组，长度和候选数一致，元素是整数分数，顺序对应输入顺序。"""


def rerank_claude(query: str, docs: list[dict]) -> list[float]:
    """LLM 重排。适合头部高价值 query，或者用来给 cross-encoder 造训练数据。"""
    import anthropic

    client = anthropic.Anthropic()
    listing = "\n".join(
        f"[{i}] {_doc_text(d)[:220]}" for i, d in enumerate(docs)
    )
    resp = client.messages.create(
        model=MODELS.claude_model,
        max_tokens=4000,
        system=RERANK_SYSTEM,
        messages=[{"role": "user",
                   "content": f"用户 query：{query}\n\n候选商品（共 {len(docs)} 个）：\n{listing}"}],
        output_config={"format": {"type": "json_schema", "schema": {
            "type": "array", "items": {"type": "integer", "minimum": 0, "maximum": 3},
        }}},
    )
    text = "".join(b.text for b in resp.content if b.type == "text")
    scores = json.loads(text)
    if len(scores) != len(docs):
        return [0.0] * len(docs)
    return [float(s) for s in scores]


def rerank(query: str, docs: list[dict], *, backend: str | None = None
           ) -> list[tuple[dict, float]]:
    """返回 [(doc, score)]，按分数降序。backend=none 时保持原顺序。"""
    if not docs:
        return []
    b = backend or resolve_backend()

    if b == "none":
        n = len(docs)
        return [(d, float(n - i)) for i, d in enumerate(docs)]

    try:
        scores = rerank_local(query, docs) if b == "local" else rerank_claude(query, docs)
    except Exception as e:
        print(f"[L4] 重排失败（{type(e).__name__}: {e}），退回融合顺序")
        n = len(docs)
        return [(d, float(n - i)) for i, d in enumerate(docs)]

    return sorted(zip(docs, scores), key=lambda ds: -ds[1])
