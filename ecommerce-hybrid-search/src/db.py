"""数据库连接 + 能力探测。

能力探测这件事值得解释一下：pg_search 的 DDL 在小版本之间变动过
（bm25 索引的 WITH 选项、分词器名字都改过）。与其让读者第一次运行就撞一堵墙，
不如在 ingest 时探测一次，把结果写进 capabilities，让整条管线自己适配：

    lexical = "bm25"    → pg_search 可用，走真 BM25（有 IDF）
    lexical = "tsrank"  → 降级到 PG 内置 tsvector + ts_rank_cd（没有 IDF，效果更差）

降级路径存在的意义不是「凑合能跑」，而是让 bench 能把两者的差距量出来——
这恰好就是「ts_rank 不是 BM25」这句话的实证。
"""

from __future__ import annotations

import contextlib
from dataclasses import dataclass

import psycopg

from .config import DB


@dataclass
class Capabilities:
    has_vector: bool
    has_pg_search: bool
    hnsw_iterative_scan: bool  # pgvector >= 0.8.0

    @property
    def lexical(self) -> str:
        return "bm25" if self.has_pg_search else "tsrank"


def connect() -> psycopg.Connection:
    return psycopg.connect(DB.conninfo())


@contextlib.contextmanager
def cursor(conn: psycopg.Connection | None = None):
    """拿一个 cursor。没传 conn 就自己开一个，用完关掉。"""
    own = conn is None
    conn = conn or connect()
    try:
        with conn.cursor() as cur:
            yield cur
        if own:
            conn.commit()
    finally:
        if own:
            conn.close()


def _extension_available(cur, name: str) -> bool:
    cur.execute("SELECT 1 FROM pg_available_extensions WHERE name = %s", (name,))
    return cur.fetchone() is not None


def detect_capabilities(conn: psycopg.Connection) -> Capabilities:
    with conn.cursor() as cur:
        has_vector = _extension_available(cur, "vector")
        has_pg_search = _extension_available(cur, "pg_search")

        # hnsw.iterative_scan 是 pgvector 0.8.0 引入的 GUC。
        # 它的存在与否，直接决定「带过滤的向量检索」会不会悄悄丢召回。
        iterative = False
        if has_vector:
            cur.execute("CREATE EXTENSION IF NOT EXISTS vector")
            cur.execute("SELECT 1 FROM pg_settings WHERE name = 'hnsw.iterative_scan'")
            iterative = cur.fetchone() is not None
    conn.commit()
    return Capabilities(
        has_vector=has_vector,
        has_pg_search=has_pg_search,
        hnsw_iterative_scan=iterative,
    )


def apply_session_tuning(conn: psycopg.Connection, caps: Capabilities) -> None:
    """每个检索会话都要设的参数。

    hnsw.iterative_scan 是这里最重要的一个。默认关闭时，带 WHERE 的 kNN 查询是
    **后过滤**：HNSW 先走出 ef_search 个候选，再把不满足过滤条件的行丢掉。
    过滤越严，返回的行数越少，甚至返回 0 行——而且不报错，只是悄悄地少。
    开成 relaxed_order 之后，pgvector 会在候选不够时继续往图里走，
    直到凑够 LIMIT 要的条数。
    """
    with conn.cursor() as cur:
        if caps.hnsw_iterative_scan:
            cur.execute("SET hnsw.iterative_scan = relaxed_order")
            # 单次查询最多扫多少个元组，防止极端过滤条件下退化成全表扫描
            cur.execute("SET hnsw.max_scan_tuples = 20000")
        # ef_search 越大召回越高、延迟越长。40 是 pgvector 默认值，
        # 电商这种「过滤重」的场景通常要往上调。
        cur.execute("SET hnsw.ef_search = 100")
    conn.commit()
