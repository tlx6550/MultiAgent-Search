"""
╔══════════════════════════════════════════════════════════════════════╗
║  Day 3 练习：异步编程深入 + 模块化（Agent 开发的两块地基）               ║
╠══════════════════════════════════════════════════════════════════════╣
║  学习目标（5 个点，全部对应项目真实代码）                                ║
║    1. asyncio.gather 并发：同时调度多个子 Agent（≈ Promise.all）        ║
║    2. 异步生成器 + async for：流式接收大模型输出（main_agent.py 核心）  ║
║    3. async with：异步上下文管理器，安全释放资源                        ║
║    4. 包与 __init__.py：项目 agent/ 目录为什么这么组织                  ║
║    5. dataclass + Literal：给配置对象加类型约束                         ║
╠══════════════════════════════════════════════════════════════════════╣
║  规则：                                                                 ║
║    - 先自己写，卡住 10 分钟再看 参考实现_day3.py                          ║
║    - 每完成一个 TODO，就运行一次：python 验收_day3.py                     ║
║    - 注意：TODO 4 要改的是 mini_agent/__init__.py，不是本文件！           ║
╚══════════════════════════════════════════════════════════════════════╝

📖 Day 3 新增 Python ↔ JS 对照速查表（Day 1/2 已学的不再重复）：
┌──────────────────────────────────────┬─────────────────────────────────────────────┐
│ Python                               │ JavaScript                                  │
├──────────────────────────────────────┼─────────────────────────────────────────────┤
│ await asyncio.gather(t1, t2, t3)     │ await Promise.all([p1, p2, p3])             │
│ await asyncio.gather(*tasks)         │ await Promise.all(tasks)                    │
│ async def gen(): yield x             │ async function* gen() { yield x }           │
│ async for x in gen():                │ for await (const x of gen())                │
│ async with obj:                      │ 无原生对应（≈ try/finally + await）          │
│ class C: __aenter__/__aexit__        │ Symbol.asyncIterator 手写                   │
│ asyncio.create_task(coro)            │ const p = fn()  // 立即启动不等待            │
│ asyncio.TimeoutError                 │ AbortError / Promise timeout                │
│ from .module import x                │ import { x } from './module'                │
│ from ..pkg import x                  │ import { x } from '../pkg'                  │
│ __init__.py                          │ index.ts（barrel 出口文件）                  │
│ __all__ = ["a", "b"]                 │ export { a, b }                             │
│ @dataclass                           │ interface X { ... } + 构造对象               │
│ Literal["a", "b"]                     │ 'a' | 'b'  (TS 联合类型)                     │
│ Optional[str] = None                 │ string | undefined                          │
└──────────────────────────────────────┴─────────────────────────────────────────────┘

🎯 学完 Day 3 你应该能回答：
  1. 3 个子 Agent 并行跑，为什么比串行快？gather 和 for 循环 await 差在哪？
  2. main_agent.py 里 `async for chunk in main_agent.astream(...)` 为什么必须用 async for？
  3. 项目为什么把 agent 拆成 agent/、agent/subagents/ 多级目录？
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from typing import Literal, Optional, AsyncIterator


# ============================================================
# TODO 1：asyncio.gather —— 并发调度多个子 Agent
# ============================================================
# 项目场景：用户问「结合竞品动态和我们的库存数据」
#   主 Agent 需要同时调「市场情报助手」和「数据分析助手」
#   串行 = 等第一个跑完再跑第二个；并发 = 两个一起跑，总耗时取最慢的那个
#
# 💡 JS 类比：
#   // 串行（慢）：总耗时 = 1 + 1 + 1 = 3 秒
#   const a = await taskA(); const b = await taskB(); const c = await taskC();
#
#   // 并发（快）：总耗时 ≈ 1 秒（最慢的那个）
#   const [a, b, c] = await Promise.all([taskA(), taskB(), taskC()]);
async def call_subagent(name: str, seconds: float = 0.1) -> str:
    """
    模拟调用一个子 Agent（耗时 seconds 秒）。

    Args:
        name: 子 Agent 名称
        seconds: 模拟耗时

    Returns:
        str: 子 Agent 的返回结果
    """
    # 💡 模拟真实耗时：asyncio.sleep 不阻塞其他协程
    await asyncio.sleep(seconds)
    return f"{name} 完成"


async def run_parallel(names: list[str]) -> list[str]:
    """
    并发调用多个子 Agent，返回结果列表（顺序与 names 一致）。

    💡 关键 API：asyncio.gather(*coros)
        - 接收多个协程对象，并发执行
        - 返回结果列表，顺序与传入顺序一致（不是完成顺序！）
        - ≈ JS 的 Promise.all

    💡 JS 类比：
        async function runParallel(names) {
          return await Promise.all(
            names.map(n => callSubagent(n))
          );
        }

    Args:
        names: 子 Agent 名称列表

    Returns:
        list[str]: 每个子 Agent 的返回结果
    """
    # TODO 1：实现并发调用
    # 提示：
    #   1. 先用列表推导式生成协程列表：[call_subagent(n) for n in names]
    #   2. 再用 await asyncio.gather(*协程列表) 并发执行
    #   3. 注意 gather 前面要加 await，否则拿到的是协程对象不是结果
    # ---- 在下面写你的代码 ----
    coros = [call_subagent(n) for n in names]
    print(f"并发调用 {len(names)} 个子 Agent：{names}")
    print(f"协程列表：{coros}")
    return await asyncio.gather(*coros)


# ============================================================
# TODO 2：异步生成器 —— 流式接收大模型输出
# ============================================================
# 项目场景：main_agent.py 的这段核心代码
#   async for chunk in main_agent.astream({...}, config=config):
#       for node_name, state in chunk.items():
#           ...
# 大模型不是一次性给你整段答案，而是「一个字一个字」吐出来（流式），
# 所以必须用 async for 逐块接收，边收边推给前端 WebSocket。
#
# 💡 JS 类比：
#   async function* streamTokens(text) {
#     for (const ch of text) {
#       await sleep(10);
#       yield ch;
#     }
#   }
#   for await (const ch of streamTokens('你好')) { process(ch); }
async def stream_tokens(text: str, delay: float = 0.01) -> AsyncIterator[str]:
    """
    把文本逐字流式输出（异步生成器）。

    语法点：
      - async def + yield = 异步生成器函数
      - 调用它不会立即执行，而是返回一个「异步迭代器」对象
      - 只能用 async for 消费

    Args:
        text: 要流式输出的文本
        delay: 每个字之间的间隔

    Yields:
        str: 单个字符
    """
    # TODO 2：实现逐字流式输出
    # 提示：
    #   1. for ch in text: 逐个字符遍历（Python 字符串可以直接遍历）
    #   2. await asyncio.sleep(delay) 模拟模型生成间隔
    #   3. yield ch 吐出这个字符（关键！yield 是生成器的标志）
    # ---- 在下面写你的代码 ----
    for ch in text:
        await asyncio.sleep(delay)
        yield ch


async def collect_stream(text: str) -> str:
    """
    消费 stream_tokens 的异步生成器，把碎片拼成完整字符串。

    这个方法本身已经写好了，用来让你验证 TODO 2 是否正确。

    💡 JS 类比：
        async function collectStream(text) {
          let result = '';
          for await (const ch of streamTokens(text)) { result += ch; }
          return result;
        }
    """
    result = ""
    # 💡 async for ≈ JS 的 for await (const x of ...)
    async for ch in stream_tokens(text):
        result += ch
    return result


# ============================================================
# TODO 3：async with —— 异步上下文管理器
# ============================================================
# 项目场景：数据库连接、会话创建这类「用完必须释放」的资源
#   同步版用 with（Day 1 已学），异步版用 async with
#   项目里 RAGFlow 的 create_session / delete_sessions 就是这种模式
#
# 💡 JS 类比：JS 没有原生 async with，只能手写
#   async function withSession(fn) {
#     const session = await createSession();
#     try { return await fn(session); }
#     finally { await session.close(); }   // 必须手动保证释放
#   }
# Python 把 try/finally 这个模板封装成了 async with，不会忘。
class MockSession:
    """
    模拟一个需要异步创建 / 异步关闭的会话。

    实现 async with 需要两个魔法方法：
      - __aenter__：进入时调用（≈ JS 的 try 前创建资源）
      - __aexit__：退出时调用（≈ JS 的 finally 释放资源）
    """

    def __init__(self, name: str):
        self.name = name
        # 💡 状态标记：验收时用它检查 enter / exit 是否都被触发
        self.entered = False
        self.exited = False

    async def __aenter__(self):
        """进入 async with 块时执行。"""
        # TODO 3a：模拟创建会话
        # 提示：await asyncio.sleep(0.01)；把 self.entered 设为 True；return self
        # ---- 在下面写你的代码 ----
        await asyncio.sleep(0.01)
        self.entered = True
        return self

    async def __aexit__(self, exc_type, exc, tb):
        """退出 async with 块时执行（无论成功还是出错都会执行）。"""
        # TODO 3b：模拟关闭会话
        # 提示：await asyncio.sleep(0.01)；把 self.exited 设为 True
        #      返回 False 表示「不吞掉异常」（把异常继续往上抛）
        # ---- 在下面写你的代码 ----
        await asyncio.sleep(0.01)
        self.exited = True
        return False  # 不吞异常，继续往上抛

    async def ask(self, question: str) -> str:
        """向会话提问。"""
        return f"[{self.name}] 回答：{question}"


async def use_session(name: str, question: str) -> dict:
    """
    使用 async with 安全地创建 / 使用 / 释放会话。

    这个方法已写好框架，你要让 MockSession 的两个魔法方法生效。

    💡 JS 类比：
        async function useSession(name, question) {
          const s = new MockSession(name);
          await s.__aenter__();
          try {
            const answer = await s.ask(question);
            return { answer, entered: s.entered, exited: s.exited };
          } finally {
            await s.__aexit__();
          }
        }
    """
    #      写法 1：async with（当前代码，简洁）
    # async with MockSession(name) as session:
    #     answer = await session.ask(question)

    # # ↕ 完全等价于 ↕

    # # 写法 2：手动写 try/finally（展开看就明白）
    # s = MockSession(name)                     # 1. 造对象
    # await s.__aenter__()                      # 2. 进入前执行异步初始化
    # try:
    #     session = s                           # as session = 把返回值赋给 session
    #     answer = await session.ask(question)  # 3. 块内干活
    # finally:
    #     await s.__aexit__(None, None, None)   # 4. 退出时一定执行清理
    # 💡 async with ≈ 自动 try/finally，退出时一定调用 __aexit__
    async with MockSession(name) as session:
        answer = await session.ask(question)
        # 注意：这里读取 exited 时还是 False，因为 __aexit__ 还没执行
        snapshot = {"answer": answer, "entered": session.entered, "exited_before_exit": session.exited}

    # 走到这里说明 __aexit__ 已经执行完了
    snapshot["exited"] = session.exited
    return snapshot


# ============================================================
# TODO 5：dataclass + Literal —— 给配置对象加类型约束
# ============================================================
# 项目场景：项目里子 Agent 配置现在是裸 dict：
#   {"name": ..., "description": ..., "system_prompt": ..., "tools": [...]}
# 裸 dict 的问题：字段名写错要到运行时才发现（'descriptoin' 也照样能跑）
# dataclass 能在定义时就锁死字段，IDE 还能自动补全
#
# 💡 TS 类比（这个最直观）：
#   interface SubAgentConfig {
#     name: string;
#     description: string;
#     system_prompt: string;
#     tools: string[];
#     kind?: 'search' | 'db' | 'rag';   // 对应 Literal
#   }
@dataclass
class SubAgentConfig:
    """
    子 Agent 配置对象（dataclass 版）。

    💡 @dataclass 自动帮你生成 __init__ / __repr__ / __eq__，
       你只写字段声明就行。

    💡 JS/TS 类比：
        interface SubAgentConfig { name: string; description: string; ... }
        （TS 只有类型；dataclass 是类型 + 真能 new 出来）

    字段说明：
      - name / description / system_prompt：必填
      - tools：默认空列表
      - kind：只能是 'search' / 'db' / 'rag' 三者之一，默认 'search'
    """

    # TODO 5a：声明 name 字段（类型 str，无默认值）
    # 提示写法：name: str
    # ---- 在下面写你的代码 ----
    name:str
    # TODO 5b：声明 description 字段（类型 str，无默认值）
    # ---- 在下面写你的代码 ----
    description:str

    # TODO 5c：声明 system_prompt 字段（类型 str，无默认值）
    # ---- 在下面写你的代码 ----
    system_prompt:str

    # TODO 5d：声明 tools 字段（类型 list[str]，默认空列表）
    # ⚠️ 坑：不能用 tools: list[str] = []（可变对象共享，所有实例会共用同一个 list）
    # 判断标准很简单：默认值如果是可变对象（list、dict、set），就用 default_factory=list/dict/set；不可变对象（int、str、float、tuple）可以直接写。
    #    正确写法：tools: list[str] = field(default_factory=list)
    # ---- 在下面写你的代码 ----
    tools:list[str] = field(default_factory=list)

    # TODO 5e：声明 kind 字段
    # 类型必须是 Literal["search", "db", "rag"]，默认值 "search"
    # 提示写法：kind: Literal["search", "db", "rag"] = "search"
    # ---- 在下面写你的代码 ----
    kind:Literal["search","db","rag"] = "search"
    def tool_count(self) -> int:
        """返回工具数量（这个方法已给好，方便你验证字段是否正确）。"""
        return len(self.tools)


# ============================================================
# 本地自测入口
# ============================================================
if __name__ == "__main__":
    print("=" * 60)
    print("Day 3 练习自测")
    print("=" * 60)

    # ── TODO 1：并发 ─────────────────────────────────────────────────────
    try:
        import time
        start = time.perf_counter()
        results = asyncio.run(run_parallel(["市场情报助手", "数据分析助手", "内部知识助手"]))
        elapsed = time.perf_counter() - start
        print(f"[1] 并发结果：{results}")
        print(f"    总耗时：{elapsed:.2f}s（并发应远小于 0.3s）")
    except Exception as e:
        print(f"[1] 未完成或失败：{type(e).__name__}: {e}")

    # ── TODO 2：异步生成器 ───────────────────────────────────────────────
    #      ❌ 错误：直接调异步函数，不会执行！
    # use_session("temp_session", "问题")
    # # 返回的是 <coroutine object use_session at 0x...>
    # # 然后程序就结束了，协程根本没跑！

    # # ✅ 正确：交给 asyncio.run
    # info = asyncio.run(use_session("temp_session", "问题"))
    # # 这次协程真的执行完，info 里拿到了最终返回值
    # 核心概念：async def 定义的函数叫协程函数，调用它不会立刻执行函数体，
    # 而是返回一个协程对象。协程对象需要被事件循环"驱动"才能真正运行。
    # asyncio.run 就是帮你启动事件循环、跑完协程、拿结果。
    # asyncio.run(coro) 是同步代码调异步函数的"入口"——它帮你造一个新的事件循环，驱动协程跑完，拿到结果，最后清理循环。
    # 相当于"启动异步世界的引擎，跑完活，再关掉引擎"。
    #     你的代码（同步世界）
    #     │
    #     │  asyncio.run(coro)  ← 入口
    #     ▼
    # ┌─────────────────┐
    # │  事件循环启动    │  ← asyncio.run 内部自动创建
    # │                 │
    # │  执行 coro       │  ← 真正跑你的 async 函数
    # │    ├─ await A   │
    # │    ├─ await B   │  ← 遇到 await 就把控制权交回事件循环
    # │    └─ return X  │
    # │                 │
    # │  事件循环关闭    │  ← asyncio.run 内部自动清理
    # └─────────────────┘
    #     │
    #     ▼
    # 你的代码继续（同步世界）
    # info = X   ← 拿到返回值
    try:
        text = asyncio.run(collect_stream("你好Agent"))
        print(f"[2] 流式拼回：{text}")
    except Exception as e:
        print(f"[2] 未完成或失败：{type(e).__name__}: {e}")

    # ── TODO 3：async with ───────────────────────────────────────────────
    try:
        info = asyncio.run(use_session("temp_session", "公司差旅标准？"))
        print(f"[3] 会话结果：{info}")
    except Exception as e:
        print(f"[3] 未完成或失败：{type(e).__name__}: {e}")

    # ── TODO 4：包导入（需要先改 mini_agent/__init__.py）──────────────────
    try:
        from mini_agent import search_tool, db_tool, rag_tool, quick_answer
        print("[4] 包导入成功：search_tool / db_tool / rag_tool / quick_answer")
    except Exception as e:
        print(f"[4] 未完成或失败：{type(e).__name__}: {e}")

    # ── TODO 5：dataclass ────────────────────────────────────────────────
    try:
        cfg = SubAgentConfig(
            name="市场情报助手",
            description="搜索市场信息",
            system_prompt="你是市场分析专家",
            kind="search",
        )
        print(f"[5] dataclass：{cfg.name} | kind={cfg.kind} | 工具数={cfg.tool_count()}")
    except Exception as e:
        print(f"[5] 未完成或失败：{type(e).__name__}: {e}")

    print("\n完成后运行：python 验收_day3.py")
