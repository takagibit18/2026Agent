# Qdrant 本地部署与测试步骤

本目录用于入门学习：用 Docker 启动 **Qdrant 服务**（镜像 **`qdrant/qdrant`**，**不需要**单独拉 Python 镜像），用本机 **Python** 运行 `qdrant_learn.py` 验证 **CRUD、相似搜索、过滤查询**。

环境与连接类问题的处理说明单独放在 **[TROUBLESHOOTING.md](TROUBLESHOOTING.md)**，本文只保留推荐操作步骤。

---

## 环境与镜像说明（Windows）

- **Docker Desktop**：安装并保证 `docker`、`docker compose` 在 PowerShell 中可用。
- **WSL 2**：Docker Desktop 通常依赖 WSL2。执行 `wsl -l -v` 若仅有 **`docker-desktop`** 且 **VERSION 为 2**、**Running**，即可支撑本项目的容器；是否再安装 **Ubuntu** 发行版为可选（便于在 Linux 里开发）。
- **只需下载的镜像**：**Qdrant 官方镜像**（本仓库 `docker-compose.yml` 中为 `qdrant/qdrant:v1.12.5`）。Python 装在本机即可，一般不必为练习再建 Python 容器。

---

## 推荐路径：用 Compose 启动（方案 A）

在 **未映射端口** 的情况下，浏览器访问 `http://localhost:6333` 会 **拒绝连接**。下面流程会正确把本机 **6333/6334** 映射进容器。

### 1. 进入本目录

```powershell
cd E:\PycharmProjects\2026Agent\embedding_test
```

（路径按你本机仓库位置调整。）

### 2. 拉取镜像

```powershell
docker compose pull
```

（也可先 `docker pull qdrant/qdrant:v1.12.5`，与 compose 中版本一致即可。）

### 3. 后台启动

```powershell
docker compose up -d
```

### 4. 确认端口已映射到本机（重要）

```powershell
docker ps
```

请确认 **PORTS** 中已将 **6333、6334** 映射到本机；若 **localhost 拒绝连接** 或 **PORTS** 显示异常，见 **[TROUBLESHOOTING.md](TROUBLESHOOTING.md)**（Docker 端口一节）。

### 5. 验证 Qdrant 已就绪

- 浏览器打开 [http://localhost:6333/dashboard](http://localhost:6333/dashboard)（Web 控制台）。
- 或访问根路径 [http://localhost:6333/](http://localhost:6333/)，若返回 **JSON**（含版本等信息），说明 HTTP 接口正常。

**端口说明**

| 端口 | 用途 |
|------|------|
| 6333 | HTTP REST API（浏览器 Dashboard、REST 客户端） |
| 6334 | gRPC（`qdrant-client` 可优先走此端口，见下） |

数据持久化在 Compose 命名卷 **`qdrant_storage`** 中；执行 `docker compose down -v` 会清空本地 Qdrant 数据，慎用。

运行脚本时出现 **503**、连接失败等异常，见 **[TROUBLESHOOTING.md](TROUBLESHOOTING.md)**。

---

## 当前进度：若你已完成「本机网页 / JSON 正常」

说明 **Compose 方案 A** 与 **端口映射** 已正确，Qdrant 服务可用。**接下来**请在本机继续下面步骤（仍在 `embedding_test` 目录下操作即可）。

### 下一步 1：安装 Python 依赖

建议使用虚拟环境（可选）：

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

不建 venv 也可：

```powershell
pip install -r requirements.txt
```

### 下一步 2：运行入门脚本

```powershell
python qdrant_learn.py
```

**预期现象**

- 终端依次打印 `=== CRUD ===`、`=== 相似搜索（无过滤）===`、`=== 相似搜索 + payload 过滤 ===` 等段落。
- 无「无法连接 Qdrant」报错。
- 脚本会 **删除并重建** 集合 `learn_demo`，再写入示例点；**可重复运行**。

连接或脚本异常时见 **[TROUBLESHOOTING.md](TROUBLESHOOTING.md)**。

### 下一步 3（可选）：在 Dashboard 里对照数据

脚本跑成功后，刷新 [Dashboard](http://localhost:6333/dashboard)，在界面中查看集合 **`learn_demo`** 与点数据，与终端输出对照，便于理解 **collection / point / payload**。

### 下一步 4（可选）：改参数做实验

- 在 `qdrant_learn.py` 中调整 **`VECTOR_SIZE`** 时，须与写入的向量长度一致，并依赖脚本内的 **删库重建** 逻辑或手动删集合。
- 更换 Qdrant 地址时，修改 `qdrant_learn.py` 中的 **`QDRANT_HOST` / `QDRANT_HTTP_PORT` / `QDRANT_GRPC_PORT`**，与 compose 端口映射一致。

---

## 常用运维命令

```powershell
# 查看日志
docker compose logs -f qdrant

# 停止（保留数据卷）
docker compose stop

# 停止并删除容器（卷仍在，数据一般保留在命名卷中）
docker compose down

# 停止并删除容器 + 命名卷（清空 Qdrant 本地数据，慎用）
docker compose down -v
```

---

## 不使用 Docker 的替代思路（了解即可）

向量库不强制 Docker。也可参考 [Qdrant 安装文档](https://qdrant.tech/documentation/guides/installation/) 使用 **二进制 / 云托管**；只要服务可达，将 `qdrant_learn.py` 中的 **`QDRANT_HOST`（及必要时端口）** 改为对应地址即可。

---

## 其他子项目：中文检索实验（独立文档）

目录 **`zh_retrieval_lab/`** 用于 **通义千问向量（DashScope）vs 本地 BGE-M3** 与 **BM25 + 向量混合** 的对比实验，**不依赖** Qdrant 或 Docker。说明、目录结构、指标定义与工程意义见专档：

**[zh_retrieval_lab/README.md](zh_retrieval_lab/README.md)**

---

## 文件说明

| 文件 | 说明 |
|------|------|
| `docker-compose.yml` | 定义 Qdrant 服务、**主机端口映射**、数据卷 |
| `requirements.txt` | Python 依赖（Qdrant 客户端 + `zh_retrieval_lab` 所需库，见子目录 README） |
| `qdrant_learn.py` | Qdrant 入门演示脚本 |
| `TROUBLESHOOTING.md` | 故障排除（端口、503、venv、检索实验后端等） |
| `zh_retrieval_lab/` | 中文检索实验（专档：`zh_retrieval_lab/README.md`；模型配置见其中 `.env.example`） |
