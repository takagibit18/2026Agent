# 代码审查与调试 Agent

**Review & Debug Agent** — 面向本地仓库与变更集的 LLM Agent：结构化代码审查（Review）与辅助调试（Debug）。


| 字段            | 说明                   |
| ------------- | -------------------- |
| 建议开源仓库名（slug） | `review-debug-agent` |
| 英文展示名         | Review & Debug Agent |
| 许可证（规划）       | MIT                  |


> 详细规划见 [code_review_debug_agent_plan.md](code_review_debug_agent_plan.md)（意图、架构、里程碑、分工）。

---

## 命名定稿与重名检索（2026-04-07）

团队采用规划文档中的**稳妥方案**：对外 GitHub 仓库 slug 使用 `**review-debug-agent`**，中文 README 主标题使用上表「代码审查与调试 Agent」。


| 候选                   | 类型     | 检索结论（抽样）                                                                         |
| -------------------- | ------ | -------------------------------------------------------------------------------- |
| `review-debug-agent` | **已定** | GitHub 上未见同名高星主项目；与 `agent-reviews`、`roborev` 等不同名，叙事为「review + debug CLI」，不易混淆。 |
| `patchlens`          | 备选     | PyPI 无同名包；存在 `prlens` 等带 lens 的 PR 审查工具，若采用需加强副标题区分。                             |
| `diff-doctor`        | 备选     | 口语化，未在本次检索中作为包名重点冲突；与已定方案相比辨识度略弱。                                                |


**PyPI**：未检索到名为 `review-debug-agent` 或 `patchlens` 的包；若日后发布 CLI，请在 [https://pypi.org](https://pypi.org) 发布前再次确认包名可用性（`pip search` 已废弃，以网站检索为准）。

---

## 与本目录其他文档

- [学习规划.md](学习规划.md) — 仓库级学习路线（P0/P1/P2、周次等）。
- [final_plan.md](final_plan.md) — 与规划文档中「Python + FastAPI + 可部署」主线对照。

---

## 学习启示（模拟面试 QA）

**问：这个 Agent 解决什么问题，MVP 长什么样？**  
答：把「变更集 + 可选日志/失败输出」转成可执行的 Review 列表和 Debug 假设与步骤；MVP 是 CLI，不先做 GitHub 评论机器人，避免 scope 爆炸。

**问：为什么强调结构化输出？**  
答：便于人审阅、接 CI、做 schema 校验和黄金集评测；字段如 severity、location、evidence、suggestion 与规划文档一致。

**问：单 Agent 够吗，为什么还要提工具并发？**  
答：简历叙事用单 Agent + 清晰工具集即可；只读工具可并发、写入串行、执行走沙箱，是工程上的安全与效率折中。

**问：评测为什么以自建黄金集为主？**  
答：可控、可复现、口径清晰；公开 benchmark 只做小样本补充，避免和「端到端修 patch 并合并」的榜单定义绑死。

**问：后续怎么扩展到 GitHub？**  
答：核心不变：内部输入仍是 diff/上下文，外部只做适配器（Webhook/GitHub App），把事件转成同一套输入即可。

**问：仓库对外语言和注释怎么定？**  
答：按规划待确认项：**中文 README**，代码与注释 **英文**，便于协作与国际化阅读。