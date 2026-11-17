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
