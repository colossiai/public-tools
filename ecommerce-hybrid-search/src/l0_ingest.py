"""L0：离线属性抽取 + 灌库 + 建索引。

    uv run python -m src.l0_ingest              # 规则抽取（默认，不需要 API key）
    uv run python -m src.l0_ingest --extract llm  # 用 Claude 抽取

这一层是整套架构里**投入产出比最高**的。它做的事情很朴素：
把商家写的营销文案，翻译成机器能过滤的类型化字段。

    「内侧 TPU 稳定片，抑制落地时的过度内旋」  →  support_type = '稳定支撑'
    「单只重约 245g」                          →  weight_grams = 245

翻译完成之后，「适合扁平足的轻量跑步鞋」这个查询里，
真正需要向量的部分就只剩下一点点了。

跑完会打印抽取准确率（对照 products.json 里的 `_gold`）。
准确率不会是 100%——文案没写克重、写得含糊的商品抽不出来。
这个噪声是有意保留的，否则结构化召回会赢得毫无意义。
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time

import psycopg

from . import ontology
from .config import DATA_DIR, MODELS, PROJECT_ROOT
from .db import connect, detect_capabilities
from .embedding import backend as embed_backend
from .embedding import embed, to_pgvector

# pg_search 各版本可用的中文分词器名字，按兼容性从高到低尝试。
TOKENIZER_CANDIDATES = ["chinese_compatible", "chinese_lindera", "jieba", "default"]


# ---------------------------------------------------------------------------
# SQL 文件执行
# ---------------------------------------------------------------------------

def split_sql(text: str) -> list[str]:
    """按分号切分语句，跳过单引号字符串和 -- 注释里的分号。"""
    stmts, buf = [], []
    in_str = in_comment = False
    i = 0
    while i < len(text):
        ch = text[i]
        if in_comment:
            if ch == "\n":
                in_comment = False
                buf.append(ch)
            i += 1
            continue
        if in_str:
            buf.append(ch)
            if ch == "'":
                if i + 1 < len(text) and text[i + 1] == "'":
                    buf.append(text[i + 1])
                    i += 2
                    continue
                in_str = False
            i += 1
            continue
        if ch == "-" and text[i : i + 2] == "--":
            in_comment = True
            i += 2
            continue
        if ch == "'":
            in_str = True
            buf.append(ch)
            i += 1
            continue
        if ch == ";":
            stmts.append("".join(buf).strip())
            buf = []
            i += 1
            continue
        buf.append(ch)
        i += 1
    tail = "".join(buf).strip()
    if tail:
        stmts.append(tail)
    return [s for s in stmts if s]


def execute_schema(conn: psycopg.Connection) -> str:
    """执行 sql/01_schema.sql，返回实际可用的词汇检索模式：bm25 | tsrank。

    pg_search 相关的两条语句允许失败——失败就降级，不中断。
    """
    path = os.path.join(PROJECT_ROOT, "sql", "01_schema.sql")
    with open(path, encoding="utf-8") as f:
        stmts = split_sql(f.read())

    conn.autocommit = True
    lexical = "tsrank"

    for stmt in stmts:
        head = " ".join(stmt.split())[:70]
        is_pg_search_ext = "EXTENSION IF NOT EXISTS pg_search" in stmt
        is_bm25_index = "USING bm25" in stmt

        if is_bm25_index:
            if lexical != "bm25":
                print("  [skip] BM25 索引：pg_search 不可用")
                continue
            if _create_bm25_index(conn, stmt):
                print("  [ok]   BM25 索引已建立（真 BM25，带 IDF）")
            else:
                print("  [warn] BM25 索引建立失败，降级到 tsvector + ts_rank_cd")
                lexical = "tsrank"
            continue

        try:
            with conn.cursor() as cur:
                cur.execute(stmt)
            if is_pg_search_ext:
                lexical = "bm25"
        except psycopg.Error as e:
            if is_pg_search_ext:
                print(f"  [warn] pg_search 不可用（{str(e).strip().splitlines()[0]}）")
                print("         → 词汇检索降级到 PG 内置 tsvector + ts_rank_cd。")
                print("         注意：ts_rank_cd 没有 IDF，不是 BM25，效果会明显更差。")
                print("         想要真 BM25 请用 ParadeDB 镜像（见 docker-compose.yml）。")
                continue
            print(f"  [FAIL] {head}\n         {e}")
            raise

    return lexical


def _create_bm25_index(conn: psycopg.Connection, stmt: str) -> bool:
    """依次尝试各个中文分词器名字，任一成功即返回 True。"""
    for tok in TOKENIZER_CANDIDATES:
        patched = re.sub(r'"type"\s*:\s*"[a-z_]+"', f'"type": "{tok}"', stmt)
        try:
            with conn.cursor() as cur:
                cur.execute(patched)
            if tok != TOKENIZER_CANDIDATES[0]:
                print(f"         （使用分词器 {tok}）")
            return True
        except psycopg.Error:
            with conn.cursor() as cur:
                cur.execute("DROP INDEX IF EXISTS products_bm25_idx")
            continue
    return False


# ---------------------------------------------------------------------------
# 属性抽取
# ---------------------------------------------------------------------------

WEIGHT_RE = re.compile(r"(?:重|重量|单只重)\D{0,4}(\d{2,3})\s*(?:g|克|G)")


def extract_rule_based(product: dict) -> dict:
    """规则抽取：领域词表 + 正则。

    生产里这一步应该用 LLM（见 extract_with_claude），规则版只是为了
    让读者没有 API key 也能跑通。但即使是规则版，它体现的思路是一样的：
    把非结构化文案变成类型化字段。
    """
    text = f"{product['product_name']} {product['description']}"

    attrs: dict = {
        "support_type": None,
        "weight_grams": None,
        "width": None,
        "pronation_fit": None,
        "has_carbon_plate": False,
        "cushion_level": None,
    }

    if product["category"] != "跑步鞋":
        return attrs

    hits = [term for term in ontology.DOC_TERM_TO_ATTRS if term in text]
    attrs.update(ontology.attrs_from_terms(hits, ontology.DOC_TERM_TO_ATTRS))

    m = WEIGHT_RE.search(text)
    if m:
        attrs["weight_grams"] = int(m.group(1))

    if attrs.get("width") is None:
        attrs["width"] = "标准"
    if attrs.get("pronation_fit") is None and attrs.get("support_type"):
        attrs["pronation_fit"] = (
            "过度内旋" if attrs["support_type"] == "稳定支撑" else "中性"
        )
    if attrs.get("cushion_level") is None and attrs.get("support_type"):
        attrs["cushion_level"] = {
            "缓震": 8, "稳定支撑": 6, "竞速": 4, "越野": 5,
        }[attrs["support_type"]]

    return attrs


EXTRACT_SCHEMA = {
    "type": "object",
    "properties": {
        "support_type": {"type": ["string", "null"], "enum": [*ontology.SUPPORT_TYPES, None]},
        "weight_grams": {"type": ["integer", "null"]},
        "width": {"type": ["string", "null"], "enum": [*ontology.WIDTHS, None]},
        "pronation_fit": {"type": ["string", "null"], "enum": [*ontology.PRONATION_TYPES, None]},
        "has_carbon_plate": {"type": "boolean"},
        "cushion_level": {"type": ["integer", "null"]},
    },
    "required": ["support_type", "weight_grams", "width",
                 "pronation_fit", "has_carbon_plate", "cushion_level"],
    "additionalProperties": False,
}

EXTRACT_SYSTEM = """你是跑鞋领域的商品属性抽取器。给你一条商品的标题和描述，抽出结构化属性。

重要规则：
- 只根据文案里**实际写了**的信息抽取。文案没提到的字段返回 null，不要猜。
- support_type 判据：
    稳定支撑 = 提到 TPU 稳定片 / 双密度中底 / 抗内旋 / 足弓支撑 / 支撑系
    竞速     = 提到碳板 / 竞速 / 比赛配速
    越野     = 提到深齿大底 / Vibram / 岩钉 / 山地
    缓震     = 提到超临界发泡 / 厚弹中底 / 气垫，且没有上面三类特征
- 注意区分**营销话术**和**实际结构**。一双中性缓震鞋在文案里写
  「扁平足也能穿」，它的 support_type 仍然是「缓震」，不是「稳定支撑」。
- 不是跑鞋的商品（鞋垫、袜子、护具、其他鞋类），所有字段返回 null。"""


def extract_with_claude(products: list[dict], batch_size: int = 20) -> list[dict]:
    """用 Claude 批量抽取属性。

    生产里这一步是离线批处理，应该走 Batch API（成本减半），
    并且只在商品新建或文案变更时跑增量。这里为了可读性用同步调用。
    """
    import anthropic

    client = anthropic.Anthropic()
    out: list[dict] = []

    for start in range(0, len(products), batch_size):
        chunk = products[start : start + batch_size]
        listing = "\n\n".join(
            f"[{i}] 标题：{p['product_name']}\n    品类：{p['category']}\n    描述：{p['description']}"
            for i, p in enumerate(chunk)
        )
        resp = client.messages.create(
            model=MODELS.claude_model,
            max_tokens=8000,
            system=EXTRACT_SYSTEM,
            messages=[{
                "role": "user",
                "content": f"抽取下面 {len(chunk)} 条商品的属性，"
                           f"按顺序返回一个 JSON 数组，每个元素对应一条商品：\n\n{listing}",
            }],
            output_config={"format": {
                "type": "json_schema",
                "schema": {"type": "array", "items": EXTRACT_SCHEMA},
            }},
        )
        text = "".join(b.text for b in resp.content if b.type == "text")
        parsed = json.loads(text)
        if len(parsed) != len(chunk):
            print(f"  [warn] 批次返回 {len(parsed)} 条，期望 {len(chunk)} 条，该批回退到规则抽取")
            parsed = [extract_rule_based(p) for p in chunk]
        out.extend(parsed)
        print(f"  已抽取 {min(start + batch_size, len(products))}/{len(products)}")

    return out


# ---------------------------------------------------------------------------
# 检索文本构造
# ---------------------------------------------------------------------------

def build_search_text(product: dict, attrs: dict) -> str:
    """词汇检索的输入。

    把 L0 抽出来的属性词也拼进去，是为了让 BM25 也能命中结构化信息——
    一个用户搜「稳定支撑」，即使商品文案里只写了「TPU 稳定片」，
    也能通过 support_type 这个词命中。这是一种很便宜的 term expansion。
    """
    parts = [product["product_name"], product["brand"] or "",
             product["category"], product["description"]]
    for key in ("support_type", "width", "pronation_fit"):
        if attrs.get(key):
            parts.append(str(attrs[key]))
    if attrs.get("has_carbon_plate"):
        parts.append("碳板")
    return " ".join(p for p in parts if p)


def segment(text: str) -> str:
    """jieba 分词，空格分隔。

    这样就能用 PG 内置的 'simple' 配置建 tsvector，
    绕开 zhparser / pg_jieba 的编译安装。降级路径用得上。
    """
    import jieba

    return " ".join(w for w in jieba.cut(text) if w.strip())


def build_embed_text(product: dict) -> str:
    """向量编码的输入。

    只喂标题 + 描述，**不喂**抽出来的属性词。属性已经有专门的结构化召回路
    去处理了，再塞进向量里会让 bench 高估向量路的贡献。
    """
    return f"{product['product_name']}。{product['description']}"


# ---------------------------------------------------------------------------
# 抽取质量报告
# ---------------------------------------------------------------------------

def report_extraction_quality(products: list[dict], extracted: list[dict]) -> None:
    shoes = [(p, a) for p, a in zip(products, extracted) if p["category"] == "跑步鞋"]
    if not shoes:
        return

    st_hit = sum(1 for p, a in shoes if a.get("support_type") == p["_gold"]["support_type"])
    w_present = [(p, a) for p, a in shoes if a.get("weight_grams") is not None]
    w_hit = sum(1 for p, a in w_present if a["weight_grams"] == p["_gold"]["weight_grams"])

    n = len(shoes)
    print()
    print("L0 抽取质量（对照 products.json 的 _gold，仅跑鞋）")
    print(f"  support_type 准确率 : {st_hit}/{n} = {st_hit / n:.1%}")
    print(f"  weight_grams 覆盖率 : {len(w_present)}/{n} = {len(w_present) / n:.1%}"
          f"   （抽到的里面准确率 {w_hit}/{len(w_present) or 1} = "
          f"{w_hit / (len(w_present) or 1):.1%}）")
    print("  ↑ 达不到 100% 是正常的，也是有意保留的：文案没写克重就是抽不出来。")
    print("    正因为 L0 会失败，词汇召回和向量召回这两路才必须存在。")


# ---------------------------------------------------------------------------
# 主流程
# ---------------------------------------------------------------------------

INSERT_SQL = """
INSERT INTO products (
    id, product_name, brand, category, description, price, stock,
    shop_id, shop_name, rating, sales_30d, image_url,
    support_type, weight_grams, width, pronation_fit, has_carbon_plate, cushion_level,
    search_text, seg_text, embedding
) VALUES (
    %(id)s, %(product_name)s, %(brand)s, %(category)s, %(description)s, %(price)s, %(stock)s,
    %(shop_id)s, %(shop_name)s, %(rating)s, %(sales_30d)s, %(image_url)s,
    %(support_type)s, %(weight_grams)s, %(width)s, %(pronation_fit)s,
    %(has_carbon_plate)s, %(cushion_level)s,
    %(search_text)s, %(seg_text)s, %(embedding)s::vector
)
"""


def main() -> int:
    ap = argparse.ArgumentParser(description="L0：属性抽取 + 灌库 + 建索引")
    ap.add_argument("--extract", choices=["rule", "llm"], default="rule",
                    help="属性抽取方式。llm 需要 ANTHROPIC_API_KEY")
    args = ap.parse_args()

    path = os.path.join(DATA_DIR, "products.json")
    if not os.path.exists(path):
        print(f"找不到 {path}，先运行：python3 data/gen_products.py", file=sys.stderr)
        return 1
    with open(path, encoding="utf-8") as f:
        products = json.load(f)
    print(f"读入 {len(products)} 条商品")

    conn = connect()
    caps = detect_capabilities(conn)
    print(f"\n数据库能力探测：pgvector={caps.has_vector} "
          f"pg_search={caps.has_pg_search} "
          f"hnsw.iterative_scan={caps.hnsw_iterative_scan}")
    if not caps.has_vector:
        print("pgvector 不可用，无法继续。", file=sys.stderr)
        return 1
    if not caps.hnsw_iterative_scan:
        print("  ⚠️  pgvector < 0.8.0：带过滤的向量召回是纯后过滤，"
              "过滤严的时候会静默丢结果。")

    print("\n建表与索引：")
    t0 = time.perf_counter()
    lexical = execute_schema(conn)
    print(f"  词汇检索模式：{lexical}"
          f"{'（真 BM25）' if lexical == 'bm25' else '（ts_rank_cd，无 IDF）'}")
    print(f"  耗时 {time.perf_counter() - t0:.1f}s")

    # ---- L0 抽取 ----
    print(f"\nL0 属性抽取（{args.extract}）：")
    t0 = time.perf_counter()
    if args.extract == "llm":
        if not MODELS.has_anthropic_key:
            print("  没有 ANTHROPIC_API_KEY，回退到规则抽取")
            extracted = [extract_rule_based(p) for p in products]
        else:
            extracted = extract_with_claude(products)
    else:
        extracted = [extract_rule_based(p) for p in products]
    print(f"  耗时 {time.perf_counter() - t0:.1f}s")

    report_extraction_quality(products, extracted)

    # ---- 向量 ----
    print(f"\n向量编码（后端 = {embed_backend()}）：")
    t0 = time.perf_counter()
    vectors = embed([build_embed_text(p) for p in products], is_query=False)
    print(f"  {len(vectors)} 条，耗时 {time.perf_counter() - t0:.1f}s")

    # ---- 灌库 ----
    print("\n写入数据库：")
    rows = []
    for p, attrs, vec in zip(products, extracted, vectors):
        search_text = build_search_text(p, attrs)
        rows.append({
            "id": p["id"], "product_name": p["product_name"], "brand": p["brand"],
            "category": p["category"], "description": p["description"],
            "price": p["price"], "stock": p["stock"],
            "shop_id": p["shop_id"], "shop_name": p["shop_name"],
            "rating": p["rating"], "sales_30d": p["sales_30d"],
            "image_url": p["image_url"],
            "support_type": attrs.get("support_type"),
            "weight_grams": attrs.get("weight_grams"),
            "width": attrs.get("width"),
            "pronation_fit": attrs.get("pronation_fit"),
            "has_carbon_plate": bool(attrs.get("has_carbon_plate")),
            "cushion_level": attrs.get("cushion_level"),
            "search_text": search_text,
            "seg_text": segment(search_text),
            "embedding": to_pgvector(vec),
        })

    conn.autocommit = False
    with conn.cursor() as cur:
        cur.executemany(INSERT_SQL, rows)
        cur.execute("ANALYZE products")
    conn.commit()

    with conn.cursor() as cur:
        cur.execute("SELECT count(*) FROM products")
        total = cur.fetchone()[0]
        cur.execute("SELECT count(*) FROM products WHERE stock > 0")
        in_stock = cur.fetchone()[0]
        cur.execute("SELECT count(*) FROM products WHERE support_type IS NOT NULL")
        with_attr = cur.fetchone()[0]

    print(f"  写入 {total} 条，其中有货 {in_stock} 条，抽到 support_type 的 {with_attr} 条")

    # 把探测结果落盘，后续检索不用再探一次
    with open(os.path.join(PROJECT_ROOT, ".cache_caps.json"), "w") as f:
        json.dump({"lexical": lexical,
                   "embedding_backend": embed_backend(),
                   "hnsw_iterative_scan": caps.hnsw_iterative_scan}, f)

    conn.close()
    print("\n完成。下一步：")
    print('  uv run python -m src.search "适合扁平足的轻量跑步鞋，500元以内"')
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
