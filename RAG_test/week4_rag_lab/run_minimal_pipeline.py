"""
最小 RAG：Markdown + PDF → 分块（默认）→ 向量索引 → Query Engine 问答。

层级 A：在终端打印本次 query 检索到的 Chunk（相似度、来源、正文片段），便于对照生成答案与语料。
层级 B：通过 Callback 打印生成阶段实际发给 LLM 的 Chat messages；默认 QA 模板下将 USER 中的 Context / Query 拆开显示。
三种分块对照：见 compare_chunking_strategies.py；本脚本可通过环境变量 CHUNK_STRATEGY 切换策略。

学习对齐: P0 · Week 4 · 贴近 M1（LlamaIndex 全链路基线）
"""

from __future__ import annotations

import os
from pathlib import Path

from llama_index.core import Settings, VectorStoreIndex
from llama_index.core import SimpleDirectoryReader
from llama_index.core.callbacks import CallbackManager
from llama_index.core.response import Response
from llama_index.embeddings.openai import OpenAIEmbedding, OpenAIEmbeddingModelType
from llama_index.llms.openai import OpenAI
from llama_index.readers.file import PyMuPDFReader

from chunking_strategies import get_strategy
from compat_llm import OpenAICompatCustomModel, llm_needs_placeholder
from generation_prompt_debug import GenerationPromptCallbackHandler
from env_config import (
    api_base,
    api_key,
    embedding_dimensions,
    embedding_model,
    load_lab_env,
    llm_context_window,
    llm_model,
)

# LlamaIndex 仅枚举了部分 OpenAI 官方模型名；DashScope 的 text-embedding-v3/v4 等需走 model_name 覆盖。
_KNOWN_OPENAI_EMBEDDING_IDS = frozenset(m.value for m in OpenAIEmbeddingModelType)


def build_openai_embedding_kwargs(
    *,
    api_key: str,
    api_base: str,
    embed_batch_size: int | None,
) -> dict:
    """构造 OpenAIEmbedding 参数；非枚举内模型名使用占位 model + model_name。"""
    name = embedding_model()
    dim = embedding_dimensions()
    kw: dict = {
        "api_key": api_key,
        "api_base": api_base,
    }
    if name in _KNOWN_OPENAI_EMBEDDING_IDS:
        kw["model"] = name
    else:
        kw["model"] = OpenAIEmbeddingModelType.TEXT_EMBED_3_SMALL.value
        kw["model_name"] = name
    if dim is not None:
        kw["dimensions"] = dim
    if embed_batch_size is not None:
        kw["embed_batch_size"] = embed_batch_size
    return kw


def load_documents(data_dir: Path) -> list:
    docs: list = []
    md_files = sorted(data_dir.glob("*.md"))
    if md_files:
        docs.extend(SimpleDirectoryReader(input_files=[str(p) for p in md_files]).load_data())
    pdf_path = data_dir / "sample.pdf"
    if pdf_path.is_file():
        docs.extend(PyMuPDFReader().load(file_path=str(pdf_path)))
    if not docs:
        raise FileNotFoundError(
            f"未在 {data_dir} 找到 .md 或 sample.pdf；"
            "请先运行: python scripts/build_sample_pdf.py"
        )
    return docs


def print_retrieved_chunks(response: Response, *, max_chars: int = 800) -> None:
    """层级 A：打印 QueryEngine 从索引中取回的节点（不额外发起检索）。"""
    nodes = response.source_nodes
    print("\n--- 检索到的内容（层级 A）---")
    if not nodes:
        print("（无 source_nodes：请检查索引是否为空或检索是否被跳过。）")
        return
    for i, sn in enumerate(nodes, 1):
        score = sn.score
        n = sn.node
        meta = n.metadata or {}
        fname = meta.get("file_name") or meta.get("file_path") or ""
        page = meta.get("page_label")
        if page is None and "page_number" in meta:
            page = meta.get("page_number")
        body = n.get_content() or ""
        if len(body) > max_chars:
            preview = body[:max_chars].rstrip() + "\n    ... [已截断]"
        else:
            preview = body
        print(f"\n[{i}] score={score}")
        if fname:
            print(f"    source: {fname}")
        if page is not None:
            print(f"    page: {page}")
        for line in preview.splitlines():
            print(f"    {line}")


def main() -> None:
    load_lab_env()
    Settings.callback_manager = CallbackManager([GenerationPromptCallbackHandler()])
    key = api_key()
    if not key:
        raise SystemExit(
            "未配置 API Key：请设置 OPENAI_API_KEY 或 DASHSCOPE_API_KEY，"
            "并配置 OPENAI_BASE_URL / DASHSCOPE_COMPAT_BASE_URL（见 .env.example）。"
        )

    base = api_base()
    batch = 10 if "dashscope" in base.lower() else None
    emb_kwargs = build_openai_embedding_kwargs(api_key=key, api_base=base, embed_batch_size=batch)

    lm = llm_model()
    if llm_needs_placeholder(lm):
        Settings.llm = OpenAICompatCustomModel(
            api_model=lm,
            context_window=llm_context_window(),
            api_key=key,
            api_base=base,
        )
    else:
        Settings.llm = OpenAI(model=lm, api_key=key, api_base=base)
    Settings.embed_model = OpenAIEmbedding(**emb_kwargs)

    data_dir = Path(__file__).resolve().parent / "data"
    documents = load_documents(data_dir)
    print(f"已加载文档块数（加载器级）: {len(documents)}")

    chunk_id = os.getenv("CHUNK_STRATEGY", "").strip()
    index_kw: dict = {}
    if chunk_id:
        spec = get_strategy(chunk_id)
        index_kw["transformations"] = spec.build_transformations(Settings.embed_model)
        print(f"分块策略: {spec.id} — {spec.title}")
    index = VectorStoreIndex.from_documents(documents, **index_kw)
    engine = index.as_query_engine(similarity_top_k=3)

    query = "实验前的准备步骤有哪些?几句话简要概括"
    print("---")
    print("Query:", query)
    resp = engine.query(query)
    print("Answer:", str(resp))
    print_retrieved_chunks(resp)


if __name__ == "__main__":
    main()
