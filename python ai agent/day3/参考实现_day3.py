"""
╔══════════════════════════════════════════════════════════════════════╗
║  Day 3 参考实现（仅供参考！自己先写，卡住 10 分钟再看）                   ║
╠══════════════════════════════════════════════════════════════════════╣
║  使用方式：                                                             ║
║    1. 先自己写 今日练习_异步编程与模块化.py                             ║
║    2. 卡住超过 10 分钟再看这里                                          ║
║    3. 看完关掉，凭记忆重写一遍                                          ║
║    4. 验收通过后，再回来对照看为什么这样写                               ║
╚══════════════════════════════════════════════════════════════════════╝

⚠️ TODO 4 的答案不在本文件里！你要改的是 mini_agent/__init__.py。
   正确内容如下（复制到 mini_agent/__init__.py 底部）：

────────────────────────── 复制开始 ──────────────────────────
from .tools import search_tool, db_tool, rag_tool
from .agent import quick_answer

__all__ = ["search_tool", "db_tool", "rag_tool", "quick_answer"]
────────────────────────── 复制结束 ──────────────────────────

💡 为什要用相对导入（from .tools）而不是绝对导入（from mini_agent.tools）？
   相对导入跟着包走，包改名不用改所有文件；绝对导入更明确但耦合了包名。
   项目里 agent/subagents/network_search_agent.py 用的是绝对导入
   （from tools.tavily_tool import internet_search），因为项目根在 sys.path 里。
   两种都能用，包内互相引用推荐相对导入。
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from typing import Literal, AsyncIterator


# ═══════════════════════════════════════════════════════════════════════════
# TODO 1：asyncio.gather 并发
# ═══════════════════════════════════════════════════════════════════════════
async def call_subagent(name: str, seconds: float = 0.1) -> str:
    """模拟调用一个子 Agent。"""
    await asyncio.sleep(seconds)
    return f"{name} 完成"


async def run_parallel(names: list[str]) -> list[str]:
    """并发调用多个子 Agent，结果顺序与 names 一致。"""
    # 第一步：用列表推导式造出「协程对象」列表（注意：此时还没开始执行）
    coros = [call_subagent(n) for n in names]

    # 第二步：*coros 把列表展开成多个位置参数传给 gather
    #   ≈ JS 的 Promise.all(coros)（JS 直接传数组，Python 要 * 展开）
    return await asyncio.gather(*coros)


# ═══════════════════════════════════════════════════════════════════════════
# TODO 2：异步生成器
# ═══════════════════════════════════════════════════════════════════════════
async def stream_tokens(text: str, delay: float = 0.01) -> AsyncIterator[str]:
    """逐字流式输出文本。"""
    # 💡 for ch in text: Python 字符串可直接遍历，每次拿到一个字符
    for ch in text:
        await asyncio.sleep(delay)  # 模拟模型生成一个 token 的耗时
        yield ch                      # 吐出当前字符，暂停在这里等下次被消费


async def collect_stream(text: str) -> str:
    """消费异步生成器，拼成完整字符串。"""
    result = ""
    async for ch in stream_tokens(text):
        result += ch
    return result


# ═══════════════════════════════════════════════════════════════════════════
# TODO 3：async with 上下文管理器
# ═══════════════════════════════════════════════════════════════════════════
class MockSession:
    """模拟需要异步创建 / 关闭的会话。"""

    def __init__(self, name: str):
        self.name = name
        self.entered = False
        self.exited = False

    async def __aenter__(self):
        """进入 async with 时执行，返回值会赋给 as 后面的变量。"""
        await asyncio.sleep(0.01)   # 模拟异步创建会话
        self.entered = True
        return self                  # 关键：必须 return self 或某个对象

    async def __aexit__(self, exc_type, exc, tb):
        """退出 async with 时执行（成功/失败都会走）。"""
        await asyncio.sleep(0.01)   # 模拟异步关闭会话
        self.exited = True
        # 💡 返回 False（或 None）= 不吞异常，异常继续往上抛
        #    返回 True = 吞掉异常（慎用，会掩盖错误）
        return False

    async def ask(self, question: str) -> str:
        return f"[{self.name}] 回答：{question}"


async def use_session(name: str, question: str) -> dict:
    """使用 async with 安全创建 / 使用 / 释放会话。"""
    async with MockSession(name) as session:
        answer = await session.ask(question)
        snapshot = {
            "answer": answer,
            "entered": session.entered,
            "exited_before_exit": session.exited,
        }

    snapshot["exited"] = session.exited
    return snapshot


# ═══════════════════════════════════════════════════════════════════════════
# TODO 5：dataclass + Literal
# ═══════════════════════════════════════════════════════════════════════════
@dataclass
class SubAgentConfig:
    """
    子 Agent 配置对象。

    💡 对比裸 dict 的好处：
       - 字段名写错 → IDE 直接报红（dict 要到运行时 KeyError）
       - 少传必填字段 → 实例化时就报错
       - 有 __repr__，print 出来可读
       - 支持 == 比较
    """
    name: str
    description: str
    system_prompt: str
    # 💡 可变默认值必须用 field(default_factory=list)
    #    如果写 tools: list[str] = []，所有实例会共享同一个 list（经典坑）
    tools: list[str] = field(default_factory=list)
    # 💡 Literal 限定取值范围 ≈ TS 的 'search' | 'db' | 'rag'
    kind: Literal["search", "db", "rag"] = "search"

    def tool_count(self) -> int:
        """工具数量。"""
        return len(self.tools)


# ── 本地自测 ────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("=" * 60)
    print("Day 3 参考实现自测")
    print("=" * 60)

    import time

    # TODO 1
    start = time.perf_counter()
    results = asyncio.run(run_parallel(["市场情报助手", "数据分析助手", "内部知识助手"]))
    elapsed = time.perf_counter() - start
    print(f"[1] 并发结果：{results}")
    print(f"    总耗时：{elapsed:.3f}s（串行需 0.30s）")

    # TODO 2
    print(f"[2] 流式拼回：{asyncio.run(collect_stream('你好Agent'))}")

    # TODO 3
    print(f"[3] 会话结果：{asyncio.run(use_session('temp_session', '公司差旅标准？'))}")

    # TODO 4（需要先完成 mini_agent/__init__.py）
    try:
        from mini_agent import search_tool, db_tool, rag_tool, quick_answer
        print("[4] 包导入成功：search_tool / db_tool / rag_tool / quick_answer")
    except Exception as e:
        print(f"[4] 包导入失败（请先完成 mini_agent/__init__.py）：{type(e).__name__}: {e}")

    # TODO 5
    cfg = SubAgentConfig(
        name="市场情报助手",
        description="搜索市场信息",
        system_prompt="你是市场分析专家",
    )
    print(f"[5] dataclass：{cfg.name} | kind={cfg.kind} | 工具数={cfg.tool_count()}")
    print(f"    repr：{cfg}")
