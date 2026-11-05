"""
╔══════════════════════════════════════════════════════════════════════╗
║  Day 1 练习：用项目真实配置，完成 5 个小任务                              ║
╠══════════════════════════════════════════════════════════════════════╣
║  学习目标（只练这 5 个点，不贪多）                                       ║
║    1. 用 pathlib 定位文件 + yaml 读取配置                               ║
║    2. 字典 / 列表遍历，理解「子智能体 = 字典配置」                        ║
║    3. if / 关键词匹配，模拟主智能体的路由决策                            ║
║    4. 构造 OpenAI 风格的 tool_call 字典                                 ║
║    5. async / await，模拟流式执行                                       ║
╠══════════════════════════════════════════════════════════════════════╣
║  规则：                                                                 ║
║    - 先自己写，卡住 10 分钟再看 参考实现_day1.py                          ║
║    - 每完成一个 TODO，就运行一次：python 验收_day1.py                     ║
╚══════════════════════════════════════════════════════════════════════╝

📖 Python ↔ JS 对照速查（本文件所有代码都能靠这张表读懂）：
┌───────────────────────────┬──────────────────────────────────────────┐
│ Python                    │ JavaScript                               │
├───────────────────────────┼──────────────────────────────────────────┤
│ dict = {"k": "v"}         │ const obj = { k: "v" }                   │
│ list = [1, 2, 3]          │ const arr = [1, 2, 3]                    │
│ list[dict] = [{...}]      │ const arr = [ {...} ]                    │
│ def fn(a: int):           │ function fn(a: number) {}                │
│ async def fn():           │ async function fn() {}                   │
│ await fn()                │ await fn()                               │
│ for x in arr:             │ for (const x of arr) {}                  │
│ for k, v in obj.items():  │ for (const [k, v] of Object.entries(obj))│
│ "a" in str                │ str.includes("a")                        │
│ f"{a}-{b}"                │ `${a}-${b}`                              │
│ "、".join(arr)            │ arr.join("、")                           │
│ raise Exception           │ throw new Error                          │
│ len(str) / len(list)      │ str.length / arr.length                  │
│ list.append(x)            │ arr.push(x)                              │
│ str.strip()               │ str.trim()                               │
└───────────────────────────┴──────────────────────────────────────────┘
"""

# ── from __future__ import annotations ──────────────────────────────────────
# 💡 JS 类比：// 允许在类型注解里直接写 dict（不需要 import typing.Dict）
# Python 3.7+ 可选，开启后注解延迟求值，IDE/LSP 更友好
from __future__ import annotations

# ── import 导入依赖 ────────────────────────────────────────────────────────
# 💡 JS 类比：import asyncio from 'asyncio'
# import 可以一次导入多个标准库，Python 是白名单导入（不像 JS 默认全量）
import asyncio          # 异步编程核心库（JS 没有这个模块，因为 JS 天生异步）
from pathlib import Path  # 路径操作库（比 os.path 更优雅，推荐用这个）
import yaml             # YAML 解析库（pip install pyyaml 装的）

# ═══════════════════════════════════════════════════════════════════════════
# 项目根目录计算（模块顶层代码，import 时立即执行）
# ═══════════════════════════════════════════════════════════════════════════
# 💡 JS 类比：const projectRoot = path.resolve(__dirname, '..', '..')
# __file__       = 当前文件路径  .../python ai agent/day1/今日练习.py
# parents[0]     = .../python ai agent/day1      ← 当前文件所在目录
# parents[1]     = .../python ai agent            ← 练习总目录
# parents[2]     = .../MultiAgent-Search          ← 项目根目录（我们要的）
PROJECT_ROOT = Path(__file__).resolve().parents[2]

# 💡 JS 类比：path.join(projectRoot, 'prompt', 'prompts.yml')
# Path 对象可以用 / 运算符拼接路径（比 os.path.join 更清爽）
PROMPTS_PATH = PROJECT_ROOT / "prompt" / "prompts.yml"


# ============================================================
# TODO 1：读取 YAML 配置
# ============================================================
# 💡 JS 类比：
#   function loadConfig(): Record<string, any> {
#     const content = fs.readFileSync(PROMPTS_PATH, 'utf-8');
#     return yaml.parse(content);
#   }
def load_config() -> dict:
    """
    读取 prompt/prompts.yml，返回 Python 字典。

    语法点：
      - with open(...) as f 是上下文管理器，用完自动关闭文件（≈ JS try/finally）
      - yaml.safe_load 安全解析 YAML，不会执行嵌入代码（不要用 yaml.load，有注入风险）
      - -> dict 是返回值类型注解，告诉 IDE 这个函数返回什么类型

    Args:
        无

    Returns:
        dict: 解析后的 Python 字典，结构与 YAML 一一对应
    """
    # 💡 JS 类比：fs.readFileSync(PROMPTS_PATH, 'utf-8')
    # encoding="utf-8" 防止中文乱码（Windows 默认编码不是 utf-8）
    with open(PROMPTS_PATH, "r", encoding="utf-8") as f:
        # 💡 JS 类比：yaml.parse(content)
        # safe_load 只解析数据，不会执行 YAML 里嵌入的 Python 对象（安全！推荐）
        return yaml.safe_load(f)
    # raise NotImplementedError("TODO 1：还没实现 load_config")


# ============================================================
# TODO 2：列出子智能体
# ============================================================
# 💡 JS 类比：
#   function listSubagents(config: Record<string, any>): Array<{name: string, description: string, prompt_chars: number}> {
#     const result = [];
#     for (const [_key, value] of Object.entries(config.sub_agents)) {
#       result.push({
#         name: value.name,
#         description: value.description.trim(),
#         prompt_chars: value.system_prompt.length,
#       });
#     }
#     return result;
#   }
def list_subagents(config: dict) -> list[dict]:
    """
    从 config["sub_agents"] 中提取每个子智能体的信息。

    返回格式（顺序与 YAML 一致）：
      [
        {"name": "市场情报助手", "description": "...", "prompt_chars": 120},
        ...
      ]

    语法点：
      - config["sub_agents"] ≈ JS 的 config.sub_agents（字典取值和 JS 对象取值几乎一样）
      - .items() 可以同时拿到 key 和 value（≈ JS 的 Object.entries）
      - .strip() 去掉首尾空白（≈ JS 的 .trim()）
      - len(str) 取字符串长度（≈ JS 的 .length）
      - .append(x) 往列表里加东西（≈ JS 的 .push(x)）

    Args:
        config: load_config() 返回的字典

    Returns:
        list[dict]: 3 个子智能体的信息列表
    """
    result = []  # 💡 JS 类比：const result = []

    # 💡 JS 类比：for (const [_key, value] of Object.entries(config.sub_agents))
    # sub_agents 字典的每个 entry：key 是 'tavily'/'db'/'ragflow'，value 是子智能体配置
    # _key 前面加下划线是 Python 约定：我知道这个变量存在但不打算用它
    for _key, value in config["sub_agents"].items():
        # 💡 JS 类比：result.push({...})
        result.append({
            "name": value["name"],                          # 💡 JS 类比：value.name
            "description": value["description"].strip(),   # 💡 JS 类比：value.description.trim()
            "prompt_chars": len(value["system_prompt"]),    # 💡 JS 类比：value.system_prompt.length
        })

    return result
    # raise NotImplementedError("TODO 2：还没实现 list_subagents")


# ============================================================
# TODO 3：关键词路由（模拟主智能体的决策）
# ============================================================
# 💡 JS 类比：const routeRules = { "市场情报助手": ["竞品", "市场", ...], ... }
# 路由表：子智能体名称 -> 触发关键词列表
ROUTE_RULES = {
    "市场情报助手": ["竞品", "市场", "新闻", "趋势", "行业", "消费者"],
    "数据分析助手": ["销量", "库存", "订单", "数据库", "数据", "指标", "营收"],
    "内部知识助手": ["sop", "复盘", "政策", "知识库", "文档", "手册", "流程"],
}


def route_query(query: str) -> list[str]:
    """
    根据用户问题，返回需要调用的子智能体名称列表。

    规则：
      - 命中多个助手的多个关键词时，返回多个（按 ROUTE_RULES 顺序）
      - 一个都没命中时，默认返回 ["市场情报助手"]
      - 关键词匹配不区分大小写（用 query.lower()）

    语法点：
      - .lower() 转小写（≈ JS 的 .toLowerCase()）
      - k in q 判断子串是否存在（≈ JS 的 q.includes(k)）
      - break 跳出内层循环（JS 也有 break）
      - hits or ["市场情报助手"] 兜底（JS 用 hits.length ? hits : ["市场情报助手"]）

    示例：
      "最近竞品有什么动作"            -> ["市场情报助手"]
      "查一下上月销量和库存"          -> ["数据分析助手"]
      "结合竞品动态和我们的库存数据"  -> ["市场情报助手", "数据分析助手"]
    """
    # 💡 JS 类比：const q = query.toLowerCase()
    q = query.lower()

    # 💡 JS 类比：const hits = []
    hits = []

    # 💡 JS 类比：for (const [name, keywords] of Object.entries(ROUTE_RULES))
    # 第一层：遍历每个子智能体的名称和它的关键词列表
    for name, keywords in ROUTE_RULES.items():
        matched = False

        # 💡 JS 类比：for (const k of keywords)
        # 第二层：逐个检查关键词，看有没有命中
        for k in keywords:
            # 💡 JS 类比：if (q.includes(k))
            if k in q:
                matched = True
                break  # 找到一个就够了，不用继续

        if matched:
            hits.append(name)

    # 💡 JS 类比：return hits.length ? hits : ["市场情报助手"]
    # Python 的 or 运算符也有短路行为：hits 非空就返回 hits，否则返回右边的兜底值
    return hits or ["市场情报助手"]
    # raise NotImplementedError("TODO 3：还没实现 route_query")


# ============================================================
# TODO 4：构造 tool_call
# ============================================================
# 💡 JS 类比：
#   function buildToolCall(subagentName: string, description: string): Record<string, any> {
#     return {
#       name: "task",
#       args: {
#         subagent_type: subagentName,
#         description: description,
#       }
#     };
#   }
def build_tool_call(subagent_name: str, description: str) -> dict:
    """
    构造 deepagents 调度子智能体时的 tool_call 结构（OpenAI 风格）。

    这就是一个嵌套字典，和 JS 对象写法几乎完全一样！

    语法点：
      - 字典里可以嵌套字典（dict 里再放 dict）
      - 返回的结构会被 deep_agent 框架解析，name="task" 是框架约定

    Args:
        subagent_name: 要调用的子智能体名称（如 "市场情报助手"）
        description: 给子智能体的任务描述（如 "搜索竞品动态"）

    Returns:
        dict: OpenAI function call 风格的工具调用字典
    """
    return {
        "name": "task",
        "args": {
            "subagent_type": subagent_name,
            "description": description,
        },
    }
    # raise NotImplementedError("TODO 4：还没实现 build_tool_call")


# ============================================================
# TODO 5：异步模拟执行
# ============================================================
# 💡 JS 类比：
#   async function runMockAgent(query: string): Promise<Record<string, any>> {
#     const routes = routeQuery(query);
#     const steps = [];
#     for (const route of routes) {
#       await new Promise(r => setTimeout(r, 50));  // ≈ await asyncio.sleep(0.05)
#       steps.push(`正在调用${route}`);
#     }
#     return {
#       query: query,
#       routes: routes,
#       steps: steps,
#       answer: `已完成：${routes.join('、')}`,
#     };
#   }
async def run_mock_agent(query: str) -> dict:
    """
    模拟主智能体的一次完整执行。

    语法点（重点！）：
      - async def 定义异步函数（≈ JS 的 async function）
      - await 暂停当前函数，等待异步操作完成（≈ JS 的 await）
      - asyncio.sleep(0.05) 异步等待 50ms（≈ JS 的 await new Promise(r => setTimeout(r, 50))）
      - "、".join(routes) 列表转字符串（≈ JS 的 routes.join('、')）
      - f"已完成：{'、'.join(routes)}" f-string 模板（≈ JS 的 `已完成：${routes.join('、')}`）

    执行流程：
      1. routes = route_query(query)
      2. 对每个 route：await asyncio.sleep(0.05) 模拟耗时，并追加一条步骤
      3. 汇总返回

    Args:
        query: 用户问题

    Returns:
        dict: 包含 query / routes / steps / answer 四个字段
    """
    routes = route_query(query)
    steps = []

    # 💡 JS 类比：for (const route of routes)
    for route in routes:
        # 💡 JS 类比：await new Promise(r => setTimeout(r, 50))
        # 异步 sleep 不会阻塞其他协程，这就是 async 的优势
        await asyncio.sleep(0.05)

        # 💡 JS 类比：steps.push(`正在调用${route}`)
        # f-string 是 Python 3.6+ 的模板字符串，比 .format() 更清爽
        steps.append(f"正在调用{route}")

    return {
        "query": query,
        "routes": routes,
        "steps": steps,
        # 💡 JS 类比：`已完成：${routes.join('、')}`
        # f-string 里可以直接放表达式，{'、'.join(routes)} 会先求值再拼接
        "answer": f"已完成：{'、'.join(routes)}",
    }
    # raise NotImplementedError("TODO 5：还没实现 run_mock_agent")


# ============================================================
# 本地自测入口（验收脚本会单独 import，不会执行这里）
# ============================================================
# 💡 JS 类比：if (import.meta.url === `file://${process.argv[1]}`) { ... }
# 这段只在你直接 python 今日练习.py 时执行，被其他文件 import 时不执行
# Python 约定：__name__ == "__main__" 就是「这个文件是主入口」的意思
if __name__ == "__main__":
    print("=" * 56)
    print("Day 1 练习自测")
    print("=" * 56)

    # ── 测试 TODO 1：load_config ──────────────────────────────────────────────
    try:
        config = load_config()
        print(f"[1] 配置加载成功，顶层键：{list(config.keys())}")
    except NotImplementedError as e:
        print(f"[1] 未完成：{e}")
        config = None

    # ── 测试 TODO 2：list_subagents ───────────────────────────────────────────
    if config:
        try:
            subs = list_subagents(config)
            print("[2] 子智能体：")
            for s in subs:
                print(f"    - {s['name']} | 提示词 {s['prompt_chars']} 字")
        except NotImplementedError as e:
            print(f"[2] 未完成：{e}")

    # ── 测试 TODO 3：route_query ──────────────────────────────────────────────
    try:
        print(f"[3] 路由测试：{route_query('结合竞品动态和我们的库存数据')}")
    except NotImplementedError as e:
        print(f"[3] 未完成：{e}")

    # ── 测试 TODO 4：build_tool_call ──────────────────────────────────────────
    try:
        print(f"[4] tool_call：{build_tool_call('市场情报助手', '搜索竞品动态')}")
    except NotImplementedError as e:
        print(f"[4] 未完成：{e}")

    # ── 测试 TODO 5：run_mock_agent ───────────────────────────────────────────
    try:
        # 💡 JS 类比：要在同步代码里跑 async 函数，用 await Promise.resolve(fn())
        # Python 用 asyncio.run() 来启动事件循环
        print(f"[5] 异步执行：{asyncio.run(run_mock_agent('查一下上月销量'))}")
    except NotImplementedError as e:
        print(f"[5] 未完成：{e}")

    print("\n完成后运行：python 验收_day1.py")
