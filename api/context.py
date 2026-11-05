"""
╔══════════════════════════════════════════════════════════════════════╗
║  文件：api/context.py                                                  ║
║  角色：协程级上下文变量——让每个请求拥有独立的「全局变量」                ║
║  JS 类比：≈ 每个请求的 React Context（但 Python async 场景里没有线程隔离）║
║  被谁用：agent/main_agent.py 设置；tools/*.py 读取                      ║
╚══════════════════════════════════════════════════════════════════════╝

📖 语法速览（重点：ContextVar 是 Python async 编程的核心）：
  - _session_dir_ctx: ContextVar[Optional[str]] = ContextVar("session_dir", default=None)
    ← 创建 ContextVar，泛型 Optional[str] 表示可以是字符串或 None
  - .set(value) → 返回 token（用于 reset）
  - .get() → 取当前值（任何深度都能 get 到，无需层层传参）
  - .reset(token) → 恢复旧值（finally 里必须调，防止内存泄漏）

🎯 读完你应该能说清：
  1. ContextVar 和 JS 的模块级变量有什么本质区别？（提示：请求隔离）
  2. 为什么 asyncio 里不能用 threading.local？（提示：所有协程在一个线程跑）
  3. set → get → reset 三步分别在哪个文件的哪个函数里调用？
"""
from contextvars import ContextVar
from typing import Optional

# =================================================================================================
# 核心知识点: ContextVars (上下文变量)
# =================================================================================================
# Q: 为什么我们需要 ContextVar？为什么不能直接用全局变量？
#
# A: 在开发异步 Web 服务 (如 FastAPI) 时，系统是 "并发" 处理多个用户请求的。
#    但在 Python 的 asyncio 机制下，这些并发请求通常运行在 *同一个线程 (Thread)* 中。
#
#    1. 如果使用全局变量 (Global Variable):
#       当 User A 的请求正在处理时，User B 的请求进来了。如果修改了全局变量，User A 的数据
#       就会被 User B 覆盖，导致严重的 "串台" 事故（例如 User A 的文件存到了 User B 的目录）。
#
#    2. 如果使用 threading.local:
#       它是基于线程隔离的。因为 asyncio 所有协程都在同一个线程跑，所以 threading.local
#       在异步场景下失效，无法隔离不同用户的请求。
#
#    3. ContextVar 的解决方案:
#       ContextVar 是 Python 3.7+ 专门为异步编程设计的 "协程级局部变量"。
#       它能确保变量在每一个 asyncio Task (即每个用户请求) 中是 *独立隔离* 的。
#       无论代码调用多深，只要是在同一个请求链路（Context）中，get() 到的都是属于当前请求的数据。
# =================================================================================================


# 定义 ContextVar 上下文变量
# -------------------------------------------------------------------------
# 这里的变量名只是一个标识符 (Identifier)，真正的值是存储在当前的 Context 环境中的。

# - 作用 ：用来记录 “当前是谁在执行任务” 。
# - 场景 ：当 Agent 打印日志或者通过 WebSocket 给前端发消息时，它需要知道：“我现在是正在服务张三，还是李四？” 这样消息才不会发错人。
_session_dir_ctx: ContextVar[Optional[str]] = ContextVar("session_dir", default=None)

# - 作用 ：用来记录 “当前是谁在执行任务” 。
# - 场景 ：当 Agent 打印日志或者通过 WebSocket 给前端发消息时，它需要知道：“我现在是正在服务张三，还是李四？” 这样消息才不会发错人。
_thread_id_ctx: ContextVar[Optional[str]] = ContextVar("thread_id", default=None)


def set_session_context(path: str):
    """
    设置当前请求链路的会话目录。
    通常在 Agent 开始执行任务前调用。

    Returns:
        Token: 返回一个 Token 对象，后续可用它来恢复(reset)变量状态。
    """
    return _session_dir_ctx.set(path)


def get_session_context() -> Optional[str]:
    """
    获取当前请求链路的会话目录。
    可以在任何深层调用的工具函数中直接使用，无需层层传递参数。
    """
    return _session_dir_ctx.get()


def set_thread_context(thread_id: str):
    """
    设置当前请求链路的 Thread ID。
    """
    return _thread_id_ctx.set(thread_id)


def get_thread_context() -> Optional[str]:
    """
    获取当前请求链路的 Thread ID。
    """
    return _thread_id_ctx.get()


def reset_session_context(session_token, thread_token=None):
    """
    清理/重置上下文。
    通常在请求处理结束 (finally 块) 中调用，防止内存泄漏或污染后续请求。
    """
    _session_dir_ctx.reset(session_token)
    if thread_token:
        _thread_id_ctx.reset(thread_token)