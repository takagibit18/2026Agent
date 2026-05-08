## 4.24
### 多agent架构的评判准则
一个 Agent 业务值不值得拆成多 Agent，==核心不是“任务复杂不复杂”==，而是**单 Agent 是否已经在稳定性、可解释性、上下文管理、职责边界上碰到上限**。
#### 真正==值得拆==的场景
通常有这几个信号：
- 任务天然分成几个==**目标==不同、==上下文==不同、==评价标准==不同**的阶段。  
    例如“需求理解 / 检索 / 规划 / 执行 / 审核”彼此输入输出明确，放在一个 Agent 里会互相污染。
- 单 Agent 的 prompt 已经承担了**多种互相冲突的职责**。  
    例如既要当客服、又要做检索策略选择、又要做安全审查、又要决定是否转人工。
- 不同阶段需要的==**工具权限差异==很大**。  
    只读检索、外部 API 调用、代码执行、写库操作混在一个 Agent 里，风险会很高。
- 不同阶段的**失败模式不同**，而且你需要分别观测。  
    比如失败可能来自路由错误、检索错误、生成幻觉、安全误判。如果不拆，根因很难定位。
- 某些子任务本身已经能作为**独立可评测模块**存在。  
    例如 Router、Retriever、Safety Checker、Judge 都可以各自有指标和回归集。
#### **适合拆多 Agent 的典型场景**
- **高风险==决策链==**：金融、医疗、售后政策、代码修改、工单自动化。这里通常要==把“执行”和“审查”拆开。==
- **==长链路任务==**：任务执行步数多，且中间状态需要保存、恢复、重试。(由LLM底层attention机制决定)
- **多域知识协同**：例如客服同时涉及产品说明、售后政策、安全合规、升级路径，每一块判断标准不同。
- **强工具型系统**：某些 Agent 负责检索和规划，某些 Agent 负责执行工具调用，某些 Agent 只做验证。
- **需要人机协同审批**：多 Agent 能把“候选方案生成”和“最终批准建议”分层，便于插 human-in-the-loop。
#### ==**不适合拆==的场景**
- 单轮 FAQ、简单问答、低风险检索增强回答。
- 只是因为“任务看起来高级”就引入 Planner / Executor / Critic。
- 子 Agent 之间没有==明确契约==，只是互相转述自然语言。 **==(明确传递信息的schema,不要传自然语言)==**
- 你没有能力为每个 Agent ==单独做评测、日志和故障归因==。
- 拆完之后总延迟、成本、复杂度明显上涨，但成功率没有实质提升。

#### **工程上的评判准则**
可以用这 7条做决策：
1. **职责分离是否清晰**  
    要能够将问题拆解为多个子问题,并且各个子问题==没有强顺序依赖==,==不需要共享推理结果==
2. **上下文是否能有效隔离**  
    如果不同阶段需要完全==不同的上下文==，拆分收益很大。反过来，如果每个 Agent 都得吃完整上下文，拆了也没意义。
3. **是否可==独立评测**==  
    你能不能单独测 Router 的分类准确率、Retriever 的 hit rate、Safety Agent 的拒答准确率。不能评测，就很难维护。**(子agent必须有明确的输入,输出和评测要求)**
4. ==**系统级==评测**
	 除了对于子agent的独立评测外,还需要做系统级评测评估==端到端指标==. 因为有些架构中,单个agent的指标都很好,但是整体成功率反而下降,因为==中间层传递损耗大.==
5. **故障定位是否更容易**  
    好的多 Agent 架构，失败后能回答“错在路由、检索、执行还是审查”。如果拆完更难排障，这是失败设计。
6. **系统风险是否下降**  
    多 Agent 应该降低 blast radius。比如执行 Agent 有工具权限，Safety Agent 没有；审查 Agent 能拦住高风险输出。
7. **收益是否覆盖复杂度成本**  
    采用多agent架构几乎必然导致token消耗提高3到10倍,并提高运行的时间成本,因此不适合对延迟敏感的场景

#### 单 Agent + 工具分层 vs 多 Agent
- **单 Agent + 工具分层**：只有一个“决策脑”，工具只是外部能力。工具 response 就算很长,也不一定要全塞回主 context,而是可以落到外部存储、摘要、结构化状态或按需检索里。
- 这种方式主要解决的是**信息治理**问题：避免长 tool response 挤占 context window,让主 agent 的==注意力==被噪声稀释。
- **多 Agent**：是把“谁来做决策”拆开。不同 agent 有自己的职责、上下文、权限和失败模式,本质上是多个==独立决策体==协作。
- 所以,**tool response 后再分析** 不自动等于多 Agent。只要还是同一个 agent 在基于工具结果继续推理,通常仍然是单 Agent + 工具分层。
- 只有当分析、路由、执行、审查被拆成不同角色,并且每个角色都要单独评测和归因时,才更像真正的多 Agent。

## 5.5

### Web Chatbot 流式输出
当前 Talk-to-Sean 项目的流式输出链路是：
**前端 `useChat` -> `POST /api/chat` -> 服务端 `streamText` -> 模型 `chat/completions` stream -> `toUIMessageStreamResponse` -> 前端逐步渲染。**
核心点：
1. **前端不手写流解析**
    - `useChat` 负责发送消息、接收 stream、维护 messages 状态。
    - 前端不需要自己处理 `ReadableStream`、`EventSource` 或 token 拼接。
2. **服务端负责把模型流转成 UI Message Stream**
    - `/api/chat` 中调用 `streamText(...)` 获取模型流。
    - 再用 `result.toUIMessageStreamResponse()` 转成 Vercel AI SDK 前端能直接消费的响应。
3. **和 Python async 的区别**
    - Python async 主要解决的是==服务端并发/非阻塞等待==，例如 `async for chunk in stream`。
    - 但浏览器如何收到 chunk，还要再通过 FastAPI `StreamingResponse`、SSE 或 fetch stream 暴露出去。
4. **和 SSE 的区别**
    - SSE 是==传输协议层==，本质是服务端向浏览器单向推送 `data:` 事件。
    - Vercel AI SDK 底层也属于 HTTP 流式响应思路，但封装了前后端协议，少写解析和状态管理代码。
5. **和 LangChain stream 的区别**
    - LangChain stream 更偏==编排事件层==，能流出 token、tool call、retriever、agent step 等中间事件。
    - 当前项目没有 RAG 和 runtime tools，只需要模型回复流式输出，所以用 Vercel AI SDK 更轻。

一句话总结：  
**Vercel AI SDK 的 stream 是面向 Next.js Chat UI 的应用层封装；Python async 是并发模型，SSE 是传输协议，LangChain stream 是 Agent/Chain 编排事件流。**

### LLM WIKI
面试问题：**这个 AI 问答机器人是如何实现按照 Sean 的真实信息回答的？如何保证不幻觉？如果出现幻觉可追溯吗？有 guardrail 吗？**

回答思路：
1. **不是让模型自由扮演 Sean**
    - 项目采用 ==LLM Wiki grounding==。
    - `knowledge/raw` 保存原始公开资料，例如个人主页中的教育、项目、技能、联系方式。
    - `knowledge/wiki` 把 raw 资料整理成运行时可用的结构化知识页，例如 `sean.md`、`projects.md`、`capabilities.md`、`boundaries.md`。
2. **运行时如何注入真实信息**
    - `lib/wiki-context.ts` 按固定顺序读取 wiki 页面，生成 deterministic context bundle。
    - `lib/prompt.ts` 的 `buildSeanSystemPrompt()` 把 wiki context 拼进 system prompt。
    - `/api/chat` 调用 `streamText` 时把这个 system prompt 传给模型，因此模型回答时以 wiki 为主要事实来源。
3. **防幻觉机制**
    - 知识边界固定：只能基于 LLM Wiki 回答，不能靠常识补全 Sean 的经历。
    - Prompt guardrail：明确要求不要编造 metrics、timeline、employer、award、implementation detail。
    - 隐私 guardrail：联系方式只允许输出邮箱，不允许输出手机号。
4. **幻觉是否可追溯**
    - 可以追溯到三层：`knowledge/raw` 看原始来源，`knowledge/wiki` 看运行时允许使用的事实，`lib/prompt.ts` / `lib/wiki-context.ts` 看最终注入模型的 system prompt。
    - 如果模型说了 wiki 中不存在的事实，说明模型违反 guardrail；如果 wiki 中存在但 raw 不支持，说明资料整理阶段有错误。
5. **当前 guardrail 的成熟度**
    - MVP+ 阶段主要是 ==prompt-level + knowledge-boundary-level guardrail==。
    - 后续可增强为输出后校验、citation、wiki context hash、prompt version、trace log 和 hallucination eval。

一句话总结：  
**这个机器人通过 LLM Wiki 作为唯一知识源 + system prompt 约束 + 隐私/事实边界 guardrail 来模拟 Sean 的真实公开信息回答；当前可通过 raw/wiki/prompt 追溯幻觉来源，但还不是完整自动化审计系统。**
