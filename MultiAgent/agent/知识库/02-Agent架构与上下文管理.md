## 4.4
### Claude code源码学习
![[Pasted image 20260404232644.png]]
#### 1. QueryEngine
这是 Claude Code 的==核心引擎==。它负责：
- 接收用户输入
- 组织消息历史
- 调用模型
- 处理工具调用
- 把结果回流到下一轮
#### 2. Tool:Claude Code 的执行接口层。
#### 3. AppState
AppState 是终端界面的运行时==状态中心==。  
它记录的不是某一个小组件状态，而是整个会话当前发生了什么，比如：
- 当前模式
- 工具权限
- 任务列表
- 远程连接状态
- 插件状态
#### 4.Context
在每轮任务里给模型补充的环境信息。  
典型内容包括：
- Git 状态
- 当前分支
- ==`CLAUDE.md`==
- 当前日期
- 项目记忆
#### 5. Plan Mode
作用不是直接改代码，而是先让 Claude：

- 做规划
- 输出方案
- 等待批准
#### 6. MCP

MCP 是 Claude Code 接入外部能力的重要方式之一。  
通过 MCP，它可以接入：

- 外部工具
- 外部资源
- 外部命令

## 4.6
### 上下文压缩（context compression）
- 去掉 **低信息密度内容**
- 保留 **对未来决策有影响的状态**
1️⃣ 状态提取（State Extraction）
从自然语言 → 结构化状态机(如json等)
2️⃣ 语义去冗余（Semantic Deduplication）
- 删除重复语义
- 合并相似意图
- 抽象表达（abstraction）
3️⃣ 重要性筛选（Saliency Filtering）
这是最关键的一步：
> 判断哪些信息“会影响未来推理”
典型保留：
- 任务目标
- 约束条件
- 已做决策
- 错误/失败路径
- 外部工具状态
丢弃：
- 一次性问题
- 已解决分支
- 无关上下文
#### 上下文压缩常用方法
##### Structured Memory（结构化记忆）
```
class ContextState(BaseModel):
    goal: str
    constraints: list[str]
    decisions: list[str]
    errors: list[str]
```

##### 3️⃣ Sliding Window + Compression（滑动窗口 + 压缩）
结构：`[远历史摘要] + [最近 N 轮 raw]`
- 短期 raw：措辞、工具返回；远历史：只留决策/状态级摘要 → 等价 **短期高保真 + 长期低保真**
- 要定死：N、何时压、摘要全量/增量、工具输出是否常驻 raw
- vs 纯 Summarization：不是「整段变一段」，近期字面可控、丢失更可预期
- 坑：摘要 drift、多话题混、长工具链中间步被压没 → 常与 **Structured Memory** 并用

##### 4️⃣ Retrieval + Embedding（检索 + 嵌入）
本质：**按需「选取」** 替代「先全量合并」；全量存库，query 时 **top-k** 再拼上下文
- 流程：chunk + payload 写入 → 用当前话（可叠 goal 等）检索 → **hits + 近窗 raw** 喂模型
- vs 文档 RAG：这里偏 **会话/轨迹**；**metadata 过滤**（会话、租户、时间）通常更重
- 坑：索引与对话状态一致、检索延迟、换任务仍捞旧话题（Hybrid / 时间窗 / 任务 id）、租户隔离与删除

##### 5️⃣ Programmatic Compression（程序化压缩）
用 **代码** 决定何时保留/丢弃/重置（控制平面），不全交给模型总结
- `task_changed` → reset 或归档 `ContextState`，防旧任务串台
- `error_loop` → 保失败链、缩成功废话，利排错
- 工具结果已入状态 → 丢复述只留 **diff**；长会话 → 摘要或转向量库
- 检测可用规则/计数/状态机；与 **Structured Memory** 同构；规则可单测
- 实践：**少量硬规则 + 结构化记忆 + 可选 LLM 摘要**
