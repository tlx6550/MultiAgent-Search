"""
╔══════════════════════════════════════════════════════════════════════╗
║  文件：agent/subagents/network_search_agent.py                        ║
║  角色：定义「网络搜索子智能体」——主 Agent 不知道怎么联网，让它去搜      ║
║  JS 类比：≈ const networkSearchAgent = { name, description, prompt }   ║
║  被谁用：agent/main_agent.py 的 subagents 列表里引用了它               ║
╚══════════════════════════════════════════════════════════════════════╝

📖 语法速览（前端工程师版）：
  - from xxx import yyy   ≈ JS 的 import { yyy } from 'xxx'
  - dict = { key: val }   ≈ JS 的 const obj = { key: val }（几乎完全一样！）
  - sub_agents_content['tavily']['name']   ≈ JS 的 obj.tavily.name 或 obj['tavily']['name']

🎯 读完这个文件你应该能说清：
  1. 子智能体本质上是什么？（提示：不是 class，不是 function，是一个 __dict__）
  2. 这个子智能体有哪 4 个关键字段？
  3. tools 里装的是什么？它和 main_agent.py 里的 tools 有什么区别？

💡 关键发现：
  子智能体不是一个独立运行的进程或模块！它就是一个纯配置的字典。
  deepagents 框架读到这个 dict，就知道：
    - 我叫啥？（name）
    - 我能干嘛？（description，模型用它判断要不要调我）
    - 我应该怎么想？（system_prompt，专属提示词）
    - 我有什么工具？（tools，可调用的函数列表）
"""

# ── 导入子智能体的提示词配置 ─────────────────────────────────────────────────
# 💡 JS 类比：import { sub_agents_content } from '../prompts'
# prompts.py 里已经 load 了 YAML，这里直接 import 那个 dict
from agent.prompts import sub_agents_content

# ── 导入搜索工具函数 ────────────────────────────────────────────────────────
# 💡 JS 类比：import { internet_search } from '../../tools/tavilyTool'
# 这个函数被 @tool 装饰过，deepagents 框架会把它自动注册成模型可调用的工具
from tools.tavily_tool import internet_search


# ═══════════════════════════════════════════════════════════════════════════
# 子智能体定义（核心就是一个字典！）
# ═══════════════════════════════════════════════════════════════════════════
# 💡 JS 类比：
#   const network_search_agent = {
#     name: sub_agents_content.tavily.name,
#     description: sub_agents_content.tavily.description,
#     system_prompt: sub_agents_content.tavily.system_prompt,
#     tools: [internet_search]
#   }
#
# 四个字段的含义：
#   name          —— 子智能体名称（模型调用时会显示）
#   description   —— 模型用它判断「这个问题要不要调我」
#   system_prompt —— 专属提示词，告诉子智能体遇到这类问题该怎么想、怎么回答
#   tools         —— 子智能体可以调用的工具函数列表
#
# 🔑 为什么这里用 sub_agents_content['tavily'] 而不是写死？
#    因为提示词可能会改，改 YAML 就行，不用改代码（配置和代码分离）
network_search_agent = {
    "name":          sub_agents_content['tavily']['name'],          # 市场情报助手
    "description":   sub_agents_content['tavily']['description'],   # 模型用它做路由判断
    "system_prompt": sub_agents_content['tavily']['system_prompt'], # 专属思考方式
    "tools":         [internet_search]                               # 它能调用的工具
}
