"""
BM25（rank_bm25）与稠密向量分数的混合检索。

两种常见做法（入门建议先理解「加权」再了解 RRF）：
1. 加权融合：对 BM25 与余弦相似度分别做 min-max 归一化后线性组合。
2. RRF（Reciprocal Rank Fusion）：只看两个排序列表的名次，对 1/(k+rank) 求和，对排序偏移不敏感。
"""

from __future__ import annotations

from collections import defaultdict

import numpy as np
from rank_bm25 import BM25Okapi


def build_bm25(tokenized_corpus: list[list[str]]) -> BM25Okapi:
    return BM25Okapi(tokenized_corpus)


def bm25_scores(bm25: BM25Okapi, query_tokens: list[str]) -> np.ndarray:
    return np.asarray(bm25.get_scores(query_tokens), dtype=np.float64)


def dense_scores(query_vec: np.ndarray, doc_matrix: np.ndarray) -> np.ndarray:
    """doc_matrix: (n_docs, dim)，返回与每篇文档的余弦相似度。"""
    q = query_vec.astype(np.float64)
    d = doc_matrix.astype(np.float64)
    qn = q / (np.linalg.norm(q) + 1e-12)
    dn = d / (np.linalg.norm(d, axis=1, keepdims=True) + 1e-12)
    return dn @ qn


def minmax(x: np.ndarray) -> np.ndarray:
    lo, hi = float(x.min()), float(x.max())
    if hi - lo < 1e-12:
        return np.zeros_like(x)
    return (x - lo) / (hi - lo)


def hybrid_weighted(bm25_s: np.ndarray, dense_s: np.ndarray, alpha: float) -> np.ndarray:
    """
    alpha 越大越偏向向量；混合分数 = alpha * norm(dense) + (1-alpha) * norm(bm25)。
    """
    a = float(np.clip(alpha, 0.0, 1.0))
    return a * minmax(dense_s) + (1.0 - a) * minmax(bm25_s)


def rank_from_scores(scores: np.ndarray, *, higher_is_better: bool = True) -> list[int]:
    order = np.argsort(scores)
    if higher_is_better:
        order = order[::-1]
    return order.tolist()


def rrf_fuse(rank_lists: list[list[int]], k: int = 60) -> list[int]:
    """多个「文档 id 排序列表」做 RRF，返回融合后的文档 id 列表（分高在前）。"""
    scores: dict[int, float] = defaultdict(float)
    for rlist in rank_lists:
        for rank, did in enumerate(rlist, start=1):
            scores[did] += 1.0 / (k + rank)
    return sorted(scores.keys(), key=lambda d: scores[d], reverse=True)


def rrf_from_two_ranks(bm25_rank: list[int], dense_rank: list[int], k: int = 60) -> list[int]:
    return rrf_fuse([dense_rank, bm25_rank], k=k)
