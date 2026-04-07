"""
OpenAI 兼容网关（如 DashScope）上的模型名往往不在 LlamaIndex 内置列表中。

学习对齐: P0 · Week 4 · 贴近 M1（LlamaIndex + 国产 API）
"""

from __future__ import annotations

from typing import Any, Dict

from llama_index.core.base.llms.types import LLMMetadata
from llama_index.llms.openai import OpenAI
from llama_index.llms.openai.utils import (
    ALL_AVAILABLE_MODELS,
    is_function_calling_model,
    openai_modelname_to_contextsize,
)

# 仅用于通过 LlamaIndex 内部校验、tiktoken 与 to_openai_message_dicts；真实请求模型见 _api_model_name
_LLAMA_INDEX_PLACEHOLDER_LLM = "gpt-4o-mini"


class OpenAICompatCustomModel(OpenAI):
    """
    `model` 字段保留为 LlamaIndex 认识的占位名；发往 API 的 `model` 使用 `api_model`。
    """

    _api_model_name: str
    _context_window_override: int | None

    def __init__(
        self,
        *,
        api_model: str,
        context_window: int | None = None,
        **kwargs: Any,
    ) -> None:
        kwargs["model"] = _LLAMA_INDEX_PLACEHOLDER_LLM
        super().__init__(**kwargs)
        self._api_model_name = api_model
        self._context_window_override = context_window

    @property
    def metadata(self) -> LLMMetadata:
        md = super().metadata
        cw = (
            self._context_window_override
            if self._context_window_override is not None
            else openai_modelname_to_contextsize(_LLAMA_INDEX_PLACEHOLDER_LLM)
        )
        return LLMMetadata(
            context_window=cw,
            num_output=md.num_output,
            is_chat_model=md.is_chat_model,
            is_function_calling_model=is_function_calling_model(self._api_model_name),
            model_name=self._api_model_name,
            system_role=md.system_role,
        )

    def _get_model_kwargs(self, **kwargs: Any) -> Dict[str, Any]:
        out = super()._get_model_kwargs(**kwargs)
        out["model"] = self._api_model_name
        return out


def llm_needs_placeholder(model_name: str) -> bool:
    """模型名不在 LlamaIndex 维护的 ALL_AVAILABLE_MODELS 时需占位包装。"""
    return model_name not in ALL_AVAILABLE_MODELS
