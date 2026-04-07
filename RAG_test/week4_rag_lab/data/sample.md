# Week 4 RAG 学习样例（Markdown）

本文件与 `sample.pdf` 一起用于**最小 Pipeline**：加载 → 分块 → 向量索引 → 问答。

## 要点

- **检索增强生成（RAG）** 把外部文档切块后写入向量索引，查询时先检索相关片段再交给大模型生成答案。
- 与纯向量实验（`embedding_test/zh_retrieval_lab`）不同，本阶段使用 **LlamaIndex** 串起完整链路。
