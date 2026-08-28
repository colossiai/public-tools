"""向量后端：local（真模型） / hash（伪向量）。

hash 后端存在的唯一目的是让人零下载跑通管线。它做的是
**字符 n-gram 的哈希词袋 + L2 归一化**，也就是说它逼近的是「词汇相似」，
不是「语义相似」。用它跑 bench 会看到向量路和 BM25 路高度相关、
混合检索的增益接近于零——这不是架构的问题，是伪向量没有语义。
想看真实数字必须 `uv sync --extra local`。
"""

from __future__ import annotations

import hashlib
import threading

import numpy as np

from .config import EMBED_DIM, MODELS


def _l2(v: np.ndarray) -> np.ndarray:
    n = np.linalg.norm(v, axis=-1, keepdims=True)
    return v / np.maximum(n, 1e-12)


# ---------------------------------------------------------------------------
# hash 后端
# ---------------------------------------------------------------------------

def _char_ngrams(text: str, lo: int = 1, hi: int = 2) -> list[str]:
    text = "".join(ch for ch in text if not ch.isspace())
    out: list[str] = []
    for n in range(lo, hi + 1):
        out.extend(text[i : i + n] for i in range(len(text) - n + 1))
    return out


def _hash_embed_one(text: str) -> np.ndarray:
    v = np.zeros(EMBED_DIM, dtype=np.float32)
    for gram in _char_ngrams(text):
        h = hashlib.blake2b(gram.encode("utf-8"), digest_size=8).digest()
        idx = int.from_bytes(h[:4], "little") % EMBED_DIM
        sign = 1.0 if h[4] & 1 else -1.0  # 符号哈希，减少碰撞带来的偏置
        v[idx] += sign
    return v


# ---------------------------------------------------------------------------
# local 后端（sentence-transformers）
# ---------------------------------------------------------------------------

_local_model = None
_local_lock = threading.Lock()


def _load_local():
    global _local_model
    with _local_lock:
        if _local_model is None:
            from sentence_transformers import SentenceTransformer

            _local_model = SentenceTransformer(MODELS.embedding_model)
            dim = _local_model.get_sentence_embedding_dimension()
            if dim != EMBED_DIM:
                raise RuntimeError(
                    f"{MODELS.embedding_model} 是 {dim} 维，但 config.EMBED_DIM={EMBED_DIM}。"
                    f"改 EMBED_DIM 后需要重新 ingest（HNSW 索引带维度）。"
                )
    return _local_model


def resolve_backend() -> str:
    """auto 模式下决定实际用哪个后端。"""
    want = MODELS.embedding_backend
    if want in ("local", "hash"):
        return want
    try:
        import sentence_transformers  # noqa: F401

        return "local"
    except ImportError:
        return "hash"


_BACKEND: str | None = None


def backend() -> str:
    global _BACKEND
    if _BACKEND is None:
        _BACKEND = resolve_backend()
        if _BACKEND == "hash":
            print(
                "[embedding] 使用 hash 伪向量后端（无语义）。"
                "要真实检索质量请 `uv sync --extra local`。"
            )
    return _BACKEND


def embed(texts: list[str], *, is_query: bool = False) -> np.ndarray:
    """返回 (len(texts), EMBED_DIM) 的 L2 归一化矩阵。"""
    if not texts:
        return np.zeros((0, EMBED_DIM), dtype=np.float32)

    if backend() == "local":
        model = _load_local()
        # BGE 系列要求查询侧加指令前缀，文档侧不加。漏掉这一步会掉几个点。
        if is_query:
            texts = [f"为这个句子生成表示以用于检索相关文章：{t}" for t in texts]
        vecs = model.encode(texts, normalize_embeddings=True, show_progress_bar=False)
        return np.asarray(vecs, dtype=np.float32)

    return _l2(np.vstack([_hash_embed_one(t) for t in texts]))


def embed_one(text: str, *, is_query: bool = False) -> np.ndarray:
    return embed([text], is_query=is_query)[0]


def to_pgvector(v: np.ndarray) -> str:
    """psycopg 没装 pgvector 适配器时，用字符串字面量传向量。"""
    return "[" + ",".join(f"{x:.6f}" for x in v) + "]"
