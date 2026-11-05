# 项目长期记忆（MultiAgent-Search）

## 用户约定 / 红线
- `python ai agent/` 文件夹是**用户自己的学习笔记**，任何情况下都不要读取、修改、移动、删除或重构其中内容，也绝不往里面写东西。
- WorkBuddy 生成的学习资料/练习产物统一放到项目根目录的 `workbuddy_学习产出/`，**按天分子目录**：`day1/`、`day2/`、`day3/` …（每新增一天就新建一个 `dayN` 子目录）。两者严格隔离。
- **云端一律不做任何改动**：资料库文件夹「python ai agent」保持现状，不增删改、不重新组织、不上传。所有修改只在本地进行。

## 项目背景
- 项目：MultiAgent-Search（多智能体搜索系统）。技术栈：FastAPI + deepagents/langgraph + langchain + RAGFlow(ragflow-sdk) + Tavily + MySQL + WebSocket。
- LLM 走 OpenAI 兼容协议，模型名由环境变量 `LLM_QWEN_MAX`（国内通义千问）指定。
- 依赖修复记录：`ragflow-sdk==0.26.0`、`beartype==0.23.1`、`langgraph-checkpoint==4.3.1`、新增 `langgraph-checkpoint-sqlite==3.1.2`。
- 虚拟环境：`.venv`（Python 3.13），启动 `python api/server.py`（0.0.0.0:8000）。

## 云端学习资料（只读，不改动）
- 资料库文件夹「python ai agent」：https://www.workbuddy.cn/space/d/6taOho9lSdvVoXeibpUUJa
