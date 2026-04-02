# 中文检索实验：`zh_retrieval_lab`

本目录是一个**独立的学习型小工程**：在**内存中**完成「文档编码 → 检索 → 评价」，对比 **OpenAI 嵌入** 与 **本地 BGE-M3**，并实现 **BM25（`rank_bm25`）与稠密向量的混合检索**。

它与同级的 **Qdrant 本地部署**（`../README.md`）**互不依赖**：不需要启动 Docker、不需要向量数据库即可跑通对比脚本。适合先理解「检索与评价」再接入 Qdrant、Elasticsearch 等工程组件。

---

## 1. 项目目标与边界

| 项目做什么 | 项目刻意不做什么 |
|------------|------------------|
| 用小语料演示稠密检索、词法检索与两种混合策略 | 不接 Qdrant / Milvus 等向量库（便于专注算法与指标） |
| 对比两种典型嵌入来源：API（OpenAI）与开源本地（BGE-M3） | 不做工业级分词、索引分片、实时增量索引 |
| 用 MRR、Recall@k 做可复现的定量对比 | 不保证在任意业务语料上最优（语料需自行替换验证） |

---

## 2. 目录与文件结构

```
zh_retrieval_lab/
├── README.md              # 本说明（项目专档）
├── __init__.py            # 包标记
├── corpus.py              # 内置中文文档与查询 + 相关性标注
├── tokenize_zh.py         # 中文分词（供 BM25 使用）
├── metrics.py             # MRR、Recall@k 定义与计算
├── hybrid.py              # BM25 索引、余弦相似度、加权混合、RRF
├── embed_backends.py      # OpenAI / BGE-M3 嵌入封装与可用性探测
├── run_compare.py         # 命令行入口：编码 → 多路检索 → 汇总 → 写结果文件
└── results_last_run.txt   # 最近一次运行生成的指标表（若存在；通常已被 .gitignore 忽略）
```

**与上级目录的关系**

- `embedding_test/requirements.txt`：合并了 **Qdrant 客户端** 与本实验所需的 **numpy / jieba / rank-bm25 / openai / FlagEmbedding / torch** 等；安装一次即可同时支持 `qdrant_learn.py` 与本实验。
- 若你**只跑本实验**、不碰 Qdrant，仍需安装该 `requirements.txt`（或按下方「依赖」一节自行挑选包）。

---

## 3. 各模块职责说明

### 3.1 `corpus.py`：语料与标注

- **`Doc`**：字段 `doc_id`（整型）、`text`（正文）。
- **`QueryItem`**：字段 `qid`、`text`、`relevant_doc_ids`（frozenset，表示与该查询相关的文档 id）。
- **`DOCS` / `QUERIES`**：固定列表，用于教学演示。查询多为**口语化或同义表述**，与正文**词面不完全重合**，用来观察 **BM25（词匹配）** 与 **向量（语义匹配）** 的差异。

扩展方式：在保持 `doc_id` 唯一、`relevant_doc_ids` 与 `DOCS` 一致的前提下，增删文档与查询即可；评价逻辑无需改。

### 3.2 `tokenize_zh.py`：中文 BM25 的前置

- 使用 **jieba** 对句子做粗粒度分词，输出词列表。
- BM25 依赖「词袋」统计，中文若不切词直接按字切，统计行为会不同；本实验采用 jieba 作为常见基线。

### 3.3 `metrics.py`：评价指标

- **`mrr(rank, relevant)`**：在排序列表中找**第一个**落在 `relevant` 里的文档，返回 \(1/\text{rank}\)；若无命中则为 0。对多条查询取平均即 **MRR**。
- **`recall_at_k(rank, relevant, k)`**：看前 `k` 个结果中是否**至少出现一条**相关文档；命中为 1，否则为 0（本语料每查询通常仅 1 条相关，与「是否进前 k」等价）。对多条查询取平均即 **R@k**。

### 3.4 `hybrid.py`：检索与混合

| 函数/概念 | 作用 |
|-----------|------|
| `build_bm25` / `bm25_scores` | 基于 `rank_bm25.BM25Okapi` 建索引并对查询打 BM25 分 |
| `dense_scores` | 查询向量与所有文档向量的**余弦相似度**（逐文档一条标量） |
| `hybrid_weighted` | 对 BM25 分数与稠密分数分别 **min-max** 到 \([0,1]\)，再按 **`alpha * dense + (1-alpha) * bm25`** 融合（`alpha` 越大越信任向量） |
| `rrf_from_two_ranks` | **倒数排名融合（RRF）**：仅使用两个排序的名次，按 \(1/(k+\text{rank})\) 累加得分（实现里常数 `k=60`），不直接使用原始 BM25/相似度的量纲 |

**四种被评价的检索方式**（在 `run_compare.py` 中组合）：

1. **dense_only**：仅按余弦相似度排序。  
2. **bm25_only**：仅按 BM25 排序。  
3. **hybrid_weighted_a{alpha}**：加权混合分数后排序。  
4. **hybrid_rrf**：对稠密排序与 BM25 排序做 RRF。

### 3.5 `embed_backends.py`：嵌入模型

- **`OpenAIEmbedder`**：调用 OpenAI API，默认模型 **`text-embedding-3-small`**，批量请求、按 `index` 排序保证与输入顺序一致。需要环境变量 **`OPENAI_API_KEY`**。
- **`BGEM3Embedder`**：加载 **`BAAI/bge-m3`**（FlagEmbedding），返回稠密向量矩阵。首次运行会从 HuggingFace 拉取权重，需磁盘与网络；CPU 可运行。
- **`try_openai` / `try_bge_m3`**：失败时返回 `None`，主程序跳过对应分支并打印提示，避免静默错误。

### 3.6 `run_compare.py`：主流程

1. 对全部文档分词 → 构建 **BM25Okapi**。  
2. 探测可用的嵌入后端，分别对**所有文档**与**所有查询**编码，得到 `(n_docs, dim)`、`(n_queries, dim)` 矩阵。  
3. 对每个查询、每个后端，计算上述四种排序方式，用 `metrics.py` 聚合 **MRR、R@3、R@5**。  
4. 终端打印表格，并写入 **`results_last_run.txt`**（与脚本同目录）。

命令行参数：

- **`--alpha`**：加权混合中的向量权重，默认 `0.65`。

---

## 4. 环境与运行步骤

在 **`embedding_test`** 目录下执行（与包导入路径一致）：

```powershell
cd E:\PycharmProjects\2026Agent\embedding_test
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

可选：启用 OpenAI 分支（PowerShell）：

```powershell
$env:OPENAI_API_KEY = "sk-..."
```

运行：

```powershell
python -m zh_retrieval_lab.run_compare
python -m zh_retrieval_lab.run_compare --alpha 0.5
```

**常见情况**

- 未设置 `OPENAI_API_KEY`：仅输出 BGE-M3 相关行（若 BGE 可用）。  
- 未安装 PyTorch / FlagEmbedding 或无法下载模型：BGE 分支跳过；若 OpenAI 也未配置，程序会以错误码退出并提示至少启用一种嵌入。

---

## 5. 最终评估指标说明

脚本输出的三列数值（对每个「嵌入后端 × 检索方法」各一行）含义如下。

### 5.1 MRR（Mean Reciprocal Rank，平均倒数排名）

- **含义**：对每个查询，看**第一个相关文档**出现在排序列表的第几位；取该位次的倒数 \(1/r\)，再对所有查询取平均。  
- **取值范围**：\([0, 1]\)，越大越好。  
- **在本项目中的解读**：若相关文档常被排到第 1 位，MRR 接近 1；若经常落在第 2、第 3 位，MRR 会明显降低。

### 5.2 R@3 / R@5（Recall at k，此处为「前 k 是否命中」型）

- **含义**：对每个查询，若前 `k` 条结果中**至少有一条**相关文档，则记 1，否则记 0；再对所有查询取平均。  
- **取值范围**：\([0, 1]\)，越大越好。  
- **与标准 IR 中「多相关文档的 recall」区别**：本语料多数查询仅标注 **1** 个相关 id，因此这里的 R@k 更接近「Top-k 是否覆盖该唯一相关文档」，便于小班教学；若你扩展为多相关文档，可在 `metrics.py` 中改为「前 k 覆盖的相关比例」等定义。

### 5.3 如何对比 OpenAI 与 BGE-M3

- 在**同一语料、同一查询集**下，比较两行 **`… | dense_only`**（分别对应两个后端）：差异主要来自**嵌入模型**对中文语义、领域词的处理。  
- 再比较 **`bm25_only`**（与嵌入无关，所有后端共用同一行逻辑，实际上每个后端打印的 bm25 行数值应一致）：作为**纯词法基线**。  
- **`hybrid_*`** 展示在**当前 `alpha` 与 RRF 设定**下，词法与语义如何折中；换语料后最优 `alpha` 往往需要重新扫参。

---

## 6. 工程与实践上的参考意义

1. **嵌入选型**：用同一套标注快速对比「商业 API vs 本地开源」在中文上的排序质量，为是否上云、是否蒸馏/微调提供粗粒度依据。  
2. **混合检索范式**：加权融合（可解释、可调 `alpha`）与 RRF（不依赖分数尺度、实现简单）是工业界常见基线；本仓库提供最小可运行实现，便于对照论文与产品文档。  
3. **评价习惯**：先固定小语料与 MRR / R@k，再扩展语料与指标（如 nDCG），符合「可复现实验 → 再接向量库与在线 A/B」的路径。  
4. **与 Qdrant 的衔接**：当前实现是**内存暴力检索**（文档数极少）；当规模变大时，可把「稠密部分」交给 Qdrant 的向量检索，把「BM25 部分」交给 Elasticsearch/OpenSearch 或内置稀疏通道，再用与本项目类似的 **加权或 RRF** 做结果融合——概念上一致，仅存储与召回引擎替换。

---

## 7. 局限与后续可改进方向（自学延伸）

- 语料规模小，指标波动大，**不宜**直接外推到生产效果。  
- 未使用 BGE-M3 的稀疏/多向量能力，仅对比**稠密向量**。  
- 分词、停用词、同义词扩展未做，BM25 仍有工程优化空间。  
- 若需与 `qdrant_learn.py` 联动：可将文档向量写入 Qdrant，仅用本项目的 **BM25 + 融合逻辑** 在应用层合并线上检索结果。

更完整的 **Qdrant Docker 部署、端口与排错**，见上级文档：**[../README.md](../README.md)**。
