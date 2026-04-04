"""
从 .env 加载模型与远程嵌入（通义千问 / DashScope 兼容 OpenAI 协议）等配置。

加载顺序：**先** `embedding_test/.env`，**再** `zh_retrieval_lab/.env`（后者 `override=True`，同名变量以子目录为准）。
若两处都不存在，则回退为当前工作目录下的默认 `load_dotenv()`。
"""

from __future__ import annotations

import os
from pathlib import Path

_LAB_DIR = Path(__file__).resolve().parent
_ROOT_ENV = _LAB_DIR.parent / ".env"
_LAB_ENV = _LAB_DIR / ".env"


def load_lab_env() -> None:
    from dotenv import load_dotenv

    # override=True：避免「已存在于系统/终端里的旧 DASHSCOPE_API_KEY」导致改 .env 仍不生效
    if _ROOT_ENV.is_file():
        load_dotenv(_ROOT_ENV, override=True)
    if _LAB_ENV.is_file():
        load_dotenv(_LAB_ENV, override=True)
    if not _ROOT_ENV.is_file() and not _LAB_ENV.is_file():
        load_dotenv()


def _strip_optional_quotes(value: str) -> str:
    v = value.strip()
    if len(v) >= 2 and v[0] == v[-1] and v[0] in "'\"":
        return v[1:-1].strip()
    return v


def dashscope_api_key() -> str:
    return _strip_optional_quotes(os.getenv("DASHSCOPE_API_KEY", ""))


def qwen_embedding_model() -> str:
    v = os.getenv("QWEN_EMBEDDING_MODEL", "text-embedding-v3").strip()
    return v or "text-embedding-v3"


def dashscope_compat_base_url() -> str:
    """DashScope OpenAI 兼容模式根 URL（北京默认；国际版见 .env.example）。"""
    v = os.getenv("DASHSCOPE_COMPAT_BASE_URL", "").strip()
    return v or "https://dashscope.aliyuncs.com/compatible-mode/v1"


def qwen_embedding_dimensions() -> int | None:
    """可选；不设置则由接口默认（如 text-embedding-v3 常见为 1024）。"""
    v = os.getenv("QWEN_EMBEDDING_DIMENSIONS", "").strip()
    if not v:
        return None
    try:
        return int(v)
    except ValueError:
        return None


def qwen_embedding_batch_size() -> int:
    """
    单次 embeddings 请求的 `input` 条数上限。
    DashScope 兼容接口对 text-embedding 等模型通常要求 **≤10**（否则会 400 InvalidParameter）。
    """
    v = os.getenv("QWEN_EMBEDDING_BATCH_SIZE", "10").strip()
    try:
        n = int(v)
    except ValueError:
        n = 10
    return max(1, min(n, 10))


def bge_m3_model_id() -> str:
    v = os.getenv("BGE_M3_MODEL", "BAAI/bge-m3").strip()
    return v or "BAAI/bge-m3"


def bge_use_fp16() -> bool:
    return os.getenv("BGE_USE_FP16", "false").strip().lower() in ("1", "true", "yes", "on")
