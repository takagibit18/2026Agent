"""
嵌入模型后端：OpenAI API 与本地 BGE-M3（FlagEmbedding）。

未配置 API Key 或缺少 PyTorch/模型文件时，对应后端会跳过并在主程序中提示。
"""

from __future__ import annotations

import os
from abc import ABC, abstractmethod

import numpy as np


class Embedder(ABC):
    name: str

    @abstractmethod
    def embed(self, texts: list[str]) -> np.ndarray:
        """返回形状 (len(texts), dim) 的 float32/float64 矩阵。"""


class OpenAIEmbedder(Embedder):
    """使用 text-embedding-3-small（默认维度 1536）。"""

    def __init__(self, model: str = "text-embedding-3-small") -> None:
        from openai import OpenAI

        self._client = OpenAI()
        self._model = model
        self.name = f"OpenAI/{model}"

    def embed(self, texts: list[str]) -> np.ndarray:
        if not texts:
            return np.zeros((0, 0), dtype=np.float64)
        # 单次请求条数适中，避免体过大
        batch = 64
        chunks: list[list[float]] = []
        for i in range(0, len(texts), batch):
            part = texts[i : i + batch]
            resp = self._client.embeddings.create(model=self._model, input=part)
            for item in sorted(resp.data, key=lambda e: e.index):
                chunks.append(item.embedding)
        return np.asarray(chunks, dtype=np.float64)


class BGEM3Embedder(Embedder):
    """BAAI/bge-m3 稠密向量，维度一般为 1024。首次运行会从 HuggingFace 下载权重。"""

    def __init__(self, model_name: str = "BAAI/bge-m3") -> None:
        from FlagEmbedding import BGEM3FlagModel

        self._model = BGEM3FlagModel(model_name, use_fp16=False)
        self.name = f"BGE-M3/{model_name}"

    def embed(self, texts: list[str]) -> np.ndarray:
        if not texts:
            return np.zeros((0, 0), dtype=np.float64)
        out = self._model.encode(
            texts,
            batch_size=8,
            max_length=8192,
            return_dense=True,
            return_sparse=False,
            return_colbert_vecs=False,
        )
        dense = out["dense_vecs"]
        return np.asarray(dense, dtype=np.float64)


def try_openai() -> OpenAIEmbedder | None:
    if not os.getenv("OPENAI_API_KEY"):
        return None
    try:
        return OpenAIEmbedder()
    except Exception:
        return None


def try_bge_m3() -> BGEM3Embedder | None:
    try:
        return BGEM3Embedder()
    except Exception:
        return None
