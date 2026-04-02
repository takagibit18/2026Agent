---
name: repo-2026agent-learning-conventions
description: >-
  Aligns Agent/LLM work in the 2026Agent repo with the learning roadmap (P0/P1/P2,
  Week N, M1–M3), learner-friendly code/docs, and README sections for mock-interview QA.
  Use when generating or editing code or docs in 2026Agent, when the user @-mentions
  .cursor/rules/skills.md or AGENTS.md, or when discussing learning alignment, RAG lab
  subprojects, or MultiAgent study materials.
---

# 2026Agent 学习仓库 · Agent 协作约定

适用于仓库内与 **Agent / LLM 应用** 相关的学习、实验与小型子项目。通过 Cursor（Chat、Composer、后台 Agent 等）**生成或修改代码与文档**时按下列执行。默认读者为 **入门到进阶** 的学习者。

若对话未自动带上仓库规则，应提醒用户 **@** 引用 `.cursor/rules/skills.md` 或根目录 `AGENTS.md`。

**权威对照**：`MultiAgent/学习规划.md`（P0/P1/P2、按周路径、M1–M3 等）。本技能只规定 **产物中如何体现**，不重复全文。

---

## 1. 与学习计划对齐

实现或评审时须能说明「对应规划的哪一层」，并在可维护处标明（任选或组合，避免冗余）：

| 位置 | 做法 |
| --- | --- |
| PR / commit 说明 | 写明 **P0 / P1 / P2**；若明确则写 **Week N** 或 **M1 / M2 / M3** |
| 新增或大幅改动的模块 | 包/文件顶部 **模块 docstring** 一行，例：`学习对齐: P0 · Week 4 · 贴近 M1（RAG 基线）` |

**分层速查**：

| 层级 | 标注关键词 |
| --- | --- |
| **P0** | Python 工程化、RAG 全流程、LangChain/LlamaIndex、Prompt、向量库、LLM API、Token 成本 |
| **P1** | Agent 原理与手写/框架、FastAPI、Docker、RAG 评估深化、Transformer 直觉、安全合规、Embedding 选型、技术选型 |
| **P2** | 微调基础、Redis/缓存与队列、可观测性、多 Agent、MCP、K8s 基础、知识图谱等加分方向 |

**里程碑**：**M1** RAG 问答 + 评估基线；**M2** 可部署 API（流式、容器、缓存与工程化）；**M3** 多步 Agent + 安全与报告。

无法对应 P0–P2 的改动（如纯排版）：说明中写 **「规划外 / 仓库维护」**。

---

## 2. 部署与调试：学习友好默认

仅要求 **本次任务触及** 的范围（不必全仓库重写历史）：

- **结构**：子项目职责清晰；入口在 README 或模块 docstring 可一眼找到。
- **文档字符串**：关键模块须有模块 docstring（目的、主要入口、依赖环境）；非显然逻辑用行内注释，优先写 **为什么**。
- **配置**：说明来源（环境变量 / `.env` 键）、默认值、本地与近生产的差异；避免魔法数字，注明单位与取值理由（必要时）。
- **错误信息**：可读；适合学习者时可提示下一步（查哪项配置、哪项服务是否启动）。

---

## 3. 子项目 README

对 **新建** 或 **大幅更新** 的子项目 `README.md`：

- 文末 **必须** 含二级标题：`## 学习启示（模拟面试 QA）`
- 形式：**模拟面试官提问** + **简明回答**；覆盖架构、关键流程、选型、主要接口、局限与改进。
- 建议 **5–10** 条，与文档体量匹配。

---

## 4. 执行优先级（速记）

1. 触及学习相关代码：**P0/P1/P2（及 Week / M1–M3）** + 学习友好注释与配置说明。  
2. 新建或大改子项目 README：**保留** `## 学习启示（模拟面试 QA）`。  
3. 细节以 `MultiAgent/学习规划.md` 为准。

---

## 可选延伸阅读

需要完整周次与面试清单时，读取仓库内 `MultiAgent/学习规划.md`（一层引用，避免重复载入）。
