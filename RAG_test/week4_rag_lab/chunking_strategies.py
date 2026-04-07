"""
三种分块策略定义，用于与同一套 Embedding / 检索参数做对照实验。

学习对齐: P0 · Week 4 · M1（分块策略对检索的影响）

策略说明（刻意区分「范式」而非仅调参）：
1. sentence_512：SentenceSplitter，按句子边界 + 固定字符窗口（512/50），接近常见默认。
2. token_256：TokenTextSplitter，按 tokenizer 词元切分（256/32），块更细、边界可能落在词中。
3. semantic：SemanticSplitterNodeParser，用语义相似度断点切分；默认 buffer / 百分位阈值见代码或环境变量 SEMANTIC_BUFFER_SIZE、SEMANTIC_BREAKPOINT_PCT。

环境变量（可选，覆盖默认值）：
- SEMANTIC_BUFFER_SIZE：默认 2
- SEMANTIC_BREAKPOINT_PCT：默认 80（越小通常切得越碎、节点越多）
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, List

from llama_index.core.embeddings import BaseEmbedding
from llama_index.core.node_parser import (
    SemanticSplitterNodeParser,
    SentenceSplitter,
    TokenTextSplitter,
)
from llama_index.core.schema import TransformComponent

TransformBuilder = Callable[[BaseEmbedding], List[TransformComponent]]

# 供对比脚本写入 JSON，确认加载的是哪一份源码
MODULE_PATH = Path(__file__).resolve()


def semantic_splitter_env_params() -> tuple[int, int]:
    """当前语义分块使用的 (buffer_size, breakpoint_percentile_threshold)。"""
    buf = int(os.getenv("SEMANTIC_BUFFER_SIZE", "1"))
    pct = int(os.getenv("SEMANTIC_BREAKPOINT_PCT", "50"))
    return buf, pct


@dataclass(frozen=True)
class ChunkStrategySpec:
    id: str
    title: str
    one_liner: str
    build_transformations: TransformBuilder


def _sentence_512(_: BaseEmbedding) -> List[TransformComponent]:
    return [
        SentenceSplitter(
            chunk_size=512,
            chunk_overlap=50,
            separator=" ",
        )
    ]


def _token_256(_: BaseEmbedding) -> List[TransformComponent]:
    return [
        TokenTextSplitter(
            chunk_size=256,
            chunk_overlap=32,
        )
    ]


def _semantic_90(embed_model: BaseEmbedding) -> List[TransformComponent]:
    buf, pct = semantic_splitter_env_params()
    return [
        SemanticSplitterNodeParser.from_defaults(
            embed_model=embed_model,
            buffer_size=buf,
            breakpoint_percentile_threshold=pct,
        )
    ]


CHUNK_STRATEGIES: List[ChunkStrategySpec] = [
    ChunkStrategySpec(
        id="sentence_512",
        title="SentenceSplitter 512/50",
        one_liner="句子边界 + 字符窗口；与常见默认接近。",
        build_transformations=_sentence_512,
    ),
    ChunkStrategySpec(
        id="token_256",
        title="TokenTextSplitter 256/32",
        one_liner="按 token 切分；块更小、检索命中更局部。",
        build_transformations=_token_256,
    ),
    ChunkStrategySpec(
        id="semantic_90",
        title="SemanticSplitter（语义断点）",
        one_liner="嵌入相似度断点；参数见 JSON 中 parser_runtime；可用 SEMANTIC_BUFFER_SIZE / SEMANTIC_BREAKPOINT_PCT 覆盖。",
        build_transformations=_semantic_90,
    ),
]


def get_strategy(strategy_id: str) -> ChunkStrategySpec:
    for s in CHUNK_STRATEGIES:
        if s.id == strategy_id:
            return s
    raise KeyError(f"未知策略: {strategy_id}；可选: {[x.id for x in CHUNK_STRATEGIES]}")
