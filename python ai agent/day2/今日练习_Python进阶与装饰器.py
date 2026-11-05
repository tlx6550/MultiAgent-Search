"""
╔══════════════════════════════════════════════════════════════════════╗
║  Day 2 练习：Python 进阶语法（装饰器 / 推导式 / 异常处理 / *args）       ║
╠══════════════════════════════════════════════════════════════════════╣
║  学习目标（5 个点，每个都对应项目里的真实代码）                           ║
║    1. 装饰器基础：写一个 @retry 装饰器（项目里 tavily_tool.py 用了这个） ║
║    2. 列表推导式：Python 最 Pythonic 的写法（≈ JS 的 .map() / .filter()）║
║    3. *args / **kwargs：写灵活的工具注册函数                             ║
║    4. 异常处理 try/except：数据库/网络请求里到处都是                    ║
║    5. 类基础：用 class 封装一个简单的 ToolRegistry                       ║
╠══════════════════════════════════════════════════════════════════════╣
║  规则：                                                                 ║
║    - 先自己写，卡住 10 分钟再看 参考实现_day2.py                          ║
║    - 每完成一个 TODO，就运行一次：python 验收_day2.py                     ║
╚══════════════════════════════════════════════════════════════════════╝

📖 Day 2 新增 Python ↔ JS 对照速查表（Day 1 已有的不再重复）：
┌───────────────────────────────────┬──────────────────────────────────────────────┐
│ Python                            │ JavaScript                                   │
├───────────────────────────────────┼──────────────────────────────────────────────┤
│ @decorator                        │ HOC / 高阶函数包装 (func => wrappedFunc)      │
│ @decorator(arg)                   │ 带参数的高阶函数 (opts => func => wrapped)     │
│ [x*2 for x in arr]                │ arr.map(x => x*2)                            │
│ [x for x in arr if x>0]           │ arr.filter(x => x > 0)                       │
│ {k:v for k,v in d.items() if ...} │ Object.fromEntries(Object.entries(d).filter())│
│ def fn(*args):                    │ function fn(...args) {}                      │
│ def fn(**kwargs):                 │ function fn({...kwargs}) {}                  │
│ def fn(a, b=1, *args, **kwargs):  │ function fn(a, b=1, ...args, opts) {}        │
│ try: ... except E as e:           │ try {} catch (e) {}                          │
│ try: ... finally:                 │ try {} finally {}                            │
│ class Foo: def __init__(self):    │ class Foo { constructor() {} }              │
│ self.name = name                  │ this.name = name                              │
│ raise Exception("msg")            │ throw new Error("msg")                       │
│ functools.wraps(fn)               │ 手动拷贝 name / length 属性                  │
└───────────────────────────────────┴──────────────────────────────────────────────┘
"""

from __future__ import annotations

import time          # 💡 JS 类比：import * as time from 'time'（但 Python 的 time 是标准库）
import functools     # 💡 JS 类比：import * as functools from 'functools'（标准库，装饰器常用）
from typing import Callable, Type, Tuple  # 💡 JS 类比：type Callable = (args) => any


# ============================================================
# TODO 1：装饰器基础 — 写一个带重试的装饰器
# ============================================================
# 项目里 tavily_tool.py 的 @retry_with_backoff 就是这个模式！
# 先做个简单版：失败自动重试 N 次，每次等 delay 秒
#
# 💡 JS 类比：
#   function retry(maxRetries = 3, delay = 1000) {
#     return function (fn) {
#       return async function (...args) {
#         let lastError;
#         for (let i = 0; i <= maxRetries; i++) {
#           try { return await fn(...args); }
#           catch (e) { lastError = e; await sleep(delay); }
#         }
#         throw lastError;
#       };
#     };
#   }
def retry(max_retries: int = 3, delay: float = 0.01):
    """
    带参数的重试装饰器工厂。

    语法点：
      - 这是「装饰器工厂」不是直接的装饰器——因为它要接收参数
      - 三层嵌套：工厂 → decorator → wrapper
      - @functools.wraps 把原函数的名字/docstring 拷贝过来

    Args:
        max_retries: 最大重试次数（不含首次调用）
        delay: 每次重试前的等待秒数

    Returns:
        decorator: 装饰器（可以直接 @retry(max_retries=3) 用）
    """
    def decorator(func: Callable) -> Callable:
        # 💡 functools.wraps 把 func.__name__ / func.__doc__ 拷到 wrapper 上
        #    这样外部看 wrapper 还是原函数的名字，不影响调试
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # TODO 1a：实现重试逻辑
            # 提示：range(max_retries + 1) 含首次调用，共 max_retries + 1 次机会
            # 成功就 return，失败就 sleep(delay) 继续试，全用完了 raise
            # ... 在这里写你的代码 ...
            pass
        return wrapper
    return decorator


# ============================================================
# TODO 2：列表推导式 — 处理子智能体列表
# ============================================================
# 项目里 list_subagents() 可以用推导式一行搞定！
#
# 💡 JS 类比：
#   // 原来的写法：for + push
#   const result = [];
#   for (const [_k, v] of Object.entries(subAgents)) {
#     result.push({ name: v.name, desc: v.description.trim() });
#   }
#   // 推导式（≈ JS 的 .map()）
#   const result = Object.entries(subAgents).map(([_k, v]) => ({
#     name: v.name, desc: v.description.trim()
#   }));
def list_subagents_compact(config: dict) -> list[dict]:
    """
    用列表推导式重写 Day 1 的 list_subagents。

    语法点：
      - [表达式 for 变量 in 可迭代对象]  ≈ JS 的 .map()
      - [表达式 for 变量 in 可迭代对象 if 条件]  ≈ JS 的 .filter().map()
      - {k: v for k, v in ...} 字典推导式 ≈ Object.fromEntries(...map...)

    要求：
      - 一行代码返回，不要 for + append
      - 字段和 Day 1 一样：name / description / prompt_chars
    """
    # TODO 2：用列表推导式替换 Day 1 的 for + append
    # 提示：config["sub_agents"].items() 拿到每个 (key, value)
    # ... 在这里写你的代码 ...
    pass


# ============================================================
# TODO 3：*args / **kwargs — 写灵活的工具注册函数
# ============================================================
# 项目里 @tool 装饰器可以接收任意函数，就是靠 *args / **kwargs 传参
#
# 💡 JS 类比：
#   function registerTool(name, ...handlers) { ... }
#   registerTool('search', handler1, handler2, handler3);  // handlers = [h1, h2, h3]
#
#   function createAgent(name, **options) { ... }
#   createAgent('main', model=deepseek, temperature=0.7);  // options = {model, temperature}
def register_tools(*tools, registry: dict | None = None, **meta):
    """
    注册工具到 registry 字典。

    语法点：
      - *tools: 任意多个位置参数都会被打包成 tuple（≈ JS 的 ...tools）
      - **meta: 任意多个关键字参数都会被打包成 dict（≈ JS 的 {..meta}）
      - registry: dict | None = None  类型注解 + 默认值 + 可选参数

    用法：
      register_tools(search_tool, db_tool, rag_tool, name="主Agent工具集", version="1.0")
      → tools = (search_tool, db_tool, rag_tool)  meta = {name: "主Agent工具集", version: "1.0"}

    Returns:
        dict: 更新后的 registry（把 meta 和 tools 合在一起）
    """
    # TODO 3：实现 register_tools
    # 逻辑：
    #   1. 如果 registry 是 None，就新建一个空 dict
    #   2. 把 meta 里的每个 key-value 合并进去
    #   3. 把 tools 元组也存进去（key 可以叫 "tools"）
    #   4. 返回 registry
    # ... 在这里写你的代码 ...
    pass


# ============================================================
# TODO 4：异常处理 — 包装一个可能失败的搜索调用
# ============================================================
# 项目里 db_tools.py 每个函数都是 try/except 包装！
#
# 💡 JS 类比：
#   function safeSearch(query) {
#     try {
#       return await searchAPI(query);
#     } catch (e) {
#       console.error("搜索失败:", e.message);
#       return { error: e.message, fallback: true };
#     } finally {
#       console.log("搜索结束");
#     }
#   }
def safe_search(query: str, mock_fail: bool = False) -> dict:
    """
    包装搜索调用，失败时返回错误字典而不是崩溃。

    语法点：
      - try: 放可能出错的代码
      - except Exception as e: 捕获所有异常，e 是异常对象
      - finally: 无论成功失败都会执行（可选）
      - raise ValueError("msg") 主动抛出异常

    Args:
        query: 搜索关键词
        mock_fail: True 时模拟搜索失败（触发 except 分支）

    Returns:
        dict: 成功时返回 {query, results}，失败时返回 {error, fallback}
    """
    # TODO 4：实现 safe_search
    # 逻辑：
    #   try:
    #     如果 mock_fail=True，就 raise ValueError("网络超时")
    #     否则返回 {"query": query, "results": f"搜索到：{query} 的结果"}
    #   except Exception as e:
    #     打印错误信息
    #     返回 {"error": str(e), "fallback": True}
    #   finally:
    #     打印 "safe_search 调用结束"
    # ... 在这里写你的代码 ...
    pass


# ============================================================
# TODO 5：类基础 — 封装 ToolRegistry
# ============================================================
# 项目里虽然大部分是 dict，但 Agent 框架底层用 class 封装复杂逻辑
#
# 💡 JS 类比：
#   class ToolRegistry {
#     constructor() {
#       this.tools = new Map();
#     }
#     register(name, fn) {
#       this.tools.set(name, fn);
#     }
#     call(name, ...args) {
#       return this.tools.get(name)?.(...args);
#     }
#   }
class ToolRegistry:
    """
    简单的工具注册表——可以注册工具、调用工具。

    语法点：
      - class ToolRegistry: 定义类（≈ JS 的 class ToolRegistry）
      - def __init__(self, ...): 构造函数（≈ JS 的 constructor）
      - self.xxx = xxx: 实例属性（≈ JS 的 this.xxx = xxx）
      - 方法的第一个参数必须是 self（≈ JS 的 this，但 JS 自动传，Python 要写出来）
    """

    def __init__(self):
        # TODO 5a：初始化工具字典（self.tools = {}）
        # ... 在这里写你的代码 ...
        pass

    def register(self, name: str, fn: Callable):
        """注册一个工具。"""
        # TODO 5b：把 fn 存进 self.tools[name]
        # ... 在这里写你的代码 ...
        pass

    def call(self, name: str, *args, **kwargs):
        """调用已注册的工具，不存在返回 None。"""
        # TODO 5c：从 self.tools 取出工具，用 *args/**kwargs 调用
        # 提示：工具不存在时返回 None（不要 raise）
        # ... 在这里写你的代码 ...
        pass

    def list_tools(self) -> list[str]:
        """列出所有已注册的工具名。"""
        # TODO 5d：用列表推导式返回 self.tools 的 key 列表
        # ... 在这里写你的代码 ...
        pass


# ============================================================
# 装饰器测试入口（验收脚本会 import 这个）
# ============================================================
@retry(max_retries=3, delay=0.001)
def flaky_search(query: str, fail_count: list[int] | None = None) -> str:
    """
    模拟不稳定的搜索：前 N 次调用会抛异常，第 N+1 次成功。
    fail_count 是一个 list（用 list 因为它是可变对象，能在函数内修改）。
    """
    if fail_count is None:
        fail_count = [2]  # 默认前 2 次失败

    if fail_count[0] > 0:
        fail_count[0] -= 1
        raise ConnectionError(f"搜索暂时不可用，还剩 {fail_count[0]} 次失败")

    return f"搜索成功：{query}"


# ============================================================
# 本地自测入口
# ============================================================
if __name__ == "__main__":
    print("=" * 56)
    print("Day 2 练习自测")
    print("=" * 56)

    # TODO 1 测试
    try:
        result = flaky_search("Python Agent")
        print(f"[1] 装饰器重试：{result}")
    except Exception as e:
        print(f"[1] 未完成或失败：{e}")

    # TODO 2 测试
    try:
        fake_config = {
            "sub_agents": {
                "tavily": {"name": "市场情报助手", "description": " 搜索市场信息 ", "system_prompt": "p" * 20},
                "db": {"name": "数据分析助手", "description": "查询数据库", "system_prompt": "p" * 30},
            }
        }
        subs = list_subagents_compact(fake_config)
        print(f"[2] 推导式子智能体：{subs}")
    except Exception as e:
        print(f"[2] 未完成或失败：{e}")

    # TODO 3 测试
    try:
        reg = register_tools("search_fn", "db_fn", name="工具集", version="2.0")
        print(f"[3] register_tools：{reg}")
    except Exception as e:
        print(f"[3] 未完成或失败：{e}")

    # TODO 4 测试
    try:
        success = safe_search("正常查询")
        fail = safe_search("触发异常", mock_fail=True)
        print(f"[4] safe_search 正常：{success}")
        print(f"    safe_search 异常：{fail}")
    except Exception as e:
        print(f"[4] 未完成或失败：{e}")

    # TODO 5 测试
    try:
        tr = ToolRegistry()
        tr.register("hello", lambda name: f"Hello, {name}!")
        result = tr.call("hello", "World")
        tools = tr.list_tools()
        print(f"[5] ToolRegistry call：{result}")
        print(f"    ToolRegistry list：{tools}")
    except Exception as e:
        print(f"[5] 未完成或失败：{e}")

    print("\n完成后运行：python 验收_day2.py")
