"""
╔══════════════════════════════════════════════════════════════════════╗
║  Day 2 参考实现（仅供参考！自己先写，卡住 10 分钟再看）                   ║
╠══════════════════════════════════════════════════════════════════════╣
║  使用方式：                                                             ║
║    1. 先自己写 今日练习_Python进阶与装饰器.py                            ║
║    2. 卡住超过 10 分钟再看这里                                          ║
║    3. 看完关掉，凭记忆重写一遍                                          ║
║    4. 验收通过后，再回来对照看为什么这样写                               ║
╚══════════════════════════════════════════════════════════════════════╝

📖 Day 2 Python ↔ JS 对照（参考实现版本）：
┌───────────────────────────┬──────────────────────────────────────────┐
│ Python                    │ JavaScript                               │
├───────────────────────────┼──────────────────────────────────────────┤
│ @retry(max_retries=3)     │ retry({maxRetries: 3})(fn)               │
│ [.. for .. in ..]         │ arr.map / arr.filter / Object.entries.map│
│ fn(*args, **kwargs)       │ fn(...args, ...kwargs)                   │
│ try: except E as e:       │ try {} catch (e) {}                      │
│ class Foo: __init__:      │ class Foo { constructor() {} }          │
│ self.xxx = yyy            │ this.xxx = yyy                           │
└───────────────────────────┴──────────────────────────────────────────┘
"""

from __future__ import annotations

import time
import functools
from typing import Callable


# ═══════════════════════════════════════════════════════════════════════════
# TODO 1：retry 装饰器工厂
# ═══════════════════════════════════════════════════════════════════════════
def retry(max_retries: int = 3, delay: float = 0.01):
    """带参数的重试装饰器工厂。"""
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # 💡 range(max_retries + 1) 含首次调用，总共 max_retries + 1 次机会
            last_exception = None
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)  # 成功直接返回
                except Exception as e:
                    last_exception = e
                    if attempt < max_retries:
                        time.sleep(delay)  # 还有机会就等 delay 秒继续
            raise last_exception  # 所有机会用完，抛出最后一次的异常
        return wrapper
    return decorator


# ═══════════════════════════════════════════════════════════════════════════
# TODO 2：列表推导式版本的 list_subagents
# ═══════════════════════════════════════════════════════════════════════════
# 💡 JS 类比：
#   const subs = Object.entries(config.sub_agents).map(([_k, v]) => ({
#     name: v.name,
#     description: v.description.trim(),
#     prompt_chars: v.system_prompt.length,
#   }));
def list_subagents_compact(config: dict) -> list[dict]:
    """用列表推导式一行搞定！"""
    # 💡 {v: val for ...} 是字典推导式；外层 [...] 是列表推导式
    # 整个表达式 = JS 的 Object.entries(...).map(...)
    return [
        {
            "name": value["name"],
            "description": value["description"].strip(),
            "prompt_chars": len(value["system_prompt"]),
        }
        for _key, value in config["sub_agents"].items()
    ]


# ═══════════════════════════════════════════════════════════════════════════
# TODO 3：register_tools *args/**kwargs
# ═══════════════════════════════════════════════════════════════════════════
def register_tools(*tools, registry: dict | None = None, **meta):
    """注册工具到 registry，*tools 收任意多个位置参数，**meta 收任意多个关键字参数。"""
    # 💡 类型注解 dict | None = None 意思是：可以是 dict 也可以是 None，默认 None
    # 如果 registry 是 None（没传），就新建一个空 dict
    if registry is None:
        registry = {}

    # 💡 把 meta 里的每个 key-value 合并进 registry
    # dict.update() ≈ JS 的 Object.assign(registry, meta) 或 { ...registry, ...meta }
    #   为什么不直接 registry.update(meta)？因为 meta 是 **kwargs 解包后的 dict
    #   直接用 update 就行
    registry.update(meta)

    # 💡 把 tools 元组也存进去
    # *tools 收到的是一个 tuple：(tool_a, tool_b, ...)
    # 这里我们用 "tools" 作为 key 存进去
    registry["tools"] = tuple(tools)

    return registry


# ═══════════════════════════════════════════════════════════════════════════
# TODO 4：safe_search 异常处理
# ═══════════════════════════════════════════════════════════════════════════
def safe_search(query: str, mock_fail: bool = False) -> dict:
    """包装搜索调用，失败时返回错误字典而不是崩溃。"""
    try:
        if mock_fail:
            # 💡 raise 主动抛出异常（≈ JS 的 throw）
            raise ValueError("网络超时")
        return {"query": query, "results": f"搜索成功：{query} 的结果"}

    # 💡 except Exception as e 捕获所有异常，e 是异常对象
    #    只捕获 ValueError 的话就写 except ValueError as e:
    except Exception as e:
        # 💡 打印到控制台（≈ console.error）
        print(f"[safe_search] 搜索失败：{e}")
        return {"error": str(e), "fallback": True}

    # 💡 finally 无论成功还是失败都会执行（可选，不是必须的）
    finally:
        print("safe_search 调用结束")


# ═══════════════════════════════════════════════════════════════════════════
# TODO 5：ToolRegistry 类
# ═══════════════════════════════════════════════════════════════════════════
class ToolRegistry:
    """简单的工具注册表——可以注册工具、调用工具、列出工具。"""

    # 💡 __init__ 是构造函数（≈ JS 的 constructor）
    # self 是实例本身（≈ JS 的 this，但 Python 要写出来）
    def __init__(self):
        # 💡 self.tools = {} 是实例属性（≈ this.tools = {}）
        self.tools = {}

    def register(self, name: str, fn: Callable):
        """注册一个工具。"""
        # 💡 self.tools[name] = fn（≈ this.tools.set(name, fn) 或 this.tools[name] = fn）
        self.tools[name] = fn

    def call(self, name: str, *args, **kwargs):
        """调用已注册的工具，不存在返回 None。"""
        # 💡 self.tools.get(name) 等价于 self.tools[name] 但不存在时返回 None 而不是 KeyError
        #    ≈ JS 的 this.tools[name] ?? null
        fn = self.tools.get(name)
        if fn is None:
            return None
        # 💡 *args 解包位置参数，**kwargs 解包关键字参数
        #    ≈ JS 的 fn(...args, ...kwargs)
        return fn(*args, **kwargs)

    def list_tools(self) -> list[str]:
        """列出所有已注册的工具名。"""
        # 💡 列表推导式：返回字典所有 key
        #    ≈ JS 的 Object.keys(this.tools)
        return list(self.tools.keys())


# ═══════════════════════════════════════════════════════════════════════════
# flaky_search：带 @retry 装饰器的测试函数
# ═══════════════════════════════════════════════════════════════════════════
@retry(max_retries=3, delay=0.001)
def flaky_search(query: str, fail_count: list[int] | None = None) -> str:
    """模拟不稳定的搜索：前 N 次抛异常，第 N+1 次成功。"""
    if fail_count is None:
        fail_count = [2]

    if fail_count[0] > 0:
        fail_count[0] -= 1
        raise ConnectionError(f"搜索暂时不可用，还剩 {fail_count[0]} 次失败")

    return f"搜索成功：{query}"


# ── 本地自测 ────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("=" * 56)
    print("Day 2 参考实现自测")
    print("=" * 56)

    # TODO 1
    fc = [2]
    print(f"[1] decorator retry: {flaky_search('Python', fail_count=fc)}")

    # TODO 2
    fake = {"sub_agents": {"tavily": {"name": "市场情报助手", "description": " 搜索 ", "system_prompt": "p"*10},
                          "db": {"name": "数据分析助手", "description": "查库", "system_prompt": "p"*20}}}
    print(f"[2] list_subagents_compact: {list_subagents_compact(fake)}")

    # TODO 3
    print(f"[3] register_tools: {register_tools('a', 'b', name='工具集')}")

    # TODO 4
    print(f"[4] safe_search 正常: {safe_search('查询')}")
    print(f"    safe_search 异常: {safe_search('触发', mock_fail=True)}")

    # TODO 5
    tr = ToolRegistry()
    tr.register("hello", lambda n: f"Hello, {n}!")
    print(f"[5] ToolRegistry call: {tr.call('hello', 'World')}")
    print(f"    ToolRegistry list: {tr.list_tools()}")
