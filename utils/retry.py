"""
╔══════════════════════════════════════════════════════════════════════╗
║  文件：utils/retry.py                                                  ║
║  角色：指数退避重试装饰器——给网络请求加上自动失败重试                    ║
║  JS 类比：≈ axios-retry / p-retry                                      ║
║  被谁用：tools/tavily_tool.py 的 _search_with_retry                     ║
╚══════════════════════════════════════════════════════════════════════╝

📖 语法速览（重点：装饰器工厂）：
  - def retry_with_backoff(max_retries=3, ...):    ← 带参数的装饰器工厂
  - def decorator(func): ...                        ← 真正的装饰器
  - def wrapper(*args, **kwargs): ...               ← 包装后的函数
  - @functools.wraps(func)                          ← 把原函数的名字/docstring 拷贝过来

🎯 读完你应该能说清：
  1. 为什么 @retry_with_backoff(max_retries=3) 能传参数？（提示：这是装饰器工厂，不是直接的装饰器）
  2. 指数退避是什么？（提示：1s → 2s → 4s → 8s，越等越久但封顶）
  3. *args 和 **kwargs 是啥？（提示：*args = 任意位置参数，**kwargs = 任意关键字参数）
"""

import time
import functools
import threading
from typing import Type, Tuple, Callable, Any


# ═══════════════════════════════════════════════════════════════════════════
# retry_with_backoff：指数退避重试装饰器工厂
# ═══════════════════════════════════════════════════════════════════════════
# 💡 JS 类比：
#   function retryWithBackoff(options) {         // 带参数的装饰器工厂
#     return function (func) {                    // 真正的装饰器
#       return function (...args) {               // 包装后的函数
#         // 重试逻辑
#       };
#     };
#   }
#
# 用法：
#   @retry_with_backoff(max_retries=3, base_delay=1.0)
#   def call_api(): ...
# 第一次失败等 1s → 第二次等 2s → 第三次等 4s → 第四次还是失败就抛出
def retry_with_backoff(
    max_retries: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 30.0,
    backoff_factor: float = 2.0,
    exceptions: Tuple[Type[BaseException], ...] = (Exception,),
):
    """
    指数退避重试装饰器工厂。

    Args:
        max_retries: 最大重试次数（不含首次调用）
        base_delay: 首次重试等待秒数
        max_delay: 重试等待上限（封顶，防止等太久）
        backoff_factor: 退避倍数（每次等待 = 上次等待 × 这个倍数）
        exceptions: 触发重试的异常类型元组

    Returns:
        装饰器（包一层，最终返回包装后的函数）

    💡 为什么是「装饰器工厂」不是「装饰器」？
       因为它需要接收参数（max_retries 等），所以要包三层：
       retry_with_backoff(options) → decorator(func) → wrapper(*args, **kwargs)

    重试时间线示例（base_delay=1, factor=2, max=30, retries=3）：
      调用0 → 失败 → 等 1s
      调用1 → 失败 → 等 2s
      调用2 → 失败 → 等 4s
      调用3 → 仍失败 → 抛出最后一次的异常
    """
    def decorator(func: Callable) -> Callable:
        # 💡 functools.wraps 把原函数的 __name__ / __doc__ 拷贝到 wrapper 上
        #    这样外部看 wrapper 还是原函数的名字，不影响调试和日志
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            """真正执行的包装函数"""
            last_exception = None
            delay = base_delay

            # 💡 range(max_retries + 1) 含首次调用，共 max_retries + 1 次机会
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)  # 成功直接返回
                except exceptions as e:
                    last_exception = e
                    if attempt < max_retries:
                        print(
                            f"[Retry] {func.__name__} 调用失败 "
                            f"(第 {attempt + 1}/{max_retries + 1} 次): {e}. "
                            f"{delay:.1f}s 后重试..."
                        )
                        time.sleep(delay)  # 💡 阻塞等待（同步版，异步版用 await asyncio.sleep）
                        delay = min(delay * backoff_factor, max_delay)  # 💡 指数增长 + 封顶
                    else:
                        print(
                            f"[Retry] {func.__name__} 重试 {max_retries} 次后仍失败: "
                            f"{last_exception}"
                        )

            raise last_exception  # 所有重试都用完了，抛出最后一次的异常

        return wrapper

    return decorator


# ── 线程安全版本（暂未用，先留着）──
class RetryState(threading.local):
    """线程本地重试计数器，避免多线程并发时互相干扰。"""
    def __init__(self):
        self.attempt = 0


_retry_state = RetryState()
