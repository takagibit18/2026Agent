"""
从 .env 加载 LLM / Embedding 所需配置。

加载顺序：先 `embedding_test/.env`，再 `RAG_test/week4_rag_lab/.env`（后者 override），
便于与 `zh_retrieval_lab` 共用 `DASHSCOPE_API_KEY`。
"""

from __future__ import annotations

import os
from pathlib import Path

_LAB_DIR = Path(__file__).resolve().parent
_EMBED_ROOT = _LAB_DIR.parent.parent / "embedding_test"
_ROOT_ENV = _EMBED_ROOT / ".env"
_LAB_ENV = _LAB_DIR / ".env"


def load_lab_env() -> None:
    from dotenv import load_dotenv

    if _ROOT_ENV.is_file():
        load_dotenv(_ROOT_ENV, override=True)
    if _LAB_ENV.is_file():
        load_dotenv(_LAB_ENV, override=True)
    if not _ROOT_ENV.is_file() and not _LAB_ENV.is_file():
        load_dotenv()


def _strip_quotes(value: str) -> str:
    v = value.strip()
    if len(v) >= 2 and v[0] == v[-1] and v[0] in "'\"":
        return v[1:-1].strip()
    return v


def api_key() -> str:
    """优先 OPENAI_API_KEY，否则 DASHSCOPE_API_KEY（与 zh_retrieval_lab 一致）。"""
    k = os.getenv("OPENAI_API_KEY", "").strip() or os.getenv("DASHSCOPE_API_KEY", "").strip()
    return _strip_quotes(k)


def api_base() -> str:
    v = os.getenv("OPENAI_BASE_URL", "").strip() or os.getenv("DASHSCOPE_COMPAT_BASE_URL", "").strip()
    return _strip_quotes(v) if v else "https://api.openai.com/v1"


def llm_model() -> str:
    v = os.getenv("LLM_MODEL", "").strip() or os.getenv("QWEN_LLM_MODEL", "").strip()
    if v:
        return v
    # 若走 DashScope 兼容且未单独设 LLM，给常见默认
    if "dashscope" in api_base().lower():
        return "qwen-turbo"
    return "gpt-4o-mini"


def embedding_model() -> str:
    v = os.getenv("EMBEDDING_MODEL", "").strip() or os.getenv("QWEN_EMBEDDING_MODEL", "").strip()
    if v:
        return v
    if "dashscope" in api_base().lower():
        return "text-embedding-v3"
    return "text-embedding-3-small"


def embedding_dimensions() -> int | None:
    v = os.getenv("EMBEDDING_DIMENSIONS", "").strip() or os.getenv("QWEN_EMBEDDING_DIMENSIONS", "").strip()
    if not v:
        return None
    try:
        return int(v)
    except ValueError:
        return None


def llm_context_window() -> int | None:
    """非 OpenAI 官方模型名（如 qwen-turbo）用于 metadata.context_window；不填则用占位模型默认窗口。"""
    v = os.getenv("LLM_CONTEXT_WINDOW", "").strip() or os.getenv("QWEN_LLM_CONTEXT_WINDOW", "").strip()
    if not v:
        return None
    try:
        return int(v)
    except ValueError:
        return None
