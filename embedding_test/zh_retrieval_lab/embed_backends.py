"""
嵌入模型后端：通义千问向量（DashScope OpenAI 兼容接口）与本地 BGE-M3（FlagEmbedding）。

远程调用使用官方 `openai` 客户端 + `base_url` 指向 DashScope；模型名、Key、地域 URL 等由 `env_config` + `.env` 提供。

未配置 API Key 或缺少 PyTorch/模型文件时，对应后端会跳过并在主程序中提示。
"""

from __future__ import annotations

import sys
from abc import ABC, abstractmethod

import numpy as np

from zh_retrieval_lab.env_config import (
    bge_m3_model_id,
    bge_use_fp16,
    dashscope_api_key,
    dashscope_compat_base_url,
    load_lab_env,
    qwen_embedding_batch_size,
    qwen_embedding_dimensions,
    qwen_embedding_model,
)


class Embedder(ABC):
    name: str

    @abstractmethod
    def embed(self, texts: list[str]) -> np.ndarray:
        """返回形状 (len(texts), dim) 的 float32/float64 矩阵。"""


class QwenDashScopeEmbedder(Embedder):
    """
    通义千问文本向量：经 DashScope **compatible-mode/v1** 调用，与 OpenAI Embeddings API 同形。
    需在阿里云百炼 / DashScope 开通模型并配置 **DASHSCOPE_API_KEY**。
    """

    def __init__(
        self,
        *,
        model: str | None = None,
        base_url: str | None = None,
        api_key: str | None = None,
        dimensions: int | None = None,
    ) -> None:
        from openai import OpenAI

        key = (api_key or dashscope_api_key()).strip()
        if not key:
            raise ValueError("DASHSCOPE_API_KEY 为空")

        m = model or qwen_embedding_model()
        bu = base_url if base_url is not None else dashscope_compat_base_url()
        self._dimensions = dimensions if dimensions is not None else qwen_embedding_dimensions()
        self._client = OpenAI(api_key=key, base_url=bu)
        self._model = m
        self._batch_size = qwen_embedding_batch_size()
        self.name = f"Qwen/{m}"

    def embed(self, texts: list[str]) -> np.ndarray:
        from openai import AuthenticationError

        if not texts:
            return np.zeros((0, 0), dtype=np.float64)
        batch = self._batch_size
        chunks: list[list[float]] = []
        for i in range(0, len(texts), batch):
            part = texts[i : i + batch]
            kwargs: dict = {"model": self._model, "input": part}
            if self._dimensions is not None:
                kwargs["dimensions"] = self._dimensions
            try:
                resp = self._client.embeddings.create(**kwargs)
            except AuthenticationError:
                _print_dashscope_401_hint()
                raise
            for item in sorted(resp.data, key=lambda e: e.index):
                chunks.append(item.embedding)
        return np.asarray(chunks, dtype=np.float64)


def _print_dashscope_401_hint() -> None:
    print(
        "\nDashScope 返回 401（invalid_api_key）时请先核对：\n"
        "  1) Key 须为百炼 / 模型服务台的「API-KEY」，不是 AccessKey ID/Secret。\n"
        "  2) 加载顺序：先 embedding_test/.env，再 zh_retrieval_lab/.env；"
        "同名变量以 zh_retrieval_lab/.env 为准。\n"
        "     若只改了上级 .env，但子目录 .env 里仍有旧的 DASHSCOPE_API_KEY，会一直用上旧的。\n"
        "  3) DASHSCOPE_COMPAT_BASE_URL 与 Key 所属地域一致（北京 / 新加坡等见 .env.example）。\n"
        "  4) Key 两侧勿多复制空格；可用引号包裹，程序会去掉外层引号。\n"
        "  5) 修改 .env 后重新执行脚本。.env 由 Python 加载，PowerShell 里 echo $env:DASHSCOPE_API_KEY 常为空（属正常）；\n"
        "     是否在进程内读到 Key，可在 embedding_test 目录执行 README/TROUBLESHOOTING 中的 python -c 自检一行命令。\n",
        file=sys.stderr,
    )


class BGEM3Embedder(Embedder):
    """BGE-M3 稠密向量；模型 ID 默认来自 BGE_M3_MODEL。"""

    def __init__(
        self,
        model_name: str | None = None,
        *,
        use_fp16: bool | None = None,
    ) -> None:
        from FlagEmbedding import BGEM3FlagModel

        mid = model_name or bge_m3_model_id()
        fp16 = bge_use_fp16() if use_fp16 is None else use_fp16
        self._model = BGEM3FlagModel(mid, use_fp16=fp16)
        self.name = f"BGE-M3/{mid}"

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


def try_qwen_dashscope() -> QwenDashScopeEmbedder | None:
    load_lab_env()
    if not dashscope_api_key():
        return None
    try:
        return QwenDashScopeEmbedder()
    except Exception:
        return None


def try_bge_m3() -> BGEM3Embedder | None:
    load_lab_env()
    try:
        return BGEM3Embedder()
    except Exception:
        return None
