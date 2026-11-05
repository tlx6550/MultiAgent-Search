"""
╔══════════════════════════════════════════════════════════════════════╗
║  文件：agent/subagents/knowledge_base_agent.py                         ║
║  角色：定义「内部知识子智能体」——主 Agent 让它查 RAGFlow 知识库          ║
║  JS 类比：≈ const knowledgeBaseAgent = { tools: [getAssistantList, ...]} ║
╚══════════════════════════════════════════════════════════════════════╝

📖 语法速览：
  - 工具函数名很长？Python 鼓励 snake_case，不像 JS 用 camelCase
  - 💡 JS 类比：get_assistant_list ≈ getAssistantList

🎯 读完你应该能说清：
  1. 这个子智能体的两个工具是什么？
  2. 它们的调用顺序？（提示：先列出助手，再向某个助手提问）
"""

# 💡 JS 类比：import { sub_agents_content } from '../prompts'
from agent.prompts import sub_agents_content

# 💡 JS 类比：import { getAssistantList, createAskDelete } from '../../tools/ragflow'
# get_assistant_list —— 列出所有知识库助手
# create_ask_delete  —— 向某个助手提问（临时创建会话 → 提问 → 删会话，不留痕迹）
from tools.ragflow_tools import get_assistant_list, create_ask_delete


# ═══════════════════════════════════════════════════════════════════════════
# 知识库查询子智能体定义
# ═══════════════════════════════════════════════════════════════════════════
# 💡 JS 类比：const knowledge_base_agent = { name, description, prompt, tools }
#
# 调用逻辑：
#   1. get_assistant_list     —— 列出 RAGFlow 里所有可用的知识库助手
#   2. create_ask_delete      —— 向某个助手提问一次（临时会话，用完即删）
knowledge_base_agent = {
    "name":          sub_agents_content['ragflow']['name'],
    "description":   sub_agents_content['ragflow']['description'],
    "system_prompt": sub_agents_content['ragflow']['system_prompt'],
    "tools":         [get_assistant_list, create_ask_delete]
}
