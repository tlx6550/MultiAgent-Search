"""
╔══════════════════════════════════════════════════════════════════════╗
║  Day 1 参考实现（仅供参考！自己先写，卡住 10 分钟再看）                   ║
╠══════════════════════════════════════════════════════════════════════╣
║  使用方式：                                                             ║
║    1. 先自己写 今日练习_python基础与Agent入门.py                        ║
║    2. 卡住超过 10 分钟再看这里                                          ║
║    3. 看完关掉，凭记忆重写一遍                                          ║
║    4. 验收通过后，再回来对照看为什么这样写                               ║
╚══════════════════════════════════════════════════════════════════════╝

📖 Python ↔ JS 对照速查（本文件用到的全部语法）：
┌───────────────────────────┬──────────────────────────────────────────┐
│ Python                    │ JavaScript                               │
├───────────────────────────┼──────────────────────────────────────────┤
│ dict = {"k": "v"}         │ const obj = { k: "v" }                   │
│ for k, v in obj.items():  │ for (const [k, v] of Object.entries(obj))│
│ v["key"]                  │ v.key 或 v["key"]                        │
│ k in str                  │ str.includes(k)                          │
│ "、".join(arr)            │ arr.join("、")                           │
│ f"{a}-{b}"                │ `${a}-${b}`                              │
│ async def / await         │ async function / await                   │
│ asyncio.sleep(0.05)      │ await new Promise(r=>setTimeout(r,50))   │
│ Path(__file__).parents[1] │ path.resolve(__dirname, '..')            │
│ Path(a) / "b"             │ path.join(a, "b")                        │
│ yaml.safe_load(f)         │ yaml.parse(content)                      │
└───────────────────────────┴──────────────────────────────────────────┘
"""

from __future__ import annotations

import asyncio
from pathlib import Path

import yaml

# ── 路径计算 ────────────────────────────────────────────────────────────────
# 💡 JS 类比：const projectRoot = path.resolve(__dirname, '..', '..')
PROJECT_ROOT = Path(__file__).resolve().parents[2]

# 💡 JS 类比：path.join(projectRoot, 'prompt', 'prompts.yml')
PROMPTS_PATH = PROJECT_ROOT / "prompt" / "prompts.yml"


# ═══════════════════════════════════════════════════════════════════════════
# TODO 1：load_config
# ═══════════════════════════════════════════════════════════════════════════
# 💡 JS 类比：
#   function loadConfig(): Record<string, any> {
#     const content = fs.readFileSync(PROMPTS_PATH, 'utf-8');
#     return yaml.parse(content);
#   }
def load_config() -> dict:
    """读取 YAML 配置，返回 dict。with 自动关闭文件，safe_load 安全解析。"""
    with open(PROMPTS_PATH, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


# ═══════════════════════════════════════════════════════════════════════════
# TODO 2：list_subagents
# ═══════════════════════════════════════════════════════════════════════════
# 💡 JS 类比：
#   function listSubagents(config) {
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
    """从 sub_agents 字典提取 name / description / prompt_chars，返回 list[dict]。"""
    result = []
    # 💡 JS 类比：for (const [_key, value] of Object.entries(config.sub_agents))
    for _key, value in config["sub_agents"].items():
        result.append({
            "name": value["name"],                          # 💡 value.name
            "description": value["description"].strip(),   # 💡 value.description.trim()
            "prompt_chars": len(value["system_prompt"]),    # 💡 value.system_prompt.length
        })
    return result


# ═══════════════════════════════════════════════════════════════════════════
# TODO 3：route_query（路由表）
# ═══════════════════════════════════════════════════════════════════════════
# 💡 JS 类比：
#   const ROUTE_RULES = {
#     "市场情报助手": ["竞品", "市场", "新闻", "趋势", "行业", "消费者"],
#     "数据分析助手": ["销量", "库存", "订单", "数据库", "数据", "指标", "营收"],
#     "内部知识助手": ["sop", "复盘", "政策", "知识库", "文档", "手册", "流程"],
#   };
ROUTE_RULES = {
    "市场情报助手": ["竞品", "市场", "新闻", "趋势", "行业", "消费者"],
    "数据分析助手": ["销量", "库存", "订单", "数据库", "数据", "指标", "营收"],
    "内部知识助手": ["sop", "复盘", "政策", "知识库", "文档", "手册", "流程"],
}

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 路由执行图解（查询 q = "结合竞品动态和我们的库存数据"，已转小写）
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#
# ━━━ 外层第1次：name="市场情报助手", keywords=[竞品,市场,新闻,趋势,行业,消费者] ━━━
#   ┃
#   ┣━ 中层第1次：k="竞品"  → 判断："竞品" in q ?  ✅ True
#   ┃              → matched=True, break
#   ┃
#   ┗━ matched=True → hits.append("市场情报助手")  ✅ 收进去！
#
# ━━━ 外层第2次：name="数据分析助手", keywords=[销量,库存,订单,数据库,数据,指标,营收] ━━━
#   ┃
#   ┣━ 中层第1次：k="销量"  → 判断："销量" in q ?  ❌ False，继续
#   ┣━ 中层第2次：k="库存"  → 判断："库存" in q ?  ✅ True
#   ┃              → matched=True, break
#   ┃
#   ┗━ matched=True → hits.append("数据分析助手")  ✅ 收进去！
#
# ━━━ 外层第3次：name="内部知识助手", keywords=[sop,复盘,政策,知识库,文档,手册,流程] ━━━
#   ┃
#   ┣━ 中层挨个试：没有一个命中
#   ┃
#   ┗━ matched=False → 跳过，不加入
#
# 最终 hits = ["市场情报助手", "数据分析助手"]
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
def route_query(query: str) -> list[str]:
    """根据用户问题，返回需要调用的子智能体名称列表。"""
    q = query.lower()       # 💡 const q = query.toLowerCase()
    hits = []               # 💡 const hits = []

    # 💡 for (const [name, keywords] of Object.entries(ROUTE_RULES))
    for name, keywords in ROUTE_RULES.items():
        matched = False
        for k in keywords:
            if k in q:      # 💡 if (q.includes(k))
                matched = True
                break       # 找到一个关键词就够了，不用继续
        if matched:
            hits.append(name)

    # 💡 return hits.length ? hits : ["市场情报助手"]
    # Python 的 or 运算符：hits 非空就返回 hits，否则走兜底
    return hits or ["市场情报助手"]


# ═══════════════════════════════════════════════════════════════════════════
# TODO 4：build_tool_call
# ═══════════════════════════════════════════════════════════════════════════
# 💡 JS 类比：
#   function buildToolCall(subagentName, description) {
#     return {
#       name: "task",
#       args: {
#         subagent_type: subagentName,
#         description: description,
#       }
#     };
#   }
def build_tool_call(subagent_name: str, description: str) -> dict:
    """构造 OpenAI 风格的 tool_call 字典，嵌套 dict 和 JS 对象几乎一样。"""
    return {
        "name": "task",
        "args": {
            "subagent_type": subagent_name,
            "description": description,
        },
    }


# ═══════════════════════════════════════════════════════════════════════════
# TODO 5：run_mock_agent
# ═══════════════════════════════════════════════════════════════════════════
# 💡 JS 类比：
#   async function runMockAgent(query) {
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
    """异步模拟主智能体执行：路由 → 逐个调用 → 汇总返回。"""
    routes = route_query(query)
    steps = []
    for route in routes:
        # 💡 JS 类比：await new Promise(r => setTimeout(r, 50))
        # 异步 sleep 不阻塞其他协程，这就是 async 的优势
        await asyncio.sleep(0.05)
        # 💡 JS 类比：steps.push(`正在调用${route}`)
        steps.append(f"正在调用{route}")

    return {
        "query": query,
        "routes": routes,
        "steps": steps,
        # 💡 JS 类比：`已完成：${routes.join('、')}`
        "answer": f"已完成：{'、'.join(routes)}",
    }


# ── 本地自测 ────────────────────────────────────────────────────────────────
# 💡 JS 类比：if (import.meta.url === `file://${process.argv[1]}`) { ... }
if __name__ == "__main__":
    print("配置顶层键：", list(load_config().keys()))
    print("子智能体：", list_subagents(load_config()))
    print("路由：", route_query("结合竞品动态和我们的库存数据"))
    print("tool_call：", build_tool_call("市场情报助手", "搜索竞品动态"))
    print("异步执行：", asyncio.run(run_mock_agent("查一下上月销量")))
