"""
╔══════════════════════════════════════════════════════════════════════╗
║  文件：tools/tavily_tool.py                                            ║
║  角色：网络搜索工具——让 Agent 能联网搜公开信息                          ║
║  JS 类比：≈ src/tools/tavilySearch.ts                                  ║
║  被谁用：agent/subagents/network_search_agent.py 的 tools 列表         ║
╚══════════════════════════════════════════════════════════════════════╝

📖 语法速览（前端工程师版 · @tool 装饰器是重点）：
  - @tool                              ← 装饰器！把普通函数变成模型可调用的工具
  - def internet_search(query: str):  ← 函数签名 + type hint（参数类型注解）
  - topic: Literal["news", ...]       ← Literal 类型：只能是这三个值之一（类似 TS 的 union type）
  - max_results: int = 5              ← 默认参数（JS 也有）
  - @retry_with_backoff(...)          ← 另一个装饰器：自动重试
  - from typing import Literal        ← Python 的类型注解库（≈ TS 的 type）

🎯 读完你应该能说清：
  1. @tool 装饰器到底做了什么？（提示：函数 docstring 变成模型能读的工具说明，参数 type hint 变成 schema）
  2. 为什么要套一个 _search_with_retry？（提示：网络请求容易失败，需要自动重试）
  3. monitor.report_tool 是干嘛的？（提示：推给前端进度）

💡 @tool 的工作原理（deep dive）：
  当你写：
    @tool
    def internet_search(query: str, max_results: int = 5):
      """搜索公开网络信息"""
      ...
  deepagents/langchain 框架会自动：
    1. 读函数 docstring 作为工具的 description（模型用它判断要不要调我）
    2. 读参数的 type hint 生成 JSON Schema（模型知道每个参数是什么类型）
    3. 把这个函数注册进 Agent 的可调用工具列表
  模型输出 tool_calls = [{ name: "internet_search", args: { query: "..." } }]
  框架就会自动调用这个函数并传入参数！
"""

# ── 导入依赖 ────────────────────────────────────────────────────────────────
# 💡 JS 类比：import { Literal } from 'types' （但 Python 的 typing 是内置库）
from typing import Literal

# 💡 JS 类比：import { tool } from '@langchain/langchain'
from langchain_core.tools import tool

# 💡 JS 类比：import TavilyClient from 'tavily-client'
# Tavily 是专门给 AI Agent 用的搜索引擎（比 Google/Bing 的 API 更友好）
from tavily import TavilyClient

# 💡 JS 类比：import os from 'node:os'; import dotenv from 'dotenv'
import os
from dotenv import load_dotenv

# 💡 JS 类比：import { monitor } from '../api/monitor'
from api.monitor import monitor

# 💡 JS 类比：import { retryWithBackoff } from '../utils/retry'
from utils.retry import retry_with_backoff


# ── 加载 .env ───────────────────────────────────────────────────────────────
load_dotenv()

# ── 创建 Tavily 客户端 ──────────────────────────────────────────────────────
# 💡 JS 类比：const tavilyClient = new TavilyClient({ apiKey: process.env.TAVILY_API_KEY })
tavily_client = TavilyClient(
    api_key=os.getenv("TAVILY_API_KEY"),
)


# ═══════════════════════════════════════════════════════════════════════════
# 带重试的搜索封装（内部函数，不直接暴露给 Agent）
# ═══════════════════════════════════════════════════════════════════════════
# 💡 JS 类比：
#   const _searchWithRetry = retryWithBackoff(async (query, topic, maxResults, includeRawContent) => {
#     return tavilyClient.search({ query, topic, max_results: maxResults, include_raw_content: includeRawContent });
#   }, { maxRetries: 3, baseDelay: 1, maxDelay: 10 });
#
# 💡 语法点：@retry_with_backoff 是装饰器，把函数包装一层：
#   调用时自动重试 3 次，退避时间 1s → 2s → 4s → 8s → 10s（封顶）
#   网络抖动时自动重试，避免整个 Agent 任务因为一次搜索失败而中断
@retry_with_backoff(
    max_retries=3,
    base_delay=1.0,
    max_delay=10.0,
    exceptions=(Exception,),
)
def _search_with_retry(query: str, topic: str, max_results: int, include_raw_content: bool):
    """
    对 Tavily 搜索调用包装指数退避重试。
    网络抖动或 Tavily 临时不可用时自动重试，最多 3 次。

    💡 为什么函数名以 _ 开头？Python 约定：单下划线开头是内部函数，不对外导出
    """
    return tavily_client.search(
        query=query,
        topic=topic,
        max_results=max_results,
        include_raw_content=include_raw_content,
    )


# ═══════════════════════════════════════════════════════════════════════════
# LangChain 工具定义（这个才是真正暴露给 Agent 的！）
# ═══════════════════════════════════════════════════════════════════════════
# 💡 JS 类比：
#   export const internetSearch = tool({
#     name: 'internet_search',
#     description: '根据用户问题进行网络信息搜索...',
#     schema: z.object({
#       query: z.string(),
#       topic: z.enum(['news', 'finance', 'general']),
#       max_results: z.number().int().default(5),
#       include_raw_content: z.boolean().default(false),
#     }),
#     execute: async ({ query, topic, max_results, include_raw_content }) => { ... }
#   });
#
# 💡 @tool 装饰器自动从函数签名和 docstring 里推断出 name / description / schema
# 也就是说：你只写普通 Python 函数，框架自动帮你变成 Agent 可调用的工具！
@tool
def internet_search(
    query: str,                                                    # 必选：搜索关键词
    topic: Literal["news", "finance", "general"] = "general",      # 可选：搜索主题（Literal 限定值）
    max_results: int = 5,                                          # 可选：最多返回几条
    include_raw_content: bool = False,                             # 可选：是否返回原文摘要
):
    """
    根据用户问题，进行网络信息搜索！
    注意：主要搜索公开的网络信息！如果指定查询数据库或者rag不能使用此工具！

    💡 docstring 会被 deepagents 框架自动解析成工具的 description
       模型就是靠这段文字判断「我要不要调用 internet_search」

    Args:
        query: 用户的查询信息
        topic: 查询的类型 (general/news/finance)
        max_results: 返回的最大条数
        include_raw_content: 是否返回原内容 False 精简 True 详细

    Returns:
        dict: Tavily 搜索结果（含 answer、results 列表等）
    """
    # 💡 JS 类比：wsManager.emit('tool_start', { name: '网络搜索工具', args: {...} })
    # 每次工具被调用，都推给前端一个进度事件
    monitor.report_tool(
        tool_name="网络搜索工具",
        args={
            "query": query,
            "topic": topic,
            "max_results": max_results,
            "include_raw_content": include_raw_content,
        },
    )

    # 💡 真正的搜索调用（带重试）
    return _search_with_retry(
        query=query,
        topic=topic,
        max_results=max_results,
        include_raw_content=include_raw_content,
    )
