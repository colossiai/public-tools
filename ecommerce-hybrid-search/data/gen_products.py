#!/usr/bin/env python3
"""生成合成商品目录 + 人工相关性标注（qrels）。

    python3 data/gen_products.py

只用标准库，确定性（固定随机种子），产出 products.json / qrels.json。

设计上刻意埋了三类「陷阱」，用来暴露单路检索的失效模式：

1. **词汇陷阱**：真正适合扁平足的鞋，描述里绝不出现「扁平足」三个字，
   写的是「TPU 稳定片」「抗过度内旋」。而少数**不合适**的商品
   （鞋垫、超预算的鞋、纯缓震鞋的营销文案）反而把「扁平足」写在了标题里。
   → 纯 BM25 会把陷阱排到最前面。

2. **语义陷阱**：鞋垫、运动袜、护踝在 embedding 空间里离「扁平足」很近，
   但它们根本不是鞋。
   → 纯向量会召回一堆不是鞋的东西。

3. **数值陷阱**：「轻量」「500元以内」是数值约束。
   → 向量和 BM25 都处理不了，只能靠 query 理解翻译成 WHERE。

商品的**真实属性**放在 `_gold` 字段里，只给 qrels 用。
管线本身看不到 `_gold`——L0 必须自己从描述文本里抽属性，
所以描述写得含糊的商品，抽出来的属性天然就是缺失或错的。
这个「抽取噪声」是有意保留的：真实电商里 L0 的准确率远达不到 100%，
如果 bench 里 L0 是完美的，结构化召回就会赢得毫无意义。
"""

from __future__ import annotations

import json
import os
import random

SEED = 20260829
rng = random.Random(SEED)

HERE = os.path.dirname(os.path.abspath(__file__))

BRANDS = [
    ("昂跑云", 1.35), ("亚瑟龙", 1.25), ("索康妮尔", 1.20), ("布鲁克世", 1.15),
    ("新百轮", 1.05), ("美津农", 1.10), ("李宇", 0.80), ("安塔风", 0.75),
    ("特步云", 0.70), ("匹克光", 0.68), ("多威特", 0.60), ("回力星", 0.45),
]

SHOPS = [
    ("S01", "官方旗舰店"), ("S02", "海外旗舰店"), ("S03", "运动世家专营店"),
    ("S04", "跑者联盟专营店"), ("S05", "奥莱折扣店"), ("S06", "体育用品旗舰店"),
]

# ---------------------------------------------------------------------------
# 各支撑类型的商品文案零件
#
# 注意：稳定支撑类的文案里**没有「扁平足」**，全是商家的行话。
# 这正是「用户说的话」和「商家写的话」之间那道鸿沟。
# ---------------------------------------------------------------------------

COPY = {
    "稳定支撑": {
        "titles": ["稳定支撑跑鞋", "支撑系公路跑鞋", "稳定型长距离跑鞋", "支撑跑鞋"],
        "features": [
            "内侧 TPU 稳定片，抑制落地时的过度内旋",
            "双密度中底，内侧密度更高，提供足弓支撑",
            "抗内旋几何结构，改善步态轨迹",
            "加固后跟稳定器，锁定后跟不晃动",
            "足弓支撑结构，适合支撑需求较高的跑者",
        ],
        "scenes": ["日常有氧慢跑", "长距离拉练", "每周 30-60 公里的训练量"],
    },
    "缓震": {
        "titles": ["缓震跑鞋", "厚底缓震跑鞋", "日常训练跑鞋", "软弹跑鞋"],
        "features": [
            "超临界发泡中底，回弹柔软",
            "全掌厚弹中底，落地冲击更小",
            "高回弹缓震科技，适合大体重跑者",
            "厚底设计，堆叠高度 38mm",
            "全掌气垫，长时间站立也舒适",
        ],
        "scenes": ["日常慢跑", "入门跑者第一双", "通勤与轻运动"],
    },
    "竞速": {
        "titles": ["碳板竞速跑鞋", "马拉松竞速跑鞋", "全掌碳板跑鞋", "竞速训练鞋"],
        "features": [
            "全掌碳纤维板，推进感强烈",
            "竞速鞋楦，包裹紧致",
            "超轻薄网面鞋面，减重优先",
            "高回弹竞速中底，适合比赛配速",
            "为破三目标设计的几何结构",
        ],
        "scenes": ["半马与全马比赛", "间歇跑与节奏跑", "冲刺训练"],
    },
    "越野": {
        "titles": ["越野跑鞋", "山地越野跑鞋", "全地形越野鞋", "户外越野跑鞋"],
        "features": [
            "Vibram 深齿大底，湿滑岩面抓地可靠",
            "岩钉式外底，泥地防滑",
            "防泼水鞋面，涉水后排水快",
            "前掌岩石护板，保护足底",
            "深齿大底配合加固鞋头，应对碎石路面",
        ],
        "scenes": ["山地越野", "泥地与碎石路", "户外徒步跑"],
    },
}

WIDTH_COPY = {
    "4E": ["加宽鞋楦，宽楦设计给前掌更多空间", "宽楦版本，脚背高的跑者也不挤"],
    "2E": ["标准偏宽鞋楦"],
    "标准": ["标准鞋楦，常规脚型合脚"],
}

# ---------------------------------------------------------------------------
# 陷阱商品：描述里明写「扁平足」，但其实是错误答案
# ---------------------------------------------------------------------------

TRAPS = [
    {
        "product_name": "扁平足专用矫形鞋垫 足弓支撑垫",
        "category": "鞋垫",
        "description": "专为扁平足设计的矫形鞋垫，足弓支撑，缓解久站疲劳。"
                       "适合扁平足、低足弓人群日常使用。可放入任意跑鞋内。",
        "price": 89,
        "gold": {"support_type": None, "weight_grams": 60, "width": None,
                 "pronation_fit": None, "has_carbon_plate": False, "cushion_level": 0},
        "why": "词汇陷阱：满篇「扁平足」，但它是鞋垫不是鞋",
    },
    {
        "product_name": "足弓支撑运动袜 扁平足适用 两双装",
        "category": "运动袜",
        "description": "足弓压缩带设计，扁平足人群跑步时提供轻度支撑。"
                       "透气速干，适合跑步、健身。",
        "price": 39,
        "gold": {"support_type": None, "weight_grams": 30, "width": None,
                 "pronation_fit": None, "has_carbon_plate": False, "cushion_level": 0},
        "why": "词汇 + 语义双陷阱：既写了扁平足，embedding 上也离「足部」很近",
    },
    {
        "product_name": "顶级稳定支撑跑鞋 PRO MAX 扁平足跑者之选",
        "category": "跑步鞋",
        "description": "旗舰级稳定支撑跑鞋，内侧 TPU 稳定片配合双密度中底，"
                       "抑制过度内旋。扁平足跑者的长距离首选。单只重约 312g。",
        "price": 1680,
        "gold": {"support_type": "稳定支撑", "weight_grams": 312, "width": "标准",
                 "pronation_fit": "过度内旋", "has_carbon_plate": False, "cushion_level": 7},
        "why": "价格陷阱：属性全对，但 1680 元远超 500 预算，而且 312g 不轻",
    },
    {
        "product_name": "软弹厚底缓震跑鞋 扁平足也能穿",
        "category": "跑步鞋",
        "description": "超临界发泡中底，回弹柔软，落地冲击小。"
                       "营销宣称扁平足也能穿，实际为中性缓震鞋，无稳定结构。单只重约 268g。",
        "price": 399,
        "gold": {"support_type": "缓震", "weight_grams": 268, "width": "标准",
                 "pronation_fit": "中性", "has_carbon_plate": False, "cushion_level": 8},
        "why": "文案陷阱：写了扁平足，但它是中性缓震鞋，没有稳定结构",
    },
    {
        "product_name": "护踝 运动护具 足弓支撑",
        "category": "护具",
        "description": "跑步护踝，足弓与踝关节支撑，适合扁平足、崴脚恢复期使用。",
        "price": 59,
        "gold": {"support_type": None, "weight_grams": 45, "width": None,
                 "pronation_fit": None, "has_carbon_plate": False, "cushion_level": 0},
        "why": "语义陷阱：向量空间里离「足部支撑」很近，但不是鞋",
    },
]

OTHER_CATEGORIES = [
    ("篮球鞋", ["实战篮球鞋", "高帮篮球鞋", "缓震篮球鞋"],
     ["高帮设计保护脚踝", "前掌气垫，急停变向稳定", "耐磨外底，室内外场地通用"]),
    ("休闲鞋", ["复古休闲鞋", "百搭板鞋", "轻便休闲鞋"],
     ["复古配色，日常百搭", "轻便鞋底，久走不累", "皮革鞋面，好打理"]),
    ("训练鞋", ["综合训练鞋", "健身房训练鞋", "力量训练鞋"],
     ["宽平鞋底，深蹲硬拉更稳", "侧向支撑强化", "耐磨外底，适合器械与跳跃"]),
]


def _weight_for(support: str) -> int:
    lo, hi = {
        "竞速": (178, 235),
        "缓震": (245, 315),
        "稳定支撑": (258, 330),
        "越野": (275, 365),
    }[support]
    return rng.randint(lo, hi)


def _price_for(support: str, tier: float) -> int:
    base = {"竞速": 950, "缓震": 480, "稳定支撑": 620, "越野": 700}[support]
    p = base * tier * rng.uniform(0.55, 1.25)
    return int(round(p / 10) * 10)


def build_running_shoe(idx: int) -> dict:
    support = rng.choices(
        ["缓震", "稳定支撑", "竞速", "越野"], weights=[40, 26, 18, 16]
    )[0]
    brand, tier = rng.choice(BRANDS)
    shop_id, shop_name = rng.choice(SHOPS)
    c = COPY[support]

    width = rng.choices(["标准", "2E", "4E"], weights=[65, 20, 15])[0]
    weight = _weight_for(support)
    price = _price_for(support, tier)
    carbon = support == "竞速" and rng.random() < 0.8
    cushion = {"竞速": rng.randint(3, 6), "缓震": rng.randint(7, 10),
               "稳定支撑": rng.randint(5, 8), "越野": rng.randint(4, 7)}[support]
    pronation = {"稳定支撑": "过度内旋", "缓震": "中性",
                 "竞速": "中性", "越野": "中性"}[support]

    title = f"{brand} {rng.choice(c['titles'])} {rng.choice(['V3','V5','2代','Pro','Lite','GT','X'])}"

    parts = rng.sample(c["features"], k=rng.randint(2, 3))
    parts.append(rng.choice(c["scenes"]) + "适用")
    if width != "标准":
        parts.append(rng.choice(WIDTH_COPY[width]))

    # 只有 ~72% 的商品在文案里写了克重。剩下的 L0 抽不出 weight_grams，
    # 这是有意保留的抽取缺失——真实电商里比这更糟。
    states_weight = rng.random() < 0.72
    if states_weight:
        parts.append(f"单只重约 {weight}g")

    description = "。".join(parts) + "。"

    return {
        "id": idx,
        "product_name": title,
        "brand": brand,
        "category": "跑步鞋",
        "description": description,
        "price": price,
        "stock": rng.choices([0, rng.randint(1, 40), rng.randint(40, 500)],
                             weights=[8, 30, 62])[0],
        "shop_id": shop_id,
        "shop_name": f"{brand}{shop_name}",
        "rating": round(rng.uniform(4.0, 4.95), 2),
        "sales_30d": int(rng.lognormvariate(4.2, 1.3)),
        "image_url": f"https://example.invalid/img/{idx}.jpg",
        "_gold": {
            "support_type": support,
            "weight_grams": weight,
            "width": width,
            "pronation_fit": pronation,
            "has_carbon_plate": carbon,
            "cushion_level": cushion,
        },
    }


def build_other(idx: int) -> dict:
    cat, titles, feats = rng.choice(OTHER_CATEGORIES)
    brand, tier = rng.choice(BRANDS)
    shop_id, shop_name = rng.choice(SHOPS)
    return {
        "id": idx,
        "product_name": f"{brand} {rng.choice(titles)}",
        "brand": brand,
        "category": cat,
        "description": "。".join(rng.sample(feats, k=2)) + "。",
        "price": int(round(300 * tier * rng.uniform(0.5, 1.6) / 10) * 10),
        "stock": rng.choices([0, rng.randint(1, 300)], weights=[10, 90])[0],
        "shop_id": shop_id,
        "shop_name": f"{brand}{shop_name}",
        "rating": round(rng.uniform(3.9, 4.9), 2),
        "sales_30d": int(rng.lognormvariate(3.8, 1.3)),
        "image_url": f"https://example.invalid/img/{idx}.jpg",
        "_gold": {
            "support_type": None, "weight_grams": None, "width": None,
            "pronation_fit": None, "has_carbon_plate": False, "cushion_level": 0,
        },
    }


def build_traps(start_idx: int) -> list[dict]:
    out = []
    for i, t in enumerate(TRAPS):
        brand, _ = rng.choice(BRANDS)
        shop_id, shop_name = rng.choice(SHOPS)
        out.append({
            "id": start_idx + i,
            "product_name": t["product_name"],
            "brand": brand,
            "category": t["category"],
            "description": t["description"],
            "price": t["price"],
            "stock": rng.randint(20, 300),
            "shop_id": shop_id,
            "shop_name": f"{brand}{shop_name}",
            "rating": round(rng.uniform(4.2, 4.9), 2),
            "sales_30d": int(rng.lognormvariate(4.5, 1.0)),
            "image_url": f"https://example.invalid/img/{start_idx + i}.jpg",
            "_gold": t["gold"],
            "_trap": t["why"],
        })
    return out


# ---------------------------------------------------------------------------
# 人工相关性标注（qrels）
#
# 判据用的是商品的**真实属性** `_gold`，也就是「一个懂跑鞋的店员会怎么答」。
# 检索管线看不到 `_gold`，它只能看到文本、向量和 L0 自己抽出来的（有噪声的）属性。
#
# 分级：2 = 完全符合，1 = 基本符合但有明显短板，0 = 不相关
# ---------------------------------------------------------------------------

def _is_runnable(p: dict) -> bool:
    """跑鞋 + 有货。缺货商品排在前面是电商搜索最基础的错误之一。"""
    return p["category"] == "跑步鞋" and p["stock"] > 0


def q_flatfoot_light_500(p):
    g = p["_gold"]
    if not _is_runnable(p) or p["price"] > 500 or g["support_type"] != "稳定支撑":
        return 0
    return 2 if (g["weight_grams"] or 999) <= 285 else 1


def q_heavy_runner_cushion(p):
    g = p["_gold"]
    if not _is_runnable(p) or g["support_type"] != "缓震":
        return 0
    return 2 if g["cushion_level"] >= 8 else 1


def q_wide_foot(p):
    g = p["_gold"]
    if not _is_runnable(p):
        return 0
    return {"4E": 2, "2E": 1}.get(g["width"], 0)


def q_entry_under_300(p):
    g = p["_gold"]
    if not _is_runnable(p) or p["price"] > 300:
        return 0
    return 2 if g["support_type"] == "缓震" else 1


def q_marathon_carbon(p):
    g = p["_gold"]
    if not _is_runnable(p) or g["support_type"] != "竞速":
        return 0
    return 2 if g["has_carbon_plate"] else 1


def q_trail(p):
    g = p["_gold"]
    if not _is_runnable(p):
        return 0
    return 2 if g["support_type"] == "越野" else 0


def q_overpronation(p):
    g = p["_gold"]
    if not _is_runnable(p):
        return 0
    return 2 if g["support_type"] == "稳定支撑" else 0


def q_ultralight_summer(p):
    g = p["_gold"]
    if not _is_runnable(p):
        return 0
    w = g["weight_grams"] or 999
    if w <= 225:
        return 2
    return 1 if w <= 250 else 0


def q_low_arch_under_1000(p):
    g = p["_gold"]
    if not _is_runnable(p) or p["price"] > 1000:
        return 0
    return 2 if g["support_type"] == "稳定支撑" else 0


def q_cushion_500_800(p):
    g = p["_gold"]
    if not _is_runnable(p) or not (500 <= p["price"] <= 800):
        return 0
    return 2 if g["support_type"] == "缓震" else 0


QUERIES = [
    ("q1",  "适合扁平足的轻量跑步鞋，500元以内", q_flatfoot_light_500),
    ("q2",  "大体重跑者的厚底缓震跑鞋",           q_heavy_runner_cushion),
    ("q3",  "宽脚掌能穿的跑鞋",                   q_wide_foot),
    ("q4",  "300块以内的入门跑鞋",                q_entry_under_300),
    ("q5",  "马拉松比赛穿的碳板竞速鞋",           q_marathon_carbon),
    ("q6",  "越野跑鞋 防滑抓地",                  q_trail),
    ("q7",  "内旋过度 稳定系跑鞋",                q_overpronation),
    ("q8",  "超轻透气夏季跑鞋",                   q_ultralight_summer),
    ("q9",  "低足弓支撑跑鞋 1000元以内",          q_low_arch_under_1000),
    ("q10", "缓震跑鞋 500到800元",                q_cushion_500_800),
]


def main() -> None:
    n_shoes, n_other = 260, 55
    products = [build_running_shoe(i) for i in range(1, n_shoes + 1)]
    products += [build_other(i) for i in range(n_shoes + 1, n_shoes + n_other + 1)]
    products += build_traps(n_shoes + n_other + 1)

    qrels = {}
    for qid, text, rule in QUERIES:
        rels = {str(p["id"]): rule(p) for p in products}
        rels = {k: v for k, v in rels.items() if v > 0}
        qrels[qid] = {"query": text, "relevance": rels}

    with open(os.path.join(HERE, "products.json"), "w", encoding="utf-8") as f:
        json.dump(products, f, ensure_ascii=False, indent=1)
    with open(os.path.join(HERE, "qrels.json"), "w", encoding="utf-8") as f:
        json.dump(qrels, f, ensure_ascii=False, indent=1)

    print(f"products.json: {len(products)} 条"
          f"（跑鞋 {n_shoes} / 其他品类 {n_other} / 陷阱 {len(TRAPS)}）")
    print(f"qrels.json:    {len(qrels)} 个 query")
    print()
    print(f"{'qid':<5} {'相关数':>6} {'其中grade2':>10}  query")
    for qid, text, _ in QUERIES:
        r = qrels[qid]["relevance"]
        g2 = sum(1 for v in r.values() if v == 2)
        print(f"{qid:<5} {len(r):>6} {g2:>10}  {text}")

    # 陷阱自检：确认「描述里写了扁平足」的商品，在 q1 的标注里基本都是 0 分。
    print()
    print("陷阱自检 —— 描述含「扁平足」的商品在 q1 中的标注分：")
    for p in products:
        if "扁平足" in p["description"] or "扁平足" in p["product_name"]:
            score = qrels["q1"]["relevance"].get(str(p["id"]), 0)
            print(f"  id={p['id']:<4} q1标注={score}  {p['product_name'][:34]}")


if __name__ == "__main__":
    main()
