"""
╔══════════════════════════════════════════════════════════════════════╗
║  文件：agent/llm.py                                                    ║
║  角色：大模型（LLM）初始化入口，整个项目只在这里创建一次模型实例       ║
║  JS 类比：≈ src/api/llmClient.ts（前端里创建一个全局 axios 实例）       ║
║  被谁用：agent/main_agent.py 通过 `from agent.llm import model` 引用  ║
╚══════════════════════════════════════════════════════════════════════╝

📖 语法速览（前端工程师版）：
  - import ... from ...   ≈ JS 的 import ... from ...（几乎一样）
  - import os             ≈ JS 的 import * as os from 'node:os'
  - os.getenv("KEY")      ≈ JS 的 process.env.KEY（读取环境变量）
  - 顶层 model = ...      ≈ JS 模块顶层 export const model = ...（只执行一次，单例）

🎯 读完这个文件你应该能说清：
  1. 大模型实例叫什么名字？在哪里创建的？
  2. API Key 从哪来？不用写死在代码里对吧？
  3. 为什么只在这里创建一次？（提示：main_agent.py 直接 import 这个变量）
"""

# ── dotenv：从 .env 文件加载环境变量 ──────────────────────────────────────
# 💡 JS 类比：import dotenv from 'dotenv'; dotenv.config()
# 语法点：from ... import ... 可以只导入需要的函数（不像 JS 要解构）
from dotenv import load_dotenv, find_dotenv

# 💡 JS 类比：import * as os from 'node:os'（但 Python 的 os 是内置模块）
import os

# 💡 JS 类比：import { initChatModel } from '@langchain/langchat'
# langchain.chat_models 提供统一的模型初始化函数，支持多种大模型厂商
from langchain.chat_models import init_chat_model


# ── 加载 .env ───────────────────────────────────────────────────────────────
# find_dotenv()：递归查找 .env 文件（从当前文件向上找）
# load_dotenv()：把 .env 里的 key=value 加载到 os.environ
# 💡 JS 类比：dotenv.config({ path: findEnvPath() })
load_dotenv(find_dotenv())


# ── 创建大模型实例（单例） ───────────────────────────────────────────────────
# 💡 JS 类比：
#   const model = initChatModel({
#     model: process.env.LLM_QWEN_MAX,
#     model_provider: 'openai'   // 用 OpenAI 兼容协议，所以国内模型也能接
#   })
#
# 语法点：
#   - 这里是模块顶层代码，被 import 时立即执行一次
#   - os.getenv("KEY") 读环境变量，避免把 API Key 写进代码（安全！）
#   - model_provider="openai" 表示用 OpenAI 兼容协议调用，
#     所以不管是 DeepSeek、通义、智谱，只要兼容这个协议都能接
#
# 🔑 环境变量说明（在 .env 文件里配）：
#   LLM_QWEN_MAX=你的模型名称（如 deepseek-chat）
#   OPENAI_API_KEY=你的 API Key
model = init_chat_model(
    model=os.getenv("LLM_QWEN_MAX"),       # 模型名，从 .env 读取
    model_provider="openai"                  # 兼容协议，国内模型通用
)
