"""集中管理所有后端开关。

设计原则：**任何一个可选依赖缺失，管线都要还能跑通**。
    - 没有 ANTHROPIC_API_KEY  → L1 走 jieba + 规则解析
    - 没有 sentence-transformers → 向量走 hash 伪向量，重排关掉
    - 没有 pg_search            → 词汇召回降级到 tsvector + ts_rank_cd
这样读者第一次 clone 下来一定能跑出结果，再按需要逐个升级成真东西。
"""

from __future__ import annotations

import os
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv()


def _env(key: str, default: str) -> str:
    v = os.environ.get(key)
    return default if v is None or v == "" else v


@dataclass(frozen=True)
class DBConfig:
    host: str = _env("PGHOST", "localhost")
    port: int = int(_env("PGPORT", "5433"))
    user: str = _env("PGUSER", "postgres")
    password: str = _env("PGPASSWORD", "postgres")
    dbname: str = _env("PGDATABASE", "ehs")

    def conninfo(self) -> str:
        return (
            f"host={self.host} port={self.port} user={self.user} "
            f"password={self.password} dbname={self.dbname}"
        )


@dataclass(frozen=True)
class ModelConfig:
    claude_model: str = _env("CLAUDE_MODEL", "claude-opus-5")
    l1_timeout: float = float(_env("L1_TIMEOUT_SECONDS", "1.5"))

    embedding_backend: str = _env("EMBEDDING_BACKEND", "auto")  # auto|local|hash
    embedding_model: str = _env("EMBEDDING_MODEL", "BAAI/bge-small-zh-v1.5")

    reranker_backend: str = _env("RERANKER_BACKEND", "auto")  # auto|local|claude|none
    reranker_model: str = _env("RERANKER_MODEL", "BAAI/bge-reranker-base")

    @property
    def has_anthropic_key(self) -> bool:
        return bool(os.environ.get("ANTHROPIC_API_KEY"))


DB = DBConfig()
MODELS = ModelConfig()

# 向量维度。BGE-small-zh-v1.5 是 512 维；hash 后端也用同一维度，
# 这样两种后端可以共用同一张表、同一个 HNSW 索引，切换后端只需重新灌一次库。
EMBED_DIM = 512

# RRF 的平滑常数。60 是 Cormack 等人 2009 年那篇论文里的取值，
# 后来被 Elasticsearch / OpenSearch 沿用为默认值。
RRF_K = 60

# 每一路召回各取多少条，进入融合。
RECALL_LIMIT = 100
# 融合后送进 cross-encoder 重排的条数。重排是 O(n) 次前向，这个数直接决定延迟。
RERANK_LIMIT = 50
# 最终返回条数。
TOP_K = 20

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(PROJECT_ROOT, "data")
CACHE_DIR = os.path.join(PROJECT_ROOT, ".cache")
