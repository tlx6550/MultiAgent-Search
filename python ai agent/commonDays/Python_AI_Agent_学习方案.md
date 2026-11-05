# Python + AI Agent 学习作战方案

> 角色：**首席战略官（Naval 思维）× 跨领域知识整合教练**
> 定制依据：你手上的真实项目 **MultiAgent-Search**（多智能体搜索系统）
> 你的背景：理科二本 / 前端工程师（Vue）｜目标：1–2 个月掌握 Python 并真实部署 AI Agent｜每日 1 小时

---

## 0. 战略总纲（Naval 视角）

- **杠杆思维**：代码是普通人能撬动的最强杠杆之一；AI Agent 是当前复利最高的方向。你已握有 Vue 这把前端杠杆，再加 Python 后端 + Agent，就凑成了「前端+AI 后端」全栈杠杆。
- **具体知识（Specific Knowledge）**：不是背证书，而是从真实项目里长出来的能力。本项目就是最好的「具体知识」训练场。
- **直接学习原则（Scott Young）**：别先啃完 20 门课再动手，直接做能跑起来的 Agent。每天 1 小时，连续 30–60 天，知识会**复利**。
- **反向思考**：不追求「学完」，追求「能做出来并部署上线」。学不会的地方就降级、绕路、先跑通主干。
- **长期游戏**：今天写的每一行代码，都是 5 年后你的护城河。

---

## 1. 项目知识点地图（按学习顺序）

> 可视化思维导图：**`知识地图_思维导图.html`**（浏览器打开，含项目坐标与验收动作）。文字版（带优先级）如下，建议**严格按 L0→L4 顺序**学，因为后一层依赖前一层。

### L0 基础层 · Python（第 1–2 周，先打底）
- 语法：变量、数据类型、函数、**类与装饰器**（项目里 `@tool` 就是装饰器）
- 异步：`async` / `await` / `asyncio`（项目大量用异步流式输出，这是前端最该补的一课）
- 工程化：**虚拟环境 venv**、`pip`、`requirements.txt`、`.env`
- 文件与路径：`pathlib`、`os`
- 配置：`python-dotenv`、`yaml`
- 进阶：`typing` 类型注解、`tenacity` 重试、`contextvars`（多会话隔离，对应你 Vue 里的「每个标签页一个会话」）

### L1 后端层 · FastAPI（第 3 周）
- 路由、`Pydantic` 数据模型
- **WebSocket 实时推送**（项目前端靠它收流式结果——这是你 Vue 经验的主场）
- 中间件 CORS、文件上传 `UploadFile`
- `uvicorn` 启动、异步服务

### L2 核心层 · AI Agent（第 4–6 周，**重点**）
- LLM 接入：`langchain.init_chat_model`，**OpenAI 兼容协议**
- 国内大模型：通义千问 Qwen / DeepSeek（本项目用环境变量 `LLM_QWEN_MAX`）
- **Function Calling / Tools**：`@tool` 装饰器把普通函数变成 Agent 可调用工具
- Agent 框架：`deepagents.create_deep_agent`
- **多 Agent 编排**：主 Agent + 子 Agent（搜索 / 知识库 / 数据库）
- 工作流持久化：`langgraph` + `SqliteSaver` checkpointer（对话历史不丢失）
- 流式输出：`astream` 异步流式
- 提示词工程：`system_prompt`、yaml 配置

### L3 能力层 · 外部工具（第 7 周）
- 联网搜索：**Tavily**（`tavily-python`）
- 知识库 / RAG：**RAGFlow**（`ragflow_sdk`）
- 数据库工具：`mysql-connector-python`
- 文档处理：Markdown、PDF（Windows 走 Word COM，跨平台可 WeasyPrint）

### L4 落地层 · 生产部署（国情，第 8 周+）
- 国内大模型 API 选型（阿里云百炼/通义、DeepSeek、智谱、火山方舟）
- 容器化：**Docker / docker-compose**（项目已自带 `Dockerfile`、`docker-compose.yml`）
- 前端对接：Vue 通过 WebSocket 接收流式结果
- 合规：数据不出境、API Key 走环境变量、敏感信息脱敏

---

## 2. 学习方法论（四件武器）

### 2.1 Naval 思维
- 具体知识来自真实好奇 + 动手实践，不是照本宣科。
- 玩长期游戏：今天学的代码是 5 年后的复利。
- **想成为 Agent 工程师，就每天都像 Agent 工程师一样写代码**（哪怕只写 10 行）。

### 2.2 费曼学习法（每学一个概念就做一遍）
1. 用大白话把这个概念讲给一个外行听。
2. 卡壳的地方 = 知识漏洞，立刻回去补。
3. 用类比：Agent ≈ 会打电话的秘书；Tool ≈ 秘书能打开用的 App；多 Agent ≈ 一个团队。
4. 简化到「一句话能说清」。

### 2.3 刻意练习（Anders Ericsson）
- **目标具体**：不是「学 Python」，而是「今天写出一个能调 LLM 的 @tool」。
- **走出舒适区**：每次加一点难度（语法 → 异步 → Agent → 部署）。
- **即时反馈**：代码跑起来、报错即反馈、流式输出肉眼可见。
- **建立心理表征**：多读优秀代码——**本项目就是现成范本**。

### 2.4 《如何高效学习》（Scott Young）
- **直接原则**：直接做真实任务，不绕弯路（直接复刻本项目，而不是先刷完 Python 全栈课）。
- **高频自测**：每天用 10 分钟小练习自测。
- **比喻/组块**：把新知识和 Vue 经验挂钩（WebSocket ≈ 前端 SSE / Socket；异步 ≈ JS 的 Promise/async）。
- **过量学习**：在「会了」的基础上多做 10%，形成肌肉记忆。

---

## 3. 1–2 个月总体路线图

| 阶段 | 周次 | 目标 | 当日可验收 |
|---|---|---|---|
| 打底 | W1–2 | Python 语法 + 异步 + 环境 | 写出异步脚本、跑通 venv |
| 后端 | W3 | FastAPI + WebSocket | 写个 WebSocket 回声服务 |
| Agent 核心 | W4–6 | LLM + Tools + 多 Agent | 复刻本项目主 Agent 骨架 |
| 外部能力 | W7 | Tavily / RAGFlow / MySQL | 接一个真实工具跑通 |
| 生产落地 | W8 | Docker + 国内云部署 | 本地 `docker compose up` 跑起来 |
| 综合实战 | W9–（延长到 2 月） | 完整复刻项目 | Vue 前端 + Agent 后端打通流式对话 |

**每日 1 小时分配**：20 分钟看（文档/视频）+ 30 分钟写（动手练）+ 10 分钟费曼复盘（写一句话笔记）。

---

## 4. 今日执行方案（Day 1）

> ⚠️ **重要：不要通读整个项目！** 先按下面步骤动手，遇到看不懂的再回来翻。原因：
> - 10 分钟读不完所有文件（光 main_agent.py 就 200 行+）
> - 先动手你才有「我缺什么知识」的体感，带着问题读才高效
> - 所有源码已加好教学注释（文件头 + 每个函数的 JS 类比 + 语法翻译），直接翻就行

### 看什么（10 min · 只读 2 个文件）
- **⚠️ 不要扩展！就这两个文件！**
- 每个文件顶部都有「文件概览 + 语法速览 + 读完应该能说清」，直接照着看：
  1. `agent/llm.py`（现在约 60 行，含教学注释）：模型怎么初始化，环境变量怎么读
  2. `agent/subagents/network_search_agent.py`（现在约 50 行，含教学注释）：子智能体就是一个 dict！
- 带着一个问题看：**子智能体到底是什么？**（答案：`{ name, description, system_prompt, tools }` 四字段字典）
- 💡 看不懂的语法？看每个文件顶部的「📖 语法速览」和「JS 类比」，都给你标出来了

### 做什么（35 min · 5 个 TODO）
- 环境已就绪：本项目已用 Python 3.13 建好 `.venv`，直接使用：
  ```powershell
  .\.venv\Scripts\python.exe "python ai agent\今日练习_python基础与Agent入门.py"
  ```
- 打开 `今日练习_python基础与Agent入门.py`，依次完成 5 个 TODO：
  1. `load_config`：读取 YAML
  2. `list_subagents`：字典遍历，列出 3 个子智能体
  3. `route_query`：关键词路由，模拟主智能体决策
  4. `build_tool_call`：构造 OpenAI 风格 tool_call
  5. `run_mock_agent`：async/await 模拟流式执行
- 卡住超过 10 分钟再看 `参考实现_day1.py`，看完关掉，凭记忆重写。

### 怎么验收（15 min）
```powershell
.\.venv\Scripts\python.exe "python ai agent\验收_day1.py"
```
- [ ] 输出 `6/6 PASS`。
- [ ] 能脱稿说清：子智能体 = 一个字典；`@tool` = 把普通函数变成模型能调用的工具。
- [ ] 填写 `费曼学习笔记_模板.md` 的 3 句话 + 1 个类比，并录 60 秒语音。
- [ ] 把当天文件归档到项目根目录「python ai agent」文件夹，标记 **Day 1 完成**。

> 想先验证验收脚本本身是否可靠，可运行：
> `.\.venv\Scripts\python.exe "python ai agent\验收_day1.py" --file "参考实现_day1.py"`

---

## 5. 国内落地资源与合规（结合国情）

- **大模型 API**：阿里云百炼（通义千问）、DeepSeek 开放平台、智谱 AI、火山方舟（豆包）。本项目用 `LLM_QWEN_MAX` 即通义，已是最佳起点。
- **知识库 / RAG**：RAGFlow（开源、可自托管，契合本项目）、Dify（国产低代码 Agent 平台）。
- **部署**：阿里云 / 腾讯云轻量应用服务器 + Docker；或 Sealos 等国产容器平台。
- **合规红线**：勿把敏感数据发到境外 API；Key 一律走环境变量（`.env`，不进代码、不进 git）；前端 WebSocket 务必加鉴权。

---

## 6. 总验收标准（1–2 个月后你应能…）

- [ ] 独立从 0 写一个 FastAPI 服务
- [ ] 接入国内 LLM 并写出 `@tool` 工具
- [ ] 用 `deepagents` / `langgraph` 搭多 Agent
- [ ] 用 Docker 部署，并让 Vue 前端调通流式对话
- [ ] 全部笔记与练习沉淀在「python ai agent」云端文件夹，随时回头看

> 记住 Naval 那句：**手段（学习资源）从来不缺，缺的是学习的欲望。** 你每天那 1 小时，就是给未来的自己存的复利。
