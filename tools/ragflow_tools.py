"""
╔══════════════════════════════════════════════════════════════════════╗
║  文件：tools/ragflow_tools.py                                           ║
║  角色：RAGFlow 知识库查询——让 Agent 能查内部文档（SOP/复盘/手册等）      ║
║  JS 类比：≈ src/tools/ragflowClient.ts                                  ║
║  被谁用：agent/subagents/knowledge_base_agent.py 的 tools 列表           ║
╚══════════════════════════════════════════════════════════════════════╝

📖 语法速览（重点：流式响应处理 + 临时会话模式）：
  - session.ask(question=..., stream=True)   ← 流式提问，返回迭代器
  - for part in response: result = part.content  ← 每次拿一小块内容
  - create_ask_delete 函数名                 ← 三个动作：create → ask → delete

🎯 读完你应该能说清：
  1. 为什么要 create → ask → delete 三步？（提示：用完即删，不留痕迹）
  2. 流式响应怎么处理的？（提示：for 循环逐块取 content）
  3. 为什么要先 get_assistant_list？（提示：模型不知道有哪些知识库助手可用）
"""

from langchain_core.tools import tool
from ragflow_sdk import RAGFlow
from api.monitor import monitor
from rawflow.rag_config import _load_ragflow_env

api_key, base_url = _load_ragflow_env()
ragflow_client = RAGFlow(api_key=api_key, base_url=base_url)


# ═══════════════════════════════════════════════════════════════════════════
# get_assistant_list：列出所有知识库助手
# ═══════════════════════════════════════════════════════════════════════════
# 💡 类比：先问「有哪些助手可用」，再决定向哪个助手提问
#    就像你不知道公司有哪个知识库，得先搜一下有哪些
@tool
def get_assistant_list() -> str:
    """
    查询 ragflow 服务器中有哪些助手和助手关联的知识库信息！
    供模型参考：我可以向哪个助手提问来获取内部文档信息？
    强调：想向某个助手提问，必须先调这个工具查助手名称
    """
    monitor.report_tool(tool_name="ragflow聊天助手列表查询工具：get_assistant_list")

    try:
        # 💡 list_chats() 返回所有聊天助手（RAGFlow 的聊天助手 ≈ 一个知识库 + 一个模型）
        chat_list = ragflow_client.list_chats()
        if not chat_list:
            return "没有任何可用助手"

        count_chat_info = ""
        for chat in chat_list:
            # 💡 chat.datasets 是这个助手关联的知识库列表
            dataset_names = []
            dataset_list = chat.datasets
            if dataset_list and isinstance(dataset_list, list):
                for dataset in dataset_list:
                    dataset_names.append(dataset['name'])

            # 💡 拼一行：助手名 + 描述 + 关联知识库
            count_chat_info += (
                f"助手名称:{chat.name};功能介绍：{chat.description}; "
                f"关联的知识库：{'、'.join(dataset_names)}\n"
            )
        return count_chat_info
    except Exception as e:
        return f"查询助手信息异常，无可用助手,异常信息:{str(e)}"


# ═══════════════════════════════════════════════════════════════════════════
# create_ask_delete：向某个助手提问（临时会话）
# ═══════════════════════════════════════════════════════════════════════════
# 💡 为什么叫这个名字？三个动作连贯执行：
#   1. create_session  —— 临时建个会话（只用来问这一次）
#   2. ask             —— 流式提问拿答案
#   3. delete_sessions —— 问完就删，不留痕迹（防止 RAGFlow 会话数被刷爆）
@tool
def create_ask_delete(chat_name, question)->str:
    """
    向某个助手创建单次会话进行提问，提问完毕后关闭会话！
    注意：调用前必须先 get_assistant_list 明确助手名称
    :param chat_name: 助手名字（上一个工具告诉模型的）
    :param question: 本次提问的问题
    """
    monitor.report_tool(tool_name="ragflow提问助手工具：create_ask_delete",
                       args={"chat_name": chat_name, "question": question})

    try:
        chats = ragflow_client.list_chats(name=chat_name)
        use_chat = chats[0]  # 💡 取第一个匹配的助手

        # 1. 创建临时会话
        session = use_chat.create_session(name="temp_session_ask")

        # 2. 流式提问（stream=True 让 RAGFlow 逐块返回）
        response = session.ask(question=question, stream=True)

        # 💡 处理流式响应：for 循环逐块取 content
        #   RAGFlow 每收到一块就 yield 出来，我们一直覆盖 result 直到最后一块
        result = ""
        for part in response:
            result = part.content

        # 3. 用完即删（防止 RAGFlow 会话被刷爆）
        use_chat.delete_sessions(ids=[session.id])

        return result
    except Exception as e:
        return f"提问失败，错误原因：{str(e)}"
