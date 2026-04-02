"""检索评价：MRR 与 Recall@k（面向单相关文档或多相关均可）。"""

from __future__ import annotations


def recall_at_k(ranked_ids: list[int], relevant: set[int], k: int) -> float:
    top = set(ranked_ids[:k])
    if not relevant:
        return 0.0
    return 1.0 if (top & relevant) else 0.0


def mrr(ranked_ids: list[int], relevant: set[int]) -> float:
    for i, did in enumerate(ranked_ids, start=1):
        if did in relevant:
            return 1.0 / i
    return 0.0
