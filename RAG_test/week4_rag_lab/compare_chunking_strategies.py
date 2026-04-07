"""
对三种分块策略构建索引，用同一 Query 做向量检索，记录检索侧指标并落盘 JSON。

不调用 LLM 生成答案，节省费用；与 run_minimal_pipeline 共用加载与 Embedding 配置。

学习对齐: P0 · Week 4 · M1（分块对比 + 检索质量记录）
"""

from __future__ import annotations

import argparse
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from llama_index.core import Settings, VectorStoreIndex
from llama_index.core.callbacks import CallbackManager
from llama_index.embeddings.openai import OpenAIEmbedding
from llama_index.llms.openai import OpenAI

from chunking_strategies import (
    CHUNK_STRATEGIES,
    ChunkStrategySpec,
    MODULE_PATH,
    semantic_splitter_env_params,
)
from compat_llm import OpenAICompatCustomModel, llm_needs_placeholder
from env_config import (
    api_base,
    api_key,
    embedding_dimensions,
    embedding_model,
    load_lab_env,
    llm_context_window,
    llm_model,
)

# 与 run_minimal_pipeline 一致，避免重复维护两套嵌入逻辑
from run_minimal_pipeline import build_openai_embedding_kwargs, load_documents


def _parser_runtime_snapshot(transformations: list) -> dict[str, Any] | None:
    """把实际用于建索引的第一个 Transform 的关键参数写入 JSON，避免「改了代码却看不出」。"""
    if not transformations:
        return None
    t0 = transformations[0]
    name = t0.class_name() if hasattr(t0, "class_name") else type(t0).__name__
    snap: dict[str, Any] = {"class_name": name}
    for key in (
        "chunk_size",
        "chunk_overlap",
        "buffer_size",
        "breakpoint_percentile_threshold",
        "separator",
    ):
        if hasattr(t0, key):
            val = getattr(t0, key)
            if callable(val) and key == "separator":
                continue
            snap[key] = val
    return snap


def _chinese_bigrams(text: str) -> list[str]:
    """从查询串抽取连续汉字 bigram，用作粗粒度「查询词是否出现在召回里」的覆盖度。"""
    chars = "".join(re.findall(r"[\u4e00-\u9fff]+", text))
    if len(chars) < 2:
        return []
    return [chars[i : i + 2] for i in range(len(chars) - 1)]


def retrieval_metrics(
    *,
    query: str,
    scores: list[float | None],
    retrieved_texts: list[str],
) -> dict[str, Any]:
    valid_scores = [float(s) for s in scores if s is not None]
    blob = "\n".join(retrieved_texts)
    bigrams = _chinese_bigrams(query)
    if bigrams:
        hits = sum(1 for bg in bigrams if bg in blob)
        bigram_coverage = hits / len(bigrams)
    else:
        bigram_coverage = None

    return {
        "num_valid_scores": len(valid_scores),
        "mean_score": sum(valid_scores) / len(valid_scores) if valid_scores else None,
        "min_score": min(valid_scores) if valid_scores else None,
        "max_score": max(valid_scores) if valid_scores else None,
        "total_retrieved_chars": sum(len(t) for t in retrieved_texts),
        "query_bigram_coverage": bigram_coverage,
        "query_bigram_count": len(bigrams),
    }


def run_one_strategy(
    *,
    spec: ChunkStrategySpec,
    documents: list,
    embed_model: OpenAIEmbedding,
    query: str,
    top_k: int,
) -> dict[str, Any]:
    transformations = spec.build_transformations(embed_model)
    runtime = _parser_runtime_snapshot(list(transformations))
    index = VectorStoreIndex.from_documents(
        documents,
        transformations=transformations,
        embed_model=embed_model,
        show_progress=False,
    )
    n_nodes = len(index.index_struct.nodes_dict)
    retriever = index.as_retriever(similarity_top_k=top_k)
    nodes = retriever.retrieve(query)
    scores = [getattr(n, "score", None) for n in nodes]
    texts = [n.node.get_content() or "" for n in nodes]
    metrics = retrieval_metrics(query=query, scores=scores, retrieved_texts=texts)
    return {
        "strategy_id": spec.id,
        "strategy_title": spec.title,
        "strategy_note": spec.one_liner,
        "parser_runtime": runtime,
        "indexed_node_count": n_nodes,
        "top_k": top_k,
        "raw_scores": [float(s) if s is not None else None for s in scores],
        "retrieval_metrics": metrics,
        "retrieved_previews": [t[:240] + ("…" if len(t) > 240 else "") for t in texts],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="对比三种分块策略的向量检索指标")
    parser.add_argument(
        "--query",
        default="实验前的准备步骤有哪些?几句话简要概括",
        help="用于检索对比的查询句（与最小 Pipeline 默认一致）",
    )
    parser.add_argument("--top-k", type=int, default=3, help="向量检索 top-k")
    parser.add_argument(
        "--out",
        type=Path,
        default=None,
        help="JSON 输出路径，默认写入 week4_rag_lab/output/chunking_compare_latest.json",
    )
    args = parser.parse_args()

    load_lab_env()
    buf, pct = semantic_splitter_env_params()
    print(f"chunking_strategies 加载自: {MODULE_PATH}", flush=True)
    print(f"语义分块环境参数: SEMANTIC_BUFFER_SIZE={buf}, SEMANTIC_BREAKPOINT_PCT={pct}", flush=True)
    Settings.callback_manager = CallbackManager([])

    key = api_key()
    if not key:
        raise SystemExit("未配置 API Key（OPENAI_API_KEY 或 DASHSCOPE_API_KEY）。")

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
    embed_model = Settings.embed_model

    data_dir = Path(__file__).resolve().parent / "data"
    documents = load_documents(data_dir)
    print(f"已加载文档（加载器级）: {len(documents)} 份")

    embedding_meta = {
        "embedding_model": embedding_model(),
        "embedding_dimensions": embedding_dimensions(),
        "api_base_host": base.split("//")[-1].split("/")[0] if base else "",
    }

    results: list[dict[str, Any]] = []
    for spec in CHUNK_STRATEGIES:
        print(f"\n>>> 构建索引 + 检索: {spec.id} — {spec.title}")
        row = run_one_strategy(
            spec=spec,
            documents=documents,
            embed_model=embed_model,
            query=args.query,
            top_k=args.top_k,
        )
        results.append(row)
        m = row["retrieval_metrics"]
        print(
            f"    索引节点数={row['indexed_node_count']} | "
            f"mean_score={m['mean_score']!s} | "
            f"top_k 总字数={m['total_retrieved_chars']} | "
            f"查询 bigram 覆盖率={m['query_bigram_coverage']!s}"
        )

    out_dir = Path(__file__).resolve().parent / "output"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = args.out or (out_dir / "chunking_compare_latest.json")
    payload = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "chunking_strategies_py": str(MODULE_PATH),
        "semantic_env": {
            "SEMANTIC_BUFFER_SIZE": buf,
            "SEMANTIC_BREAKPOINT_PCT": pct,
        },
        "query": args.query,
        "top_k": args.top_k,
        "embedding": embedding_meta,
        "strategies": results,
        "metrics_note": (
            "mean_score 等为向量相似度统计；越高通常表示与查询向量越近，但不等于答案正确。"
            "query_bigram_coverage 为查询汉字 bigram 在 top-k 拼接正文中的命中率，仅作粗对照。"
        ),
    }
    out_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n已写入: {out_path.resolve()}")


if __name__ == "__main__":
    main()
