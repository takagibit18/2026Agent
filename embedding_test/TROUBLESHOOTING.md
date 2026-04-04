# `embedding_test` 故障排除与解决方案

本文件集中存放**环境问题、连接异常、虚拟环境**等排错说明。主流程与项目介绍见 **[README.md](README.md)**；中文检索实验见 **[zh_retrieval_lab/README.md](zh_retrieval_lab/README.md)**。

---

## Docker：端口未映射导致 localhost 拒绝连接

在未把容器端口发布到本机时，访问 `http://localhost:6333` 会**拒绝连接**。

### 如何用 `docker ps` 判断

**PORTS** 列应类似 **`0.0.0.0:6333->6333/tcp`**（以及 6334），**不要**只有 **`6333-6334/tcp`** 而没有 **`->`**：

| PORTS 显示 | 含义 |
|------------|------|
| `0.0.0.0:6333->6333/tcp, ...` | 本机可访问，正确 |
| 仅 `6333-6334/tcp` | 未发布到主机，**localhost 会拒绝连接** |

若曾在 Docker Hub 上「直接运行」镜像且**未加 `-p`**，容易出现后者。请停止并删除该容器后，**只使用本目录的** `docker compose up -d` 启动（参见 [README.md](README.md) 中的 Compose 流程）。

---

## Qdrant：脚本报「无法连接」或连接失败

1. 执行 `docker compose ps`，确认容器为 **Up**。  
2. 执行 `docker ps`，确认 **6333、6334** 已映射到本机（见上一节）。  
3. 仍异常时查看日志：`docker compose logs qdrant --tail 50`。

---

## Qdrant：浏览器正常，Python `qdrant-client` 报 503

可能原因与处理：

1. **`localhost` 解析为 IPv6 `::1`**（例如 `curl.exe -v http://localhost:6333/` 中出现 `Trying [::1]:6333`），与端口映射不一致时可能异常。请在脚本或客户端中使用 **`127.0.0.1`** 代替 `localhost`。  
2. **仅 REST（6333）异常**：少数 **Windows + Docker Desktop** 环境下，浏览器访问 HTTP 正常，但 Python 走 REST 仍 503。`qdrant_learn.py` 中的 **`connect_client()`** 会**先尝试 gRPC（6334）**，失败再退回 REST 6333。  
3. 若两种方式均失败，结合上一节检查端口映射与容器日志。

---

## Python：`python -m venv .venv` 报 `Permission denied: ...\.venv\Scripts\python.exe`

### 原因

终端**已经激活**了 `.venv`（提示符前有 **`(.venv)`**）时，当前 `python` 就是 **`.venv\Scripts\python.exe`**。对**同名**目录再执行 `python -m venv .venv` 会尝试覆盖正在使用的解释器文件，Windows 报 **Errno 13 Permission denied**。

### 处理步骤

1. 执行 **`deactivate`**，直到提示符前不再显示 **`(.venv)`**。  
2. **关闭**其他已激活**同一** `.venv` 的终端标签（含 Cursor / VS Code 集成终端）。  
3. 若环境损坏，在**未激活** venv 的 PowerShell 中删除后重建：

   ```powershell
   cd E:\PycharmProjects\2026Agent\embedding_test
   Remove-Item -Recurse -Force .venv
   py -3.12 -m venv .venv
   ```

   若 `py -3.12` 不可用，可改为 `py -3.11` 或使用**未在虚拟环境中**的 `python` 的完整路径。  
4. **可选**：改用新目录名，避免与残留进程纠缠：`py -3.12 -m venv .venv-new`，再 `.\.venv-new\Scripts\Activate.ps1`。

---

## `zh_retrieval_lab`：无任何可用嵌入后端（程序退出码 2）

- 未设置 **`DASHSCOPE_API_KEY`** 时，不会调用通义千问向量（DashScope OpenAI 兼容接口）。可将 Key 写在 **`zh_retrieval_lab/.env`** 或 **`embedding_test/.env`**（参见 **`.env.example`**），由 `python-dotenv` 加载。  
- **BGE-M3** 需要安装 **PyTorch、FlagEmbedding**，且能下载 **`BAAI/bge-m3`**（网络与磁盘空间）。  

至少启用**一种**后端后再运行：

```powershell
python -m zh_retrieval_lab.run_compare
```

仅远程向量：在百炼 / DashScope 创建 API Key 并配置 **`DASHSCOPE_API_KEY`**；地域与 **`DASHSCOPE_COMPAT_BASE_URL`** 需一致（北京 / 新加坡等见 `.env.example`）。仅本地：安装 `requirements.txt` 并确保能访问 HuggingFace（若受限需自行配置镜像或离线缓存）。

---

## DashScope：`401` / `invalid_api_key`

1. **Key 类型**：须使用百炼 / 模型服务台控制台创建的 **API-KEY**，不是 RAM 用户的 **AccessKey ID / AccessKey Secret**。  
2. **两份 `.env` 谁生效**：程序会先加载 **`embedding_test/.env`**，再加载 **`zh_retrieval_lab/.env`**，后者**覆盖**前者同名变量。若只修改了上级文件，而 `zh_retrieval_lab/.env` 里仍是旧 Key，请求会一直带旧 Key。  
3. **地域**：国内账号常用北京兼容地址；新加坡等国际域需使用对应 **`DASHSCOPE_COMPAT_BASE_URL`** 与在该地域创建的 Key（以控制台说明为准）。  
4. **改完仍 401**：先确认 `.env` 里 Key 正确；若怀疑系统里残留错误变量，可在「Windows 环境变量」中删除 `DASHSCOPE_API_KEY` 后重开终端。

### PowerShell 里 `echo $env:DASHSCOPE_API_KEY` 为空，是否正常？

**通常是正常的。** `zh_retrieval_lab/.env` 只在 **运行 Python** 时由 `python-dotenv` 读入并写入**该 Python 进程**的 `os.environ`，**不会**自动给 PowerShell 的 `$env:DASHSCOPE_API_KEY` 赋值。因此未在 shell 里手动 `export` / `$env:...=` 时，`echo` 看不到内容，**不代表** `.env` 没生效。

在 **`embedding_test`** 目录下用下面命令自检（**不打印 Key 全文**，只说明是否读到、长度多少）：

```powershell
cd E:\PycharmProjects\2026Agent\embedding_test
python -c "from zh_retrieval_lab.env_config import load_lab_env, dashscope_api_key; load_lab_env(); k=dashscope_api_key(); print('已读取 DASHSCOPE_API_KEY，长度', len(k)) if k else '未读取到（检查 .env 路径与变量名 DASHSCOPE_API_KEY）')"
```

若这里显示「已读取」而仍 401，则是 **Key 本身无效**或与 **地域 URL** 不匹配，需在百炼控制台重新核对 API-KEY。

---

## DashScope：`400` / `batch size is invalid, it should not be larger than 10`

通义千问文本向量在 DashScope **兼容模式**下，单次 `embeddings.create` 的 **`input` 列表长度**（一批里有多少条文本）**不能超过 10**。本仓库已把默认批次改为 **10** 并在 `env_config.qwen_embedding_batch_size()` 中封顶；若你自行把 **`QWEN_EMBEDDING_BATCH_SIZE`** 调大，仍会按 **≤10** 截断。

---

## 常用诊断命令（备忘）

```powershell
docker compose ps
docker ps
docker compose logs -f qdrant
```
