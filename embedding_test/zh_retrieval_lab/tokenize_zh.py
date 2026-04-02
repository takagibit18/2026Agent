"""中文分词：BM25 需要词序列，使用 jieba 做粗粒度切分。"""

from __future__ import annotations

import jieba


def tokenize(text: str) -> list[str]:
    return [t.strip() for t in jieba.cut(text, cut_all=False) if t.strip()]
