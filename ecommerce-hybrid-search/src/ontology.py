"""跑鞋领域本体。

这是整套架构里**最不像技术、但价值最高**的一个文件。

「适合扁平足的跑步鞋」搜不到东西，不是因为向量模型不够大，而是因为
商品描述里根本不会出现「扁平足」三个字。商家写的是「TPU 稳定片」「抗过度内旋」
「支撑系」。这中间隔着一条领域知识链：

    扁平足 → 足弓塌陷 → 落地时过度内旋(overpronation) → 需要稳定支撑系跑鞋

通用 embedding 模型不掌握这条链（它只会把「扁平足」拉近到「足部护理」「鞋垫」），
BM25 更不可能。所以这条链必须**显式地写下来**，然后：
    - L0 用它把商品描述抽成结构化属性
    - L1 用它把用户 query 翻译成结构化约束

一旦翻译完成，「适合扁平足」就变成了 support_type = '稳定支撑'，
一个 B-tree 就能解决的问题。

生产里这张表通常由领域专家 + LLM 半自动维护，规模在几百到几千条。
"""

from __future__ import annotations

# ---------------------------------------------------------------------------
# 属性值域
# ---------------------------------------------------------------------------

SUPPORT_TYPES = ["缓震", "稳定支撑", "竞速", "越野"]
PRONATION_TYPES = ["中性", "过度内旋", "内旋不足"]
WIDTHS = ["标准", "2E", "4E"]

# ---------------------------------------------------------------------------
# 用户词 → 结构化属性
#
# key   是用户会说的话（口语、症状、场景）
# value 是这句话应该被翻译成的结构化约束
# ---------------------------------------------------------------------------

USER_TERM_TO_ATTRS: dict[str, dict] = {
    # —— 足型 / 生物力学 ——
    "扁平足":   {"support_type": "稳定支撑", "pronation_fit": "过度内旋"},
    "平足":     {"support_type": "稳定支撑", "pronation_fit": "过度内旋"},
    "低足弓":   {"support_type": "稳定支撑", "pronation_fit": "过度内旋"},
    "足弓塌陷": {"support_type": "稳定支撑", "pronation_fit": "过度内旋"},
    "内旋过度": {"support_type": "稳定支撑", "pronation_fit": "过度内旋"},
    "过度内旋": {"support_type": "稳定支撑", "pronation_fit": "过度内旋"},
    "外翻":     {"support_type": "稳定支撑", "pronation_fit": "过度内旋"},
    "高足弓":   {"support_type": "缓震", "pronation_fit": "内旋不足"},
    "内旋不足": {"support_type": "缓震", "pronation_fit": "内旋不足"},
    "宽脚":     {"width": "4E"},
    "宽脚掌":   {"width": "4E"},
    "脚宽":     {"width": "4E"},

    # —— 体重 / 强度 ——
    "大体重":   {"support_type": "缓震", "min_cushion": 8},
    "体重大":   {"support_type": "缓震", "min_cushion": 8},
    "胖":       {"support_type": "缓震", "min_cushion": 8},

    # —— 场景 ——
    "马拉松":   {"support_type": "竞速"},
    "比赛":     {"support_type": "竞速"},
    "碳板":     {"support_type": "竞速", "has_carbon_plate": True},
    "破三":     {"support_type": "竞速", "has_carbon_plate": True},
    "越野":     {"support_type": "越野"},
    "山路":     {"support_type": "越野"},
    "泥地":     {"support_type": "越野"},
    "日常":     {"support_type": "缓震"},
    "慢跑":     {"support_type": "缓震"},
    "入门":     {"support_type": "缓震"},
    "新手":     {"support_type": "缓震"},

    # —— 形容词 → 数值 ——
    # 「轻量」是数值属性的形容词伪装。不翻译它，向量和 BM25 都只能瞎猜。
    "轻量":     {"weight_grams_max": 260},
    "轻便":     {"weight_grams_max": 260},
    "超轻":     {"weight_grams_max": 220},
    "很轻":     {"weight_grams_max": 240},
    "厚底":     {"min_cushion": 8},
    "缓震":     {"support_type": "缓震"},
    "软弹":     {"support_type": "缓震"},
}

# ---------------------------------------------------------------------------
# 商品文案词 → 结构化属性
#
# L0 离线抽取时用。注意它和上面那张表**词汇几乎不重叠**——
# 这正是「用户说的话」和「商家写的话」之间的鸿沟，也是纯词汇检索失效的根因。
# ---------------------------------------------------------------------------

DOC_TERM_TO_ATTRS: dict[str, dict] = {
    "TPU稳定片":   {"support_type": "稳定支撑"},
    "稳定片":       {"support_type": "稳定支撑"},
    "支撑系":       {"support_type": "稳定支撑"},
    "抗内旋":       {"support_type": "稳定支撑", "pronation_fit": "过度内旋"},
    "防内旋":       {"support_type": "稳定支撑", "pronation_fit": "过度内旋"},
    "足弓支撑":     {"support_type": "稳定支撑"},
    "双密度中底":   {"support_type": "稳定支撑"},
    "碳板":         {"support_type": "竞速", "has_carbon_plate": True},
    "碳纤维板":     {"support_type": "竞速", "has_carbon_plate": True},
    "竞速":         {"support_type": "竞速"},
    "超临界发泡":   {"support_type": "缓震"},
    "厚弹中底":     {"support_type": "缓震"},
    "全掌气垫":     {"support_type": "缓震"},
    "Vibram":       {"support_type": "越野"},
    "岩钉":         {"support_type": "越野"},
    "深齿大底":     {"support_type": "越野"},
    "宽楦":         {"width": "4E"},
    "加宽鞋楦":     {"width": "4E"},
}

# ---------------------------------------------------------------------------
# 同义词扩展：喂给 BM25 / tsquery，提升词汇召回
#
# 这是「穷人版的 learned sparse retrieval」。真上了 SPLADE 这类模型之后，
# 这张表可以退役——模型会自己学到 扁平足 该激活 支撑/稳定 这些 term。
# ---------------------------------------------------------------------------

SYNONYM_EXPANSION: dict[str, list[str]] = {
    "扁平足":   ["支撑", "稳定", "内旋", "足弓"],
    "平足":     ["支撑", "稳定", "内旋", "足弓"],
    "低足弓":   ["支撑", "稳定", "内旋"],
    "内旋过度": ["支撑", "稳定", "抗内旋"],
    "轻量":     ["轻便", "轻质"],
    "跑步鞋":   ["跑鞋", "运动鞋"],
    "跑鞋":     ["跑步鞋"],
    "大体重":   ["缓震", "厚底", "回弹"],
    "马拉松":   ["竞速", "碳板", "破三"],
    "越野":     ["山地", "抓地", "防滑"],
}


def expand_terms(terms: list[str]) -> list[str]:
    """把用户词扩展成一组检索词（去重，保序）。"""
    out: list[str] = []
    seen: set[str] = set()
    for t in terms:
        for w in [t, *SYNONYM_EXPANSION.get(t, [])]:
            if w not in seen:
                seen.add(w)
                out.append(w)
    return out


def attrs_from_terms(terms: list[str], table: dict[str, dict]) -> dict:
    """把一组词按给定映射表合并成属性字典。后出现的词覆盖先出现的。"""
    attrs: dict = {}
    for t in terms:
        attrs.update(table.get(t, {}))
    return attrs
