"""
╔══════════════════════════════════════════════════════════════════════╗
║  文件：day3/mini_agent/__init__.py                                     ║
║  角色：包的「门面」——决定外界能 import 到什么                            ║
║  JS 类比：≈ src/index.ts / barrel file（统一 re-export）                ║
║  状态：🔴 TODO 4 要你填！                                              ║
╚══════════════════════════════════════════════════════════════════════╝

📖 __init__.py 是什么？（这是 Python 包机制的核心，项目里 agent/__init__.py 同款）

  1. 一个文件夹里只要有 __init__.py，Python 就认为它是一个「包」，可以 import
  2. 外界执行 `from mini_agent import xxx` 时，实际是去执行 __init__.py
  3. __init__.py 里写什么，外界就能 import 什么

  💡 JS 类比：
     // 这就是一个 barrel file（统一出口文件）
     // src/index.ts
     export { searchTool, dbTool, ragTool } from './tools';
     export { quickAnswer } from './agent';

  🔑 为什么要这层「门面」？
     项目里 main_agent.py 写的是：
       from agent.subagents.network_search_agent import network_search_agent
     如果包设计得好，可以缩短成：
       from agent.subagents import network_search_agent
     外界不需要知道内部文件怎么拆的，只认「门面」暴露的名字。

  🔑 __all__ 是什么？
     一个列表，声明「这个包对外公开哪些名字」，影响 from mini_agent import * 的行为。
     💡 JS 类比：≈ 模块的 export 列表

──────────────────────────────────────────────────────────────────────
【TODO 4】请把下面的 TODO 填完，让这四行 import 都能成功：

    from mini_agent import search_tool, db_tool, rag_tool   # 三个工具
    from mini_agent import quick_answer                      # 一个 Agent

提示：
  - 从 .tools 导入 search_tool / db_tool / rag_tool
  - 从 .agent 导入 quick_answer
  - 注意：agent.py 已经 import 了 tools，这里重复导入是正常的（显式导出）
──────────────────────────────────────────────────────────────────────
"""

# TODO 4a：从 .tools 导入三个工具函数
# 提示写法：from .tools import search_tool, db_tool, rag_tool
# ---- 在下面写你的代码 ----
from .tools import search_tool,db_tool,rag_tool

# TODO 4b：从 .agent 导入 quick_answer
# 提示写法：from .agent import quick_answer
# ---- 在下面写你的代码 ----
from .agent import quick_answer

# TODO 4c：定义 __all__，列出所有对外公开的名字
# 提示写法：__all__ = ["search_tool", "db_tool", "rag_tool", "quick_answer"]
# ---- 在下面写你的代码 ----
__all__ = ["search_tool","db_tool","rag_tool","quick_answer"]