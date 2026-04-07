# Week 4 RAG 学习子项目（最小 Pipeline）

**学习对齐**：P0 · Week 4 · 贴近 M1（LlamaIndex：加载 → 分块 → 索引 → 检索 → 生成）

与 `embedding_test/zh_retrieval_lab` **分工**：本目录走 **LlamaIndex 全链路**；上级目录实验偏 **向量与 BM25 混合检索** 底层。环境可与 `embedding_test` **共用 DashScope Key**（见 `env_config.py` 加载顺序）。

---

## 环境配置

1. Python **3.10+**，建议虚拟环境。
2. 安装依赖：

```bash
cd RAG_test/week4_rag_lab
pip install -r requirements.txt
```

3. 复制 `.env.example` 为 `.env`，填写 **OpenAI** 或 **通义 DashScope**（与 `zh_retrieval_lab` 相同变量即可复用上级 `embedding_test/.env`）。
4. 生成 `data/sample.pdf`：脚本从 **`data/磁阻效应实验讲义(第3版)-邹斌.pdf`** 抽取**前 5 页**写入 `sample.pdf`（整本过大，便于最小 Pipeline 快速跑通）。需先把该讲义 PDF 放在 `data/` 下。

```bash
python scripts/build_sample_pdf.py
```

若提示无法覆盖 `sample.pdf`（Permission denied），请先**关闭** IDE 或 PDF 阅读器中对 `data/sample.pdf` 的预览。

**排障**：若出现 `No Python at '...Python312\python.exe'`，说明仓库根目录 `.venv` 仍指向已卸载/移动的 Python。请在仓库根目录删除 `.venv` 后，用当前机器上存在的解释器重建，例如：

```powershell
cd E:\PycharmProjects\2026Agent
Remove-Item -Recurse -Force .venv
py -3.11 -m venv .venv
# 或: "D:\Program Files (x86)\python.exe" -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r RAG_test\week4_rag_lab\requirements.txt
```

`requirements.txt` 仅使用 ASCII 注释，避免 Windows 下 pip 按系统默认编码（如 GBK）读文件时失败。

若使用 **DashScope** 的 `text-embedding-v3` / `text-embedding-v4` 等名称时报 `OpenAIEmbeddingModelType` 无效：`LlamaIndex` 的 `OpenAIEmbedding` 只枚举了部分官方模型名；`run_minimal_pipeline.py` 已对非枚举名自动使用 **占位 model + `model_name` 传入真实模型**（与 `llama_index.embeddings.openai` 实现一致）。

若 LLM 报 **`Unknown model 'qwen-turbo'`**：`LlamaIndex` 的 `OpenAI` 会校验 `openai_modelname_to_contextsize`；`qwen-*` 等不在内置表。本项目用 **`compat_llm.OpenAICompatCustomModel`**：内部以 `gpt-4o-mini` 占位（tiktoken/metadata），请求体里 `model` 仍为你配置的 `QWEN_LLM_MODEL`。可选环境变量 **`QWEN_LLM_CONTEXT_WINDOW`**（或 `LLM_CONTEXT_WINDOW`）覆盖上下文窗口元数据。

---

## 最小 Pipeline 做什么

| 步骤 | 实现 |
| --- | --- |
| 加载 | `SimpleDirectoryReader` 读 `data/*.md`；`PyMuPDFReader` 读 `data/sample.pdf` |
| 分块 | 默认 `Settings` 的 `SentenceSplitter`；或设环境变量 `CHUNK_STRATEGY` 为 `sentence_512` / `token_256` / `semantic_90`（定义见 `chunking_strategies.py`） |
| 索引 | `VectorStoreIndex.from_documents`（内存，未持久化） |
| 生成 | `as_query_engine` → `query()` |
| 检索可见（层级 A） | `Response.source_nodes`；`print_retrieved_chunks()` 打印相似度、来源与正文片段 |
| 生成提示可见（层级 B） | `GenerationPromptCallbackHandler` 监听 `CBEventType.LLM`，打印发给模型的 `MESSAGES`；默认 QA 模板下尝试拆分 Context / Query |

运行：

```bash
python run_minimal_pipeline.py
```

可选：指定分块策略（与对比脚本中三种一致），例如 PowerShell 下 ` $env:CHUNK_STRATEGY="token_256"; python run_minimal_pipeline.py `。

**三种分块策略对照**：在同一 Query 与 `top_k` 下依次建索引并做向量检索，**不调用 LLM**，将相似度统计与粗粒度 bigram 覆盖率写入 `output/chunking_compare_latest.json`。

```bash
python compare_chunking_strategies.py
# 自定义查询与输出路径：
python compare_chunking_strategies.py --query "你的问题" --out output/my_compare.json
```

**排障：改了 `chunking_strategies.py` 但 JSON 像没变**  
1. 确认已**保存文件**，并**重新运行** `compare_chunking_strategies.py`（看终端是否打印 `chunking_strategies 加载自: ...` 路径应对应当前仓库）。  
2. 打开 **`chunking_compare_latest.json`** 看 **`generated_at_utc`** 是否更新；若 IDE 里文件未自动刷新，请关闭标签再打开或从磁盘重新加载。  
3. 语义策略参数微调在**小语料**上可能得到**相同的节点划分**，`indexed_node_count` / `raw_scores` 会几乎不变，属正常现象；JSON 里现在有 **`parser_runtime`** 与 **`semantic_env`**，可确认实际使用的 `buffer_size` / `breakpoint_percentile_threshold`。  
4. 不改代码只调参：可设环境变量 `SEMANTIC_BUFFER_SIZE`、`SEMANTIC_BREAKPOINT_PCT` 后再运行对比脚本。

指标说明（见 JSON 内 `metrics_note`）：**mean_score / min / max** 来自向量检索分数；**query_bigram_coverage** 表示查询中汉字 **bigram** 在 top-k 拼接正文里出现的比例，仅作粗对照，**不能**替代 RAGAS 等标注评估。

需有效 `OPENAI_API_KEY` 或 `DASHSCOPE_API_KEY`。通义路径下默认 `qwen-turbo` + `text-embedding-v3`，可在 `.env` 覆盖 `QWEN_LLM_MODEL` / `QWEN_EMBEDDING_MODEL`。**语义分块**（`semantic_90`）建索引时会额外调用嵌入 API，耗时与费用高于另外两种。

终端除 **Answer** 外会输出 **检索到的内容（层级 A）**：每条含 `score`、`source` / `page`（若有）与截断后的 Chunk 正文，便于对照「检索 → 生成」是否一致。

在 **`engine.query()` 内部**（LLM 调用结束后、返回答案前）会输出 **生成阶段发给 LLM 的结构化提示（层级 B）**：先列出每条 `ChatMessage` 的 `role`，对默认 `CHAT_TEXT_QA` 的 USER 消息会尽量拆成 **Context（即 `{context_str}`）** 与 **Query**。若你改用自定义 `text_qa_template` 或 `ResponseMode` 导致多轮 LLM 调用，可能出现**多段**「生成阶段」输出，属正常现象。

---

## 目录结构

```
week4_rag_lab/
├── README.md
├── requirements.txt
├── .env.example
├── env_config.py           # 加载 .env（先 embedding_test，再本目录）
├── run_minimal_pipeline.py      # 最小问答入口
├── chunking_strategies.py       # 三种分块策略定义
├── compare_chunking_strategies.py # 建索引 + 检索指标对比 + 写 JSON
├── generation_prompt_debug.py   # 层级 B：打印发给 LLM 的 messages
├── output/                      # 默认写入 chunking_compare_latest.json（可 gitignore）
├── data/
│   ├── sample.md
│   ├── 磁阻效应实验讲义(第3版)-邹斌.pdf  # 源讲义（自备）；build_sample_pdf 从中抽取前 5 页
│   └── sample.pdf          # 由 scripts/build_sample_pdf.py 从上述讲义生成
└── scripts/
    └── build_sample_pdf.py
```

---

## 学习启示（模拟面试 QA）

**问：这个最小 Pipeline 和 zh_retrieval_lab 有什么区别？**  
答：`zh_retrieval_lab` 用手写 BM25 + 稠密分数做**检索对比**；本项用 LlamaIndex 把 **Loader、Node、Index、QueryEngine** 串成产品化 RAG，为分块对比、RAGAS 评估打骨架。

**问：为什么 Embedding 要和 Week3 实验对齐？**  
答：换分块或混合策略时，若 Embedding 不变，指标变化才主要反映「策略」而不是「换模型」。

**问：PDF 为什么用 PyMuPDF？**  
答：Week4 教学要求之一；LlamaIndex 的 `PyMuPDFReader` 基于 PyMuPDF，适合常见版式文本抽取。

**问：当前索引存在哪里？**  
答：默认只在**内存**；要持久化可后续接 `StorageContext` + 本地目录或向量库（Qdrant 等）。

**问：通义 Embedding 为什么要限制 batch？**  
答：DashScope 兼容接口对单次 `input` 条数常有限制（如 ≤10），`OpenAIEmbedding(embed_batch_size=10)` 避免 400。

**问：层级 A 为什么要打印检索到的 Chunk？**  
答：调试 RAG 时先确认 **Retriever 是否召回了正确段落**，再判断 **LLM 是复述还是幻觉**；`query()` 返回的 `Response.source_nodes` 与最终 Answer 分开观察，问题定位更快。

**问：三种分块对比脚本在比什么？**  
答：在 **同一套 Embedding 与 top_k** 下，换 **NodeParser / Splitter**，看 **索引节点数、检索分数分布、召回正文长度、查询 bigram 覆盖率** 等差异；语义分块会改变「一块里装多少句」，向量命中位置随之变化。要评「答案对不对」仍需人工或 RAGAS。

---

*对照：`RAG_test/Week4_前置知识教学.md` 第二节「本周学习项目指南」。*
