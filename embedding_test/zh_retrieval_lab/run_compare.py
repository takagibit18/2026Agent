"""
运行中文检索对比：纯稠密、纯 BM25、加权混合、RRF 混合。

完整说明（结构、指标、工程意义）见同目录 README.md。

用法（在 embedding_test 目录）：
  pip install -r requirements.txt
  # 可选：PowerShell: $env:OPENAI_API_KEY="sk-..."
  python -m zh_retrieval_lab.run_compare

结果会打印到终端，并写入 zh_retrieval_lab/results_last_run.txt。
"""

from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass
from pathlib import Path

import numpy as np

from zh_retrieval_lab.corpus import DOCS, QUERIES
from zh_retrieval_lab.embed_backends import try_bge_m3, try_openai
from zh_retrieval_lab.hybrid import (
    bm25_scores,
    build_bm25,
    dense_scores,
    hybrid_weighted,
    rank_from_scores,
    rrf_from_two_ranks,
)
from zh_retrieval_lab.metrics import mrr, recall_at_k
from zh_retrieval_lab.tokenize_zh import tokenize


@dataclass
class MethodAgg:
    name: str
    mrr: float
    r3: float
    r5: float


def evaluate_ranks(
    ranked_lists: list[list[int]],
    relevant: set[int],
    ks: tuple[int, ...] = (3, 5),
) -> tuple[float, dict[int, float]]:
    m = mrr(ranked_lists[0], relevant)
    rk: dict[int, float] = {k: recall_at_k(ranked_lists[0], relevant, k) for k in ks}
    return m, rk


def run_one_system(
    name: str,
    doc_matrix: np.ndarray,
    query_matrix: np.ndarray,
    bm25,
    tokenized_corpus: list[list[str]],
    alpha: float,
) -> list[MethodAgg]:
    n_docs = len(DOCS)
    assert doc_matrix.shape[0] == n_docs

    methods: dict[str, list[float]] = {
        "dense_only": [],
        "bm25_only": [],
        f"hybrid_weighted_a{alpha:.2f}": [],
        "hybrid_rrf": [],
    }
    recalls3: dict[str, list[float]] = {k: [] for k in methods}
    recalls5: dict[str, list[float]] = {k: [] for k in methods}

    for qi, q in enumerate(QUERIES):
        q_tokens = tokenize(q.text)
        bm25_s = bm25_scores(bm25, q_tokens)
        dense_s = dense_scores(query_matrix[qi], doc_matrix)

        dense_rank = rank_from_scores(dense_s)
        bm25_rank = rank_from_scores(bm25_s)
        hybrid_s = hybrid_weighted(bm25_s, dense_s, alpha)
        hybrid_w_rank = rank_from_scores(hybrid_s)
        hybrid_rrf_rank = rrf_from_two_ranks(bm25_rank, dense_rank)

        rel = set(q.relevant_doc_ids)
        for key, rlist in (
            ("dense_only", dense_rank),
            ("bm25_only", bm25_rank),
            (f"hybrid_weighted_a{alpha:.2f}", hybrid_w_rank),
            ("hybrid_rrf", hybrid_rrf_rank),
        ):
            methods[key].append(mrr(rlist, rel))
            recalls3[key].append(recall_at_k(rlist, rel, 3))
            recalls5[key].append(recall_at_k(rlist, rel, 5))

    out: list[MethodAgg] = []
    for key in methods:
        out.append(
            MethodAgg(
                name=f"{name} | {key}",
                mrr=float(np.mean(methods[key])),
                r3=float(np.mean(recalls3[key])),
                r5=float(np.mean(recalls5[key])),
            )
        )
    return out


def format_table(rows: list[MethodAgg]) -> str:
    header = f"{'方法':<52} {'MRR':>8} {'R@3':>8} {'R@5':>8}"
    lines = [header, "-" * len(header)]
    for r in rows:
        lines.append(f"{r.name:<52} {r.mrr:8.4f} {r.r3:8.4f} {r.r5:8.4f}")
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description="中文检索：OpenAI vs BGE-M3 + BM25 混合")
    parser.add_argument(
        "--alpha",
        type=float,
        default=0.65,
        help="加权混合中向量权重（越大越信向量）",
    )
    args = parser.parse_args()

    tokenized_corpus = [tokenize(d.text) for d in DOCS]
    bm25 = build_bm25(tokenized_corpus)

    embedders: list = []
    oa = try_openai()
    if oa:
        embedders.append(oa)
    else:
        print("提示：未设置 OPENAI_API_KEY 或 OpenAI 初始化失败，跳过 OpenAI 嵌入。", file=sys.stderr)

    bge = try_bge_m3()
    if bge:
        embedders.append(bge)
    else:
        print(
            "提示：BGE-M3 未就绪（需安装 torch、FlagEmbedding，且能下载 BAAI/bge-m3）。跳过 BGE-M3。",
            file=sys.stderr,
        )

    if not embedders:
        print("错误：没有可用的嵌入后端。请至少配置 OpenAI 或安装 BGE-M3 依赖。", file=sys.stderr)
        sys.exit(2)

    all_rows: list[MethodAgg] = []
    print("\n正在编码文档与查询（首次跑 BGE 会下载模型，请耐心等待）…\n")
    for emb in embedders:
        doc_texts = [d.text for d in DOCS]
        q_texts = [q.text for q in QUERIES]
        doc_mat = emb.embed(doc_texts)
        q_mat = emb.embed(q_texts)
        rows = run_one_system(emb.name, doc_mat, q_mat, bm25, tokenized_corpus, args.alpha)
        all_rows.extend(rows)

    text = format_table(all_rows)
    print(text)

    out_path = Path(__file__).resolve().parent / "results_last_run.txt"
    banner = (
        "中文检索对比（内置小语料）\n"
        f"文档数={len(DOCS)} 查询数={len(QUERIES)} 向量混合 alpha={args.alpha}\n"
        "说明：MRR 越高越好；R@k 表示前 k 条里是否命中任一条相关文档（本语料每查询 1 条相关）。\n\n"
    )
    out_path.write_text(banner + text + "\n", encoding="utf-8")
    print(f"\n已写入: {out_path}")


if __name__ == "__main__":
    main()
