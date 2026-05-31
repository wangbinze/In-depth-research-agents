# DeepSearch Agents: 深度研搜多智能体研究台

`DeepSearch Agents` 是一个基于 **DeepAgents** 框架（依托 **LangGraph** 与 **LangChain** 状态管理运行时）开发的**对话式多智能体深度研究工作台**。该系统专为制药、金融、电商等复杂研究场景设计，具备自动分析问题、分工调度专家助手、读取多格式附件、检索公开与私有数据库，并最终生成标准化 Markdown 报告和 PDF 交付件的能力。

---

## 🌟 核心特性

1. **多智能体协同调度**：
   * **主智能体（Main Agent）**：作为调度中心，承接长周期复杂任务，掌握文件读取与交付文档生成工具。
   * **网络搜索助手（Network Search Agent）**：通过 **Tavily API** 检索最新公开互联网资讯，返回结构化参考链接。
   * **数据库查询助手（Database Query Agent）**：动态感知 **MySQL** 业务数据库（表结构与样例数据），生成并执行 SQL 完成结构化数据提炼。
   * **RAGFlow 知识库助手（RAGFlow Agent）**：对接企业私有知识库，支持跨多文档的高精度语义问答。

2. **多模态文件交付与交互**：
   * 支持用户上传 `PDF`、`Word`、`Excel`、`Markdown` 及 `TXT` 格式附件。
   * 自动整理提炼素材并生成结构化的 Markdown 报告，可一键将其转为标准的 **PDF 文档** 保存到会话工作区。

3. **双通道通讯与实时进度推送**：
   * **FastAPI 接口层**：提供任务流控制（启动与主动取消）、附件上传与安全的文件浏览器/下载通道。
   * **WebSocket 双向长连接**：后端通过 `monitor` 机制实时推送智能体思维状态、工具调用日志、子任务进度及最终结果到前端，避免接口超时并提供流畅的响应体验。

4. **极客质感前端工作台 (Scheme B)**：
   * 基于 **React 19** + **Vite** + **Ant Design 5** 构建。
   * 采用深邃曜石黑与石板蓝（Obsidian & Slate Blue）的高端科技风格。
   * 支持多层半透烟熏玻璃（Smoke Glass）特效、高精度 Outfit/Share Tech Mono 字体排版、折叠式的思维链调试面板及文件预览下载。

---

## 🛠 技术栈一览

| 模块 | 核心技术/工具 | 作用描述 |
| :--- | :--- | :--- |
| **智能体框架** | `DeepAgents` (v0.5.7) | 创建主/子智能体，定义图拓扑与多专家分工调度 |
| **状态运行时** | `LangGraph` (v1.1.10) | 基于 `InMemorySaver` 提供状态检查点与执行中断/恢复能力 |
| **模型驱动层** | `LangChain` & `LangChain-OpenAI` | 统一接口封装，管理提示词模板与结构化输出声明 |
| **底层大模型** | 通义千问 `qwen-max` / `GPT-4` | 驱动智能体逻辑推理与工具执行决策 |
| **公开网络检索** | `Tavily API` | 面向 AI 优化的结构化网络内容检索 |
| **结构化数据库**| `MySQL 8.0` (Docker 容器化) | 模拟企业制药主数据、库存批次及销售流水库 |
| **私有知识检索**| `RAGFlow SDK` | 处理企业内部 PDF 白皮书、知识沉淀等非结构化检索 |
| **文件转换引擎**| `reportlab` / `python-docx` / `openpyxl` / `pypdf` | 实现多格式文件解析与高保真 Markdown 转 PDF |
| **后端 API 服务**| `FastAPI` (Uvicorn 运行时) | 构建 HTTP 调度服务、安全文件分发及 WebSocket 通信 |
| **包与环境管理**| `uv` | 高速 Python 环境隔离、锁定与依赖管理工具 |
| **前端应用** | `React` + `Vite` + `pnpm` + `antd` | 渐变发光 UI 界面与实时消息流处理 |

---

## 📂 项目目录结构

```text
In-depth-research-agents/
├── app/                         # 后端源码主目录
│   ├── agent/                   # 智能体核心配置与提示词加载
│   │   ├── subagents/           # 网络搜索、数据库查询、RAGFlow 知识库等子智能体
│   │   ├── llm.py               # 大模型初始化与代理连接
│   │   ├── main_agent.py        # 主智能体组装、Context 处理与任务执行入口
│   │   └── prompts.py           # 读取 yaml 集中管理的主/子智能体提示词
│   ├── api/                     # FastAPI 接口层与实时状态管理器
│   │   ├── context.py           # ContextVar 线程/协程级上下文共享
│   │   ├── monitor.py           # 统一封装 WebSocket 消息分发管理器
│   │   └── server.py            # API Server (HTTP 路由、上传下载、WebSocket 端点)
│   ├── prompt/                  # prompts.yml，提示词中心
│   ├── ragflow/                 # RAGFlow 连接适配与示例
│   ├── tools/                   # 主/子智能体可用工具（db_tools, tavily_tool, pdf_tools 等）
│   ├── utils/                   # 路径解析、文档转换等系统级通用函数
│   ├── output/                  # 动态生成：前端每个会话的沙盒工作区及产出物
│   └── updated/                 # 动态生成：用户上传附件的会话暂存目录
├── docker/                      # 本地 MySQL 数据服务容器配置
│   ├── mysql/                   # 制药公司核心数据初始化 mysql.sql 脚本
│   └── docker-compose.yaml      # 本地 MySQL 8.0 容器化启动配置
├── docs/                        # 项目说明文档与预置知识库（电商、金融行业 PDF）
├── frontend/                    # React 前端 SPA 源码目录
│   ├── src/                     # 前端 React 源代码
│   ├── package.json             # 依赖声明与打包脚本 (使用 pnpm 管理)
│   └── vite.config.ts           # 前端服务器端口与 API/WS 代理配置
├── .env.example                 # 环境变量模板文件
├── pyproject.toml               # Python 项目配置与依赖锁定描述
└── uv.lock                      # uv 环境锁文件
```

---

## 🚀 环境准备与快速启动

### 1. 克隆与配置环境变量
1. 复制根目录下的 `.env.example` 为 `.env`：
   ```bash
   cp .env.example .env
   ```
2. 打开 `.env`，按照您的实际 API 密钥修改配置（如：通义千问 `DASHSCOPE_API_KEY`、`TAVILY_API_KEY` 等）。

### 2. 启动本地 MySQL 数据库 (Docker)
项目在 `docker` 目录中预置了包含 50 种药品信息、150 条库存批次、100 条销售记录的制药公司核心业务数据库：
1. 进入 `docker` 目录：
   ```bash
   cd docker
   ```
2. 启动数据库容器（默认映射至本机 **`3307`** 端口，防止与本地已有 MySQL 冲突）：
   ```bash
   docker compose up -d
   ```
3. 容器首次创建时会自动导入 `docker/mysql/mysql.sql` 进行数据初始化。

### 3. 安装依赖并启动 Python 后端
推荐使用现代 Python 构建工具 **`uv`** 以获得极速的安装体验：
1. 回到项目根目录，同步安装虚拟环境与所有依赖：
   ```bash
   uv sync
   ```
2. 启动 FastAPI 后端服务（默认运行在 `8000` 端口）：
   ```bash
   uv run python app/api/server.py
   ```
   或者直接运行：
   ```bash
   uvicorn app.api.server:app --host 0.0.0.0 --port 8000 --reload
   ```

### 4. 安装并启动 React 前端
前端采用 `pnpm` 包管理工具：
1. 进入 `frontend` 目录：
   ```bash
   cd frontend
   ```
2. 安装依赖并启动开发服务器：
   ```bash
   pnpm install
   pnpm run dev
   ```
3. 打开浏览器访问控制台提示的地址（默认为 `http://localhost:5173`），即可进入深度研搜工作台。

---

## 💡 典型使用场景示例

在工作台首屏，系统预置了 5 种典型的示例任务，点击即可一键填入输入框，体验不同专家智能体的流转轨迹：

* **联网趋势研判 (网络搜索工具)**：
  > *"请使用网络搜索工具，检索 2026 年跨境电商 AI 客服趋势，列出 5 条关键变化，并附上来源链接。"*
  * **调用链路**：`Main Agent` ➡️ `Network Search Agent` (通过 Tavily) ➡️ 返回结构化资讯并汇总。
* **药品库存排查 (数据库查询工具)**：
  > *"请请使用数据库查询工具，查询库存大于 100 的药品，按库存量升序列出药品名称、批次号、仓库位置和过期日期。"*
  * **调用链路**：`Main Agent` ➡️ `Database Query Agent` (感知库表 ➡️ 获取 Schema ➡️ 组装 SQL 并执行) ➡️ 汇总报表。
* **上传文件分析 (文件读取工具)**：
  * **操作**：通过输入框左侧的 📎 按钮上传您的报告或文档（如 Word、PDF），随后发送任务：
  > *"请使用文件读取工具，读取我上传的文件，提炼核心观点、风险点和待补充信息，并给出下一步分析计划。"*
  * **调用链路**：`Main Agent` 直接调用 `read_file_content` 工具读取工作目录中的上传文件，并根据大模型分析输出大纲。
* **生成交付报告 (Markdown/PDF 工具)**：
  > *"请使用 Markdown 文档生成工具和 Markdown 转 PDF 工具，基于本次调研结果生成一份 Markdown 报告，并转换成 PDF 保存到当前工作目录。"*
  * **调用链路**：智能体在处理完信息后，调用本地 `generate_markdown` 创建报告，接着调用 `convert_md_to_pdf` 生成高保真 PDF 交付物，前端文件架中会实时浮现该文件并提供一键下载。

---

## 🔒 安全性与沙盒设计

* **路径安全隔离**：后端在 `download` 和 `files` (文件浏览器) 接口层做了严格的相对路径解析校验（使用 `Path.resolve()` 和 `.is_relative_to(output_dir)`），确保前端只能访问与下载 `app/output/` 沙盒目录下的文件，杜绝路径穿越攻击。
* **会话级物理隔离**：每次新对话创建时都会生成唯一的 `thread_id`，并创建独立的沙盒目录 `app/output/session_{thread_id}`。每次任务执行时关联的上传文件和最终报告均落入该独立文件夹，避免多用户高并发时文件被覆盖或越权读取。


## 参考说明
https://didilili.github.io/ai-agents-from-zero  参考学习开源教程，在此基础上做的学习开发修改