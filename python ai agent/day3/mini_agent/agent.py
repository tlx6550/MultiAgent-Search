"""
╔══════════════════════════════════════════════════════════════════════╗
║  文件：day3/mini_agent/agent.py                                        ║
║  角色：迷你包里的「Agent 模块」——组合工具执行任务                       ║
║  JS 类比：≈ src/agent/index.ts（依赖 tools 模块）                        ║
║  状态：已给好，不用改                                                   ║
╚══════════════════════════════════════════════════════════════════════╝

📖 这个文件演示「模块之间怎么互相引用」：
  - 这是包内相对导入：from .tools import search_tool
  - 点号 . 表示「当前包」，≈ JS 的 './tools' 或 '@/tools'
  - 项目里 agent/subagents/network_search_agent.py 就是这么写的：
      from tools.tavily_tool import internet_search
"""
#===
# 让类型注解（冒号后面写的类型）延迟到整个模块加载完才求值——解决了三个经典痛点：前向引用、导入循环、默认值写类型。
# def search(query: str) -> list[str]:    # ← str、list[str] 就是类型注解
#     ...

# from dataclasses import dataclass
# @dataclass
# class Agent:
#     name: str                             # ← str 是类型注解
#     tools: list[str] = []                 # ← list[str] 是类型注解


# # ❌ 没有 __future__ import：报错！
# from dataclasses import dataclass

# @dataclass
# class Agent:
#     name: str
#     sub_agent: Agent | None = None   # ← Agent 这个类还没定义完，就引用了自己！
#                                      # NameError: name 'Agent' is not defined
# ✅ 有 __future__ import：延迟求值，等类定义完再回头算类型
# from __future__ import annotations

# @dataclass
# class Agent:
#     name: str
#     sub_agent: Agent | None = None   # ✅ 正确！


# # tool.py
# from agent import Agent    # ← 需要 Agent 类型

# class Tool:
#     owner: Agent           # ← 引用 Agent

# # agent.py
# from tool import Tool      # ← 需要 Tool 类型

# class Agent:
#     tools: list[Tool]      # ← 引用 Tool

#===
from __future__ import annotations

# 💡 相对导入：.tools 表示同一个包（mini_agent）下的 tools 模块
#    JS 类比：import { searchTool } from './tools'
#    注意：相对导入只能在「包内」使用，不能在被直接运行的脚本里用
from .tools import search_tool, db_tool


async def quick_answer(question: str) -> str:
    """
    一个最小的 Agent：根据问题关键词挑一个工具，执行并返回结果。

    💡 JS 类比：
        async function quickAnswer(question) {
          if (question.includes('销量')) return await dbTool(question);
          return await searchTool(question);
        }

    Args:
        question: 用户问题

    Returns:
        str: 工具执行结果
    """
    # 💡 简单的关键词路由（Day 1 已经练过这个思路）
    if "销量" in question or "库存" in question:
        return await db_tool(question)

    return await search_tool(question)
