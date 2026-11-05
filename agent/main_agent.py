"""
╔══════════════════════════════════════════════════════════════════════════╗
║  文件：agent/main_agent.py                                                ║
║  角色：多智能体调度中心！主 Agent 在这里创建、在这里运行                    ║
║  JS 类比：≈ src/core/orchestrator.ts（但 Python 这个是真正的 Agent 框架）   ║
║  被谁用：api/server.py 的 /api/task 接口调 run_deep_agent                  ║
╚══════════════════════════════════════════════════════════════════════════╝

📖 语法速览（前端工程师版 · 这份文件最重要）：
  - from xxx import yyy, zzz   ≈ JS 的 import { yyy, zzz } from 'xxx'
  - from xxx import *          ≈ JS 的 import * as xxx from 'xxx'
  - async def 函数名():       ≈ JS 的 async function 函数名() {}
  - await 表达式              ≈ JS 的 await 表达式（几乎一模一样）
  - async for item in stream:  ≈ JS 的 for await (const item of stream)
  - with ... as ...:          ≈ JS 的 try/finally（自动清理资源）
  - try: ... except Exception as e:  ≈ JS 的 try { } catch (e) { }
  - try: ... finally:          ≈ JS 的 try { } finally { }
  - { } 字典 = JS 的 Object    ≈ { "key": "val" }
  - [ ] 列表 = JS 的 Array    ≈ [item1, item2]
  - .parents[1]               ≈ path.resolve(__dirname, '..')

🎯 读完这份文件你应该能说清（W4-W5 的任务）：
  1. main_agent 是怎么创建的？哪 4 个参数？
  2. run_deep_agent 函数的执行流程？（画图！）
  3. 主 Agent 怎么知道什么时候调子 Agent？（提示：看 main_agent.astream 里的 tool_call 解析）
  4. SQLite checkpointer 干嘛的？重启后还能记住对话吗？

💡 调用链路（从头到尾）：
  用户提问 → POST /api/task → asyncio.create_task(run_deep_agent)
           → main_agent.astream（流式执行）
           → 模型决定：调工具？调子 Agent？给最终答案？
           → monitor.report_xxx 通过 WebSocket 推给前端
"""

# ═══════════════════════════════════════════════════════════════════════════
# 【导入区】把所有需要的模块先 import 进来
# ═══════════════════════════════════════════════════════════════════════════

# ── 子智能体（三个纯配置字典）──
# 💡 JS 类比：import { knowledgeBaseAgent } from './subagents/knowledgeBaseAgent'
from agent.subagents.knowledge_base_agent import knowledge_base_agent
from agent.subagents.database_query_agent import database_query_agent
from agent.subagents.network_search_agent import network_search_agent

# ── LangGraph 状态图的持久化存储 ──
# 💡 JS 类比：把对话历史存到 SQLite（而不是每次重启都丢）
# SqliteSaver 是 LangGraph 内置的 checkpointer，用 SQLite 实现多轮对话记忆
from langgraph.checkpoint.sqlite import SqliteSaver
import sqlite3

# ── 主 Agent 自己的工具（和子 Agent 的工具不一样！）──
# 💡 JS 类比：import { generateMarkdown } from '../tools/markdown'
# 主 Agent 自己也能干活：生成 Markdown、转 PDF、读文件
from tools.markdown_tools import generate_markdown
from tools.pdf_tools import convert_md_to_pdf
from tools.upload_file_read_tool import read_file_content

# ── deepagents 框架的核心函数 ──
# 💡 JS 类比：import { createDeepAgent } from 'deepagents'
# 这个函数负责把「模型 + 提示词 + 工具 + 子 Agent」组装成一个可运行的 Agent
from deepagents import create_deep_agent

# ── 我们自己的大模型实例和主 Agent 提示词 ──
# 💡 JS 类比：import { model } from './llm'; import { mainAgentContent } from './prompts'
from agent.llm import model
from agent.prompts import main_agent_content

# ── WebSocket 监控器（用来给前端推进度）──
# 💡 JS 类比：import { monitor } from '../api/monitor'
# monitor.report_tool / report_assistant / report_task_result 都是通过它推给前端的
from api.monitor import monitor

# ── Python 标准库 ──
# 💡 JS 类比：import * as uuid from 'uuid'; import path from 'path'
import asyncio     # 异步编程核心库
import uuid        # 生成唯一 ID（session_id 用它）
import shutil      # 文件复制、移动
from pathlib import Path  # 优雅的路径操作

# ── 上下文变量（每个请求独立隔离的全局变量）──
# 💡 JS 类比：每个请求的 React Context（但这里是 Python async 场景）
from api.context import set_session_context, reset_session_context, set_thread_context

# ── LangChain 消息类型 ──
# 💡 JS 类比：import { AIMessage } from '@langchain/langchain'
# 用来判断模型输出里有没有 tool_calls
from langchain_core.messages import AIMessage


# ═══════════════════════════════════════════════════════════════════════════
# 【持久化】用 SQLite 存对话历史，服务重启后不丢
# ═══════════════════════════════════════════════════════════════════════════
# 💡 JS 类比：const conn = new Database('data/checkpoints.db')
#
# 为什么需要这个？
#   1. 用户第一次问：「你好」→ Agent 记住了
#   2. 用户第二次问：「刚才说了啥」→ Agent 应该能引用上一轮
#   3. 没持久化的话，服务一重启，所有对话历史清零
#
# 目录结构：
#   project_root / data / checkpoints.db   ← SQLite 文件
checkpoint_db_path = Path(__file__).parents[1] / "data" / "checkpoints.db"
checkpoint_db_path.parent.mkdir(parents=True, exist_ok=True)  # 确保 data 目录存在

# 💡 JS 类比：const conn = sqlite3.open(str(checkpointDbPath))
# check_same_thread=False 允许多线程共享（Async 场景需要）
_conn = sqlite3.connect(str(checkpoint_db_path), check_same_thread=False)

# 💡 JS 类比：const checkpointer = new SqliteSaver(conn)
# 这个对象会被传给 deep_agent，每次对话自动存/读
checkpointer = SqliteSaver(_conn)


# ═══════════════════════════════════════════════════════════════════════════
# 【创建主 Agent】核心装配点
# ═══════════════════════════════════════════════════════════════════════════
# 💡 JS 类比：
#   const mainAgent = createDeepAgent({
#     model,                        // 用哪个大模型
#     system_prompt,                // 主 Agent 的身份设定
#     tools,                        // 它自己能直接调用的工具
#     checkpointer,                 // 对话历史存哪
#     subagents                     // 可以调度的子 Agent 列表
#   })
#
# 五个参数的含义：
#   model            —— 大模型实例（deepseek-chat）
#   system_prompt    —— 主 Agent 的「人设」（从 YAML 读的）
#   tools            —— 主 Agent 自己的工具（生成 Markdown、转 PDF、读文件）
#   checkpointer     —— 对话历史持久化
#   subagents        —— 三个子 Agent（搜索、查库、知识库）
main_agent = create_deep_agent(
   model = model,
   system_prompt = main_agent_content['system_prompt'],
   tools = [generate_markdown, convert_md_to_pdf, read_file_content],  # 主 Agent 自己的工具
   checkpointer = checkpointer,
   subagents = [
       database_query_agent,      # 数据分析助手
       network_search_agent,      # 市场情报助手
       knowledge_base_agent       # 内部知识助手
   ]
)


# ═══════════════════════════════════════════════════════════════════════════
# 【执行】主 Agent 的异步执行入口
# ═══════════════════════════════════════════════════════════════════════════
# 💡 JS 类比：
#   async function runDeepAgent(taskQuery, sessionId) {
#     // 创建会话目录
#     const sessionDir = path.resolve(projectRoot, 'output', `session_${sessionId}`);
#     fs.mkdirSync(sessionDir, { recursive: true });
#
#     // 遍历模型输出的每个 chunk（流式）
#     for await (const chunk of mainAgent.astream({ messages: [...] }, config)) {
#       // 判断是工具调用？子 Agent 调用？还是最终结果？
#       // 通过 WebSocket 推给前端
#     }
#   }
#
# 💡 async def 和 JS async function 几乎完全一样！
# 💡 await 和 JS await 也完全一样！
# 💡 async for chunk in stream 和 JS 的 for await (const chunk of stream) 完全一样！
#
# 🔑 为什么要 async？
#   1. 多个用户同时请求时，不会互相阻塞
#   2. main_agent.astream 是流式输出（token 逐字生成），必须用 async 处理
async def run_deep_agent(task_query, session_id):
    """
    定义流式+异步执行主智能体！！

    执行过程中会产生三类事件，都通过 monitor 推给前端：
      1. 会话文件目录创建 → monitor.report_session_dir
      2. 子智能体被调用   → monitor.report_assistant
      3. 最终结果返回     → monitor.report_task_result

    Args:
        task_query: 前端提问的问题（用户输入）
        session_id: 每个前端会话对应的标识（UUID，用来隔离不同用户）
    """
    print(f"当前会话的main_agent开始执行了！ 会话id:{session_id}")

    # ── Step 1：准备工作目录 ────────────────────────────────────────────────────
    # 💡 JS 类比：
    #   const sessionDir = path.resolve(projectRoot, 'output', `session_${sessionId}`);
    #   fs.mkdirSync(sessionDir, { recursive: true });
    session_dir = project_root_path / "output" / f"session_{session_id}"
    session_dir.mkdir(parents=True, exist_ok=True)  # 不存在就创建，存在也不报错

    # 💡 JS 类比：sessionDirStr.replace(/\\\\/g, '/')
    # Windows 下 Path 转字符串会带反斜杠 \，大模型提示词里统一用正斜杠 /
    session_dir_str = str(session_dir).replace("\\", "/")

    # 💡 JS 类比：sessionDir.relativeTo(projectRoot)  // 得到相对路径
    # 大模型提示词里告诉它「工作目录是 /output/session_xxx」，它就知道文件存哪
    relative_session_dir_str = str(session_dir.relative_to(project_root_path)).replace("\\", "/")


    # ── Step 2：处理用户上传的文件 ─────────────────────────────────────────────
    # 用户可能上传了文档（.docx/.pdf/.xlsx），Agent 需要先分析这些文件
    # 💡 JS 类比：
    #   const updatedDir = path.resolve(projectRoot, 'updated', `session_${sessionId}`);
    #   if (fs.existsSync(updatedDir)) {
    #     // 把上传的文件复制到 session 目录（统一入口）
    #     // 告诉大模型：这些文件已加载，你要先读它们
    #   }
    updated_dir_path = project_root_path / "updated" / f"session_{session_id}"
    updated_info_prompt = ""  # 有上传文件时，后面拼接这个提示词

    if updated_dir_path.exists():
        # 💡 JS 类比：[...updatedDir.iterdir()].filter(f => f.isFile()).map(f => f.name)
        files = [f.name for f in updated_dir_path.iterdir() if f.is_file()]

        if files:
            # 💡 JS 类比：fs.copyFileSync(src, dest)
            # 把上传文件复制到 session 目录，前端统一从 output/session_xxx 读
            for filename in files:
                shutil.copy2(updated_dir_path / filename, session_dir / filename)

            # 💡 JS 类比：`\n    [已上传文件] 已加载到工作目录:\n${files.map(...)}\n    ...`
            # 拼一段提示词，告诉大模型「这些文件已加载，你要先读它们」
            updated_info_prompt = (
                f"\n    [已上传文件] 已加载到工作目录:\n" +
                "\n".join([f"    - {f}" for f in files]) +
                "\n    请优先使用工具（read_file_content）读取并参考这些文件。"
            )


    # ── Step 3：设置上下文变量（让工具能知道当前会话是谁） ──────────────────────
    # 💡 JS 类比：React Context（但 Python 这个是协程级隔离）
    #
    # 为什么需要这个？
    #   Agent 调用工具时（比如 generate_markdown），工具需要知道文件存哪
    #   但工具函数不应该每个都传 session_dir 参数（太烦）
    #   用 ContextVar 存起来，任何深度的函数都能直接 get() 到
    session_dir_token = set_session_context(session_dir_str)   # 存当前会话的文件目录
    session_id_token = set_thread_context(session_id)         # 存当前会话的 thread_id（WebSocket 定向推送用）

    # 💡 JS 类比：wsManager.emit('session_created', sessionDir)
    # 把会话目录告诉前端，前端可以在浏览器里实时看到生成的文件
    monitor.report_session_dir(session_dir_str)


    # ── Step 4：执行主 Agent（核心循环） ────────────────────────────────────────
    # 💡 JS 类比：
    #   for await (const chunk of mainAgent.astream({ messages: [...] }, config)) {
    #     for (const [nodeName, state] of Object.entries(chunk)) { ... }
    #   }
    #
    # deep_agent.astream 返回的是一个异步生成器，每次 yield 一个 chunk（字典）
    # chunk 长这样：{ "model": { messages: [...] } } 或 { "tools": { ... } }
    # 我们关心 node_name == "model"，因为模型的 tool_calls 就在里面
    config = {
        "configurable": {
            "thread_id": session_id  # checkpointer 用这个 ID 区分不同对话
        }
    }

    # 💡 提示词拼接：告诉大模型「工作目录是啥、文件存哪、读文件用什么工具」
    path_instruction = f"""
    【工作环境指令】
    工作目录: {relative_session_dir_str}
    {updated_info_prompt}

    规则：
    1. 新生成文件必须保存到工作目录：'{relative_session_str}/filename'
    2. 读取已上传的文件时，直接传文件名给 read_file_content，不要带目录前缀
    3. 使用相对路径，禁止使用绝对路径
    4. 若存在上传文件，请先分析内容
    """

    try:
        # 💡 async for 和 JS 的 for await 完全一样！
        # 每收到一个 chunk，我们就解析：模型是在想调用工具？调子 Agent？还是给最终答案？
        async for chunk in main_agent.astream(
            {
                "messages": [
                    {
                        "role": "user",         # role 可选：system / user / assistant / tool
                        "content": task_query + path_instruction  # 用户问题 + 环境指令
                    }
                ]
            },
            config=config
        ):
            # 💡 JS 类比：for (const [nodeName, state] of Object.entries(chunk))
            for node_name, state in chunk.items():
                if not state or "messages" not in state:
                    continue

                messages = state["messages"]
                if messages and isinstance(messages, list):
                    last_msg = messages[-1]  # 取最后一条消息（最新的）

                    # ── 情况 A：模型决定调子 Agent 或调工具 ──────────────────────────
                    if node_name == 'model':
                        if last_msg.tool_calls:
                            # 💡 tool_calls 是什么？OpenAI Function Calling 协议！
                            # 模型不直接执行代码，而是输出一个 JSON：
                            #   tool_call = {
                            #     name: "task",                    // 要调什么（task = 调子 Agent）
                            #     args: {
                            #       subagent_type: "市场情报助手",   // 调哪个子 Agent
                            #       description: "搜索竞品动态"      // 子 Agent 的任务描述
                            #     }
                            #   }
                            # deep_agent 框架读到这个 JSON，自动调度对应的子 Agent
                            for tool_call in last_msg.tool_calls:
                                if tool_call['name'] == 'task':
                                    # 💡 JS 类比：monitor.emit('assistant_call', { name: subagentName, ... })
                                    # 通过 WebSocket 告诉前端：正在调某个子 Agent
                                    monitor.report_assistant(
                                        tool_call['args']['subagent_type'],
                                        {'description': tool_call['args']['description']}
                                    )

                        # ── 情况 B：模型给出了最终文本回答 ─────────────────────────────
                        elif last_msg.content:
                            print(f"主智能体执行结果，最终结果：{last_msg.content[:100]}")
                            monitor.report_task_result(last_msg.content)

    except Exception as e:
        # 💡 JS 类比：catch (e) { ws.emit('error', e.message) }
        # 任何异常都推给前端，而不是让用户一脸懵
        monitor._emit("error", f"执行主智能发生异常信息：{str(e)}")

    finally:
        # 💡 JS 类比：finally { cleanup() }
        # 无论成功还是失败，最后都要清理上下文变量（防止内存泄漏和请求串台）
        reset_session_context(session_dir_token, session_id_token)
