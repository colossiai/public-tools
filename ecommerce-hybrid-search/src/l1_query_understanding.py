"""L1：Query 理解。

把一句自然语言拆成「硬过滤 + 软属性 + 语义残余 + 检索词」四份。

    「适合扁平足的轻量跑步鞋，500元以内」
        ↓
    hard   : category=跑步鞋, price_max=500, in_stock=True
    soft   : support_type=稳定支撑, weight_grams_max=260
    semantic: "适合扁平足日常慢跑的鞋"
    keywords: [跑步鞋, 跑鞋, 支撑, 稳定, 内旋, 足弓, 轻量, 轻便]

这一层做完之后，原来那个「向量搜不到、BM25 也搜不到」的查询，
大部分已经变成了 WHERE 子句。

工程上有两件事决定它能不能上生产：

1. **缓存**。搜索 query 的分布是长尾 Zipf，头部 query 的缓存命中率轻松 80%+。
   命中缓存时这一层的延迟是 0，LLM 的成本和延迟问题基本消失。

2. **降级**。给这层一个硬延迟预算，超时立刻走规则解析。
   query 理解绝不能成为搜索可用性的硬依赖——LLM 挂了，搜索还得能用。
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import time
from dataclasses import asdict, dataclass, field

from . import ontology
from .config import CACHE_DIR, MODELS


@dataclass
class ParsedQuery:
    raw: str

    # 硬过滤：必须满足，不满足就不该出现在结果里
    category: str | None = None
    price_min: float | None = None
    price_max: float | None = None
    in_stock: bool = True

    # 软属性：由领域知识翻译出来，用于结构化召回和重排
    support_type: str | None = None
    weight_grams_max: int | None = None
    width: str | None = None
    pronation_fit: str | None = None
    has_carbon_plate: bool | None = None
    min_cushion: int | None = None

    # 剩下的、真正需要向量去理解的部分
    residual_semantic: str = ""
    # 词汇检索用的词表（已做同义词扩展），OR 语义
    keywords: list[str] = field(default_factory=list)

    source: str = "rule"  # llm | cache | rule
    latency_ms: float = 0.0

    def hard_filters_summary(self) -> str:
        bits = []
        if self.category:
            bits.append(f"category={self.category}")
        if self.price_max is not None:
            bits.append(f"price<={self.price_max:g}")
        if self.price_min is not None:
            bits.append(f"price>={self.price_min:g}")
        if self.in_stock:
            bits.append("stock>0")
        return ", ".join(bits) or "(无)"

    def soft_attrs_summary(self) -> str:
        bits = []
        for k in ("support_type", "weight_grams_max", "width",
                  "pronation_fit", "has_carbon_plate", "min_cushion"):
            v = getattr(self, k)
            if v is not None:
                bits.append(f"{k}={v}")
        return ", ".join(bits) or "(无)"


# ---------------------------------------------------------------------------
# 规则解析器（降级路径）
# ---------------------------------------------------------------------------

CATEGORY_HINTS = [
    (["跑步鞋", "跑鞋", "跑步"], "跑步鞋"),
    (["篮球鞋", "打球"], "篮球鞋"),
    (["训练鞋", "健身房"], "训练鞋"),
    (["休闲鞋", "板鞋"], "休闲鞋"),
    (["鞋垫"], "鞋垫"),
    (["袜子", "运动袜"], "运动袜"),
]

# 「500元以内」「500块以下」「不超过500」
_MAX_PRICE = re.compile(r"(\d+)\s*(?:元|块|rmb|RMB|¥)?\s*(?:以内|以下|以内的|之内|内)")
_MAX_PRICE2 = re.compile(r"(?:不超过|低于|少于|预算)\s*(\d+)")
# 「500到800元」「500-800元」「500~800」
_RANGE_PRICE = re.compile(r"(\d+)\s*(?:到|-|~|至)\s*(\d+)\s*(?:元|块)?")


def parse_price(text: str) -> tuple[float | None, float | None]:
    m = _RANGE_PRICE.search(text)
    if m:
        lo, hi = float(m.group(1)), float(m.group(2))
        return (min(lo, hi), max(lo, hi))
    for pat in (_MAX_PRICE, _MAX_PRICE2):
        m = pat.search(text)
        if m:
            return (None, float(m.group(1)))
    return (None, None)


def parse_rule_based(query: str) -> ParsedQuery:
    t0 = time.perf_counter()
    pq = ParsedQuery(raw=query, source="rule")

    for hints, cat in CATEGORY_HINTS:
        if any(h in query for h in hints):
            pq.category = cat
            break

    pq.price_min, pq.price_max = parse_price(query)

    # 领域词表：直接在原文里扫子串，比先分词再匹配更稳
    # （jieba 未必会把「扁平足」「内旋过度」切成一个词）
    hits = [term for term in ontology.USER_TERM_TO_ATTRS if term in query]
    attrs = ontology.attrs_from_terms(hits, ontology.USER_TERM_TO_ATTRS)

    pq.support_type = attrs.get("support_type")
    pq.weight_grams_max = attrs.get("weight_grams_max")
    pq.width = attrs.get("width")
    pq.pronation_fit = attrs.get("pronation_fit")
    pq.has_carbon_plate = attrs.get("has_carbon_plate")
    pq.min_cushion = attrs.get("min_cushion")

    # 检索词：命中的领域词 + jieba 切出来的实词，再做同义词扩展
    try:
        import jieba

        toks = [w for w in jieba.cut(query)
                if len(w) >= 2 and not w.isdigit() and w not in {"以内", "以下", "适合"}]
    except ImportError:
        toks = []
    pq.keywords = ontology.expand_terms(list(dict.fromkeys([*hits, *toks])))

    # 语义残余：把数值约束从原文里去掉，剩下的才该交给向量
    residual = _RANGE_PRICE.sub("", _MAX_PRICE.sub("", _MAX_PRICE2.sub("", query)))
    pq.residual_semantic = residual.strip(" ，,。") or query

    pq.latency_ms = (time.perf_counter() - t0) * 1000
    return pq


# ---------------------------------------------------------------------------
# Claude 解析器
# ---------------------------------------------------------------------------

QUERY_SCHEMA = {
    "type": "object",
    "properties": {
        "category": {"type": ["string", "null"],
                     "enum": ["跑步鞋", "篮球鞋", "训练鞋", "休闲鞋", "鞋垫", "运动袜", None]},
        "price_min": {"type": ["number", "null"]},
        "price_max": {"type": ["number", "null"]},
        "support_type": {"type": ["string", "null"], "enum": [*ontology.SUPPORT_TYPES, None]},
        "weight_grams_max": {"type": ["integer", "null"]},
        "width": {"type": ["string", "null"], "enum": [*ontology.WIDTHS, None]},
        "pronation_fit": {"type": ["string", "null"], "enum": [*ontology.PRONATION_TYPES, None]},
        "has_carbon_plate": {"type": ["boolean", "null"]},
        "min_cushion": {"type": ["integer", "null"]},
        "residual_semantic": {"type": "string"},
        "keywords": {"type": "array", "items": {"type": "string"}},
    },
    "required": ["category", "price_min", "price_max", "support_type", "weight_grams_max",
                 "width", "pronation_fit", "has_carbon_plate", "min_cushion",
                 "residual_semantic", "keywords"],
    "additionalProperties": False,
}

L1_SYSTEM = f"""你是电商跑鞋搜索的 query 解析器。把用户的自然语言查询拆成结构化约束。

核心原则：**能变成 WHERE 条件的，都不要留给向量检索。**

数值约束：
- 「500元以内」→ price_max=500；「500到800」→ price_min=500, price_max=800
- 「轻量」不是形容词，是数值约束 → weight_grams_max=260；「超轻」→ 220

领域知识映射（这是重点，商品文案里不会出现用户说的这些词）：
- 扁平足 / 平足 / 低足弓 / 足弓塌陷 / 内旋过度 → support_type=稳定支撑, pronation_fit=过度内旋
- 高足弓 / 内旋不足 → support_type=缓震, pronation_fit=内旋不足
- 宽脚 / 宽脚掌 → width=4E
- 马拉松 / 比赛 / 碳板 / 破三 → support_type=竞速
- 越野 / 山路 / 泥地 → support_type=越野
- 大体重 / 入门 / 日常慢跑 → support_type=缓震

residual_semantic：去掉所有已经结构化的部分之后，**剩下的、真正需要语义理解的描述**。
如果全部都结构化了，给一句概括使用场景的短句。

keywords：给 BM25 用的检索词，OR 语义。既要包含用户原话里的词，
也要包含商家文案里可能出现的对应说法（比如用户说「扁平足」，
就要加上「支撑」「稳定」「内旋」「足弓」）。8-12 个词。

可用的属性值域：
  support_type: {ontology.SUPPORT_TYPES}
  width: {ontology.WIDTHS}
  pronation_fit: {ontology.PRONATION_TYPES}"""


def _cache_path(query: str) -> str:
    h = hashlib.sha1(query.strip().encode("utf-8")).hexdigest()[:16]
    return os.path.join(CACHE_DIR, "l1", f"{h}.json")


def _load_cache(query: str) -> dict | None:
    p = _cache_path(query)
    if os.path.exists(p):
        try:
            with open(p, encoding="utf-8") as f:
                return json.load(f)
        except (OSError, json.JSONDecodeError):
            return None
    return None


def _save_cache(query: str, payload: dict) -> None:
    p = _cache_path(query)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=1)


def parse_with_claude(query: str, timeout: float) -> ParsedQuery | None:
    """调 Claude 解析。任何失败都返回 None，让调用方走降级。"""
    try:
        import anthropic
    except ImportError:
        return None

    try:
        client = anthropic.Anthropic(timeout=timeout, max_retries=0)
        resp = client.messages.create(
            model=MODELS.claude_model,
            max_tokens=1024,
            system=L1_SYSTEM,
            messages=[{"role": "user", "content": query}],
            output_config={"format": {"type": "json_schema", "schema": QUERY_SCHEMA}},
        )
        text = "".join(b.text for b in resp.content if b.type == "text")
        data = json.loads(text)
    except Exception:
        # 超时、限流、网络错误、schema 不匹配……一律降级。
        # 搜索的可用性不能被 LLM 拖下水。
        return None

    pq = ParsedQuery(raw=query, source="llm")
    for k in ("category", "price_min", "price_max", "support_type", "weight_grams_max",
              "width", "pronation_fit", "has_carbon_plate", "min_cushion"):
        setattr(pq, k, data.get(k))
    pq.residual_semantic = data.get("residual_semantic") or query
    pq.keywords = ontology.expand_terms(data.get("keywords") or [])
    return pq


# ---------------------------------------------------------------------------
# 对外入口
# ---------------------------------------------------------------------------

def understand(query: str, *, use_llm: bool = True, verbose: bool = False) -> ParsedQuery:
    t0 = time.perf_counter()

    if use_llm:
        cached = _load_cache(query)
        if cached is not None:
            pq = ParsedQuery(**{**cached, "raw": query})
            pq.source = "cache"
            pq.latency_ms = (time.perf_counter() - t0) * 1000
            if verbose:
                print(f"[L1] 缓存命中，{pq.latency_ms:.1f}ms")
            return pq

    if use_llm and MODELS.has_anthropic_key:
        pq = parse_with_claude(query, MODELS.l1_timeout)
        if pq is not None:
            pq.latency_ms = (time.perf_counter() - t0) * 1000
            payload = asdict(pq)
            payload.pop("raw", None)
            payload.pop("latency_ms", None)
            _save_cache(query, payload)
            if verbose:
                print(f"[L1] Claude 解析，{pq.latency_ms:.1f}ms")
            return pq
        if verbose:
            print(f"[L1] Claude 不可用或超时（预算 {MODELS.l1_timeout}s），降级到规则解析")

    pq = parse_rule_based(query)
    pq.latency_ms = (time.perf_counter() - t0) * 1000
    if verbose:
        why = "无 ANTHROPIC_API_KEY" if not MODELS.has_anthropic_key else "LLM 降级"
        print(f"[L1] 规则解析（{why}），{pq.latency_ms:.1f}ms")
    return pq


if __name__ == "__main__":
    import sys

    q = sys.argv[1] if len(sys.argv) > 1 else "适合扁平足的轻量跑步鞋，500元以内"
    pq = understand(q, verbose=True)
    print(json.dumps(asdict(pq), ensure_ascii=False, indent=2))
