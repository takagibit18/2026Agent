"""
打印 LlamaIndex 在「生成阶段」实际发给 LLM 的提示（Chat messages 或 completion prompt）。

学习对齐: P0 · Week 4 · 贴近 M1（可观测：检索 → 提示词 → 生成）
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, cast

from llama_index.core.base.llms.types import ChatMessage
from llama_index.core.callbacks.base_handler import BaseCallbackHandler
from llama_index.core.callbacks.schema import CBEventType, EventPayload


@dataclass(frozen=True)
class ParsedUserQA:
    """默认 CHAT_TEXT_QA 模板下，从 USER 消息中拆出的 context / query。"""

    context_block: str
    query_line: str


def try_parse_default_chat_qa_user(user_text: str) -> Optional[ParsedUserQA]:
    """
    匹配 LlamaIndex `CHAT_TEXT_QA_PROMPT` / `CHAT_TREE_SUMMARIZE_PROMPT` 常见形态，
    将「检索到的 context_str」与「Query: …」拆开便于阅读；不匹配则返回 None。
    """
    t = user_text.strip()
    # 默认 text QA（context_str 可含多行，故用第二道 --- 作为结束锚）
    m = re.search(
        r"Context information is below\.\s*\n-{3,}\s*\n"
        r"(.*)"
        r"\n-{3,}\s*\nGiven the context information and not prior knowledge,\s*\n"
        r"answer the query\.\s*\n"
        r"Query:\s*(.*?)\s*\n\s*Answer:\s*",
        t,
        flags=re.DOTALL | re.IGNORECASE,
    )
    if m:
        return ParsedUserQA(context_block=m.group(1).strip(), query_line=m.group(2).strip())
    # Tree summarize 变体
    m2 = re.search(
        r"Context information from multiple sources is below\.\s*\n-{3,}\s*\n"
        r"(.*)"
        r"\n-{3,}\s*\nGiven the information from multiple sources and not prior knowledge,\s*\n"
        r"answer the query\.\s*\n"
        r"Query:\s*(.*?)\s*\n\s*Answer:\s*",
        t,
        flags=re.DOTALL | re.IGNORECASE,
    )
    if m2:
        return ParsedUserQA(context_block=m2.group(1).strip(), query_line=m2.group(2).strip())
    return None


class GenerationPromptCallbackHandler(BaseCallbackHandler):
    """在 CBEventType.LLM 结束时打印输入侧提示词（不打印模型回复，避免与 Answer 重复）。"""

    def __init__(self) -> None:
        super().__init__(event_starts_to_ignore=[], event_ends_to_ignore=[])

    def on_event_start(
        self,
        event_type: CBEventType,
        payload: Optional[Dict[str, Any]] = None,
        event_id: str = "",
        parent_id: str = "",
        **kwargs: Any,
    ) -> str:
        return event_id

    def on_event_end(
        self,
        event_type: CBEventType,
        payload: Optional[Dict[str, Any]] = None,
        event_id: str = "",
        **kwargs: Any,
    ) -> None:
        if event_type != CBEventType.LLM or not payload:
            return
        print("\n--- 生成阶段：发给 LLM 的结构化提示 ---", flush=True)
        if EventPayload.MESSAGES in payload:
            messages = cast(List[ChatMessage], payload.get(EventPayload.MESSAGES, []))
            self._print_messages(messages)
            return
        if EventPayload.PROMPT in payload:
            prompt = str(payload.get(EventPayload.PROMPT, ""))
            print("[completion 模式 · 单段 prompt]", flush=True)
            print(prompt, flush=True)
            return
        print("（本帧 LLM 事件无 MESSAGES / PROMPT 字段，可能为内部实现差异。）", flush=True)

    def _print_messages(self, messages: List[ChatMessage]) -> None:
        for i, msg in enumerate(messages, 1):
            role = getattr(msg, "role", None)
            role_s = getattr(role, "value", None) or str(role)
            text = (msg.content or "").strip()
            print(f"\n[{i}] role={role_s.upper()}", flush=True)
            if role_s.lower() == "user" and text:
                parsed = try_parse_default_chat_qa_user(text)
                if parsed:
                    print("    ### Context（检索文本拼接，对应模板中的 {context_str}）", flush=True)
                    for line in parsed.context_block.splitlines():
                        print(f"    {line}", flush=True)
                    print("    ### Query（用户问题，对应模板中的 {query_str}）", flush=True)
                    print(f"    {parsed.query_line}", flush=True)
                    continue
            for line in text.splitlines():
                print(f"    {line}", flush=True)

    def start_trace(self, trace_id: Optional[str] = None) -> None:
        return

    def end_trace(
        self,
        trace_id: Optional[str] = None,
        trace_map: Optional[Dict[str, List[str]]] = None,
    ) -> None:
        return
