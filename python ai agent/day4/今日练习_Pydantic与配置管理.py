"""
╔══════════════════════════════════════════════════════════════════════╗
║  Day 4 练习：Pydantic 数据建模 + 生产配置管理                            ║
╠══════════════════════════════════════════════════════════════════════╣
║  学习目标（5 个点，Day 3 的 dataclass 的「生产版」）                     ║
║    1. BaseModel：字段自动校验（dataclass 只声明不校验）                  ║
║    2. Field 约束：长度 / 范围 / 枚举，错误数据直接拒绝                    ║
║    3. 嵌套模型：一个配置里套多个子配置，逐层校验                          ║
║    4. model_dump / model_validate：模型 ↔ JSON 互转                     ║
║    5. BaseSettings：从 .env / 环境变量读配置（部署必备）                  ║
╠══════════════════════════════════════════════════════════════════════╣
║  规则：                                                                 ║
║    - 先自己写，卡住 10 分钟再看 参考实现_day4.py                          ║
║    - 每完成一个 TODO，就运行一次：python 验收_day4.py                     ║
╚══════════════════════════════════════════════════════════════════════╝

📖 Day 4 新增 Python ↔ TS/JS 对照速查表：
┌────────────────────────────────────────┬─────────────────────────────────────────────┐
│ Python (Pydantic)                      │ TypeScript / JavaScript                     │
├────────────────────────────────────────┼─────────────────────────────────────────────┤
│ class X(BaseModel):                    │ interface X { ... } + zod.object({...})     │
│ name: str                              │ name: string                                │
│ timeout: int = Field(ge=1, le=60)      │ z.number().min(1).max(60)                   │
│ name: str = Field(min_length=1)        │ z.string().min(1)                           │
│ Literal["a", "b"]                       │ z.enum(['a', 'b'])                          │
│ X(**data)                              │ XSchema.parse(data)                         │
│ X.model_validate(dict)                 │ XSchema.parse(obj)                          │
│ X.model_validate_json(str)             │ XSchema.parse(JSON.parse(str))              │
│ x.model_dump()                         │ JSON.parse → plain object / zod output      │
│ x.model_dump_json()                    │ JSON.stringify(x)                           │
│ ValidationError                        │ ZodError                                    │
│ BaseSettings                           │ dotenv + zod 校验环境变量                    │
│ SettingsConfigDict(env_file=".env")    │ dotenv.config({ path: '.env' })             │
└────────────────────────────────────────┴─────────────────────────────────────────────┘

🎯 学完 Day 4 你应该能回答：
  1. dataclass 和 BaseModel 的核心差别是什么？（为什么生产项目用后者）
  2. 为什么 `.env` 里的 `MAX_RETRIES=abc` 应该在启动时就报错，而不是跑到一半才崩？
  3. `model_dump()` 和 `model_dump_json()` 该分别用在什么场景？

💡 为什么要学这个？
  - 项目 .env 里有 LLM_API_KEY / LLM_MODEL / MAX_RETRIES 等配置
  - api/ 目录的 FastAPI 接口，请求体和响应体全靠 Pydantic 校验
  - 配置写错时，要在「启动那一刻」就失败，而不是在用户请求进来时 500
"""

from __future__ import annotations

import os
from typing import Literal

# 💡 Pydantic 是「运行时校验」库：声明一次，所有入口自动校验
#    ≈ 前端 zod / yup，但 Python 里它几乎成了事实标准
from pydantic import BaseModel, Field, ValidationError
# 💡 pydantic-settings 专门用来读环境变量 / .env 文件
from pydantic_settings import BaseSettings, SettingsConfigDict


# ============================================================
# TODO 1：BaseModel 基础 —— 子 Agent 配置模型
# ============================================================
# 对比 Day 3 的 dataclass：
#   dataclass 只有「形状」，类型写错也能跑（Python 不做运行时检查）
#   BaseModel 有「形状 + 校验」，类型不对立刻抛 ValidationError
#
# 💡 TS 类比：
#   // 如果只用 TS interface，运行时传入错误数据不会有任何报错
#   interface SubAgentConfig { name: string; description: string; ... }
#   // 用 zod 才有运行时校验：
#   const SubAgentConfig = z.object({ name: z.string(), ... })
#   Pydantic 的 BaseModel ≈ zod.object
class SubAgentConfig(BaseModel):
    """
    子 Agent 配置（Pydantic 版）。

    字段要求：
      - name: str，必填
      - description: str，必填
      - system_prompt: str，必填
      - tools: list[str]，默认空列表
      - kind: Literal["search", "db", "rag"]，默认 "search"

    💡 注意两个和 dataclass 不同的点：
      1. 默认值可以直接写 = []，Pydantic 会为每个实例深拷贝，不会共享
         （dataclass 必须用 field(default_factory=list)，这是个经典坑）
      2. 不需要写 __init__，BaseModel 自动生成
    """

    # TODO 1a：声明 name 字段（str，必填）
    # ---- 在下面写你的代码 ----
    name:str
    # TODO 1b：声明 description 字段（str，必填）
    # ---- 在下面写你的代码 ----
    description:str
    # TODO 1c：声明 system_prompt 字段（str，必填）
    # ---- 在下面写你的代码 ----
    system_prompt:str
    # TODO 1d：声明 tools 字段（list[str]，默认空列表）
    # 提示：tools: list[str] = []
    # ---- 在下面写你的代码 ----
    tools:list[str] = []
    # TODO 1e：声明 kind 字段（Literal 三选一，默认 "search"）
    # 提示：kind: Literal["search", "db", "rag"] = "search"
    # ---- 在下面写你的代码 ----
    kind: Literal["search", "db", "rag"] = "search"

# ============================================================
# TODO 2：Field 约束 —— 让错误数据进不来
# ============================================================
# 真实场景：工具配置里的超时不能是 0 或负数，名字不能是空字符串
# 用 Field(...) 把这些规则「写死在类型上」，比写 if 判断可靠得多
#
# 💡 TS/zod 类比：
#   z.object({
#     name: z.string().min(1).max(50),
#     timeout: z.number().int().min(1).max(60),
#     retries: z.number().int().min(0).max(5).default(3),
#   })
class ToolConfig(BaseModel):
    """
    工具配置（带约束）。

    字段要求：
      - name: str，长度 1~50
      - timeout: int，范围 1~60
      - retries: int，范围 0~5，默认 3
      - enabled: bool，默认 True
    """

    # TODO 2a：name 字段，str，min_length=1，max_length=50
    # 提示：name: str = Field(min_length=1, max_length=50)
    # ---- 在下面写你的代码 ----
    name:str = Field(min_length=1,max_length = 50)
    # TODO 2b：timeout 字段，int，ge=1，le=60
    # 提示：ge = greater or equal（>=），le = less or equal（<=）
    # ---- 在下面写你的代码 ----
    timeout: int = Field(ge=1, le=60)
    # TODO 2c：retries 字段，int，ge=0，le=5，默认 3
    # ---- 在下面写你的代码 ----
    retries:int = Field(ge=0, le=5,default=3)
    # TODO 2d：enabled 字段，bool，默认 True
    # ---- 在下面写你的代码 ----
    enabled:bool = True

# ============================================================
# TODO 3：嵌套模型 —— 一个配置里装多个子配置
# ============================================================
# 项目场景：prompt/prompts.yml 里 main_agent + 3 个 sub_agents
# 用嵌套模型后，任何一个子配置写错，整个配置在加载时就会失败
#
# 💡 TS/zod 类比：
#   const AgentConfig = z.object({
#     main_prompt: z.string(),
#     sub_agents: z.array(SubAgentConfig),
#   })
class AgentConfig(BaseModel):
    """
    主配置：一个主提示词 + 若干子 Agent。

    字段要求：
      - main_prompt: str，必填
      - sub_agents: list[SubAgentConfig]，默认空列表

    💡 嵌套校验：传入 sub_agents 里的 dict 会被自动转成 SubAgentConfig 并校验
       （这是 Pydantic 最爽的地方，不需要你手写循环）
    """

    # TODO 3a：main_prompt 字段（str，必填）
    # ---- 在下面写你的代码 ----
    main_prompt: str
    # TODO 3b：sub_agents 字段（list[SubAgentConfig]，默认空列表）
    # 提示：sub_agents: list[SubAgentConfig] = []
    # ---- 在下面写你的代码 ----
    sub_agents:list[SubAgentConfig] = []

# ============================================================
# TODO 4：序列化 —— 模型 ↔ JSON
# ============================================================
# 场景：配置存成 JSON 文件、API 返回响应、写入日志，都需要互转
#
# 💡 JS 类比：
#   JSON.stringify(agentConfig)   ≈  agent_config.model_dump_json()
#   JSON.parse(text)              ≈  AgentConfig.model_validate_json(text)
#   {...agentConfig}              ≈  agent_config.model_dump()
def config_to_json(config: AgentConfig) -> str:
    """
    模型 → JSON 字符串。

    Args:
        config: AgentConfig 实例

    Returns:
        str: JSON 字符串（ensure_ascii=False 保证中文不转义）

    💡 注意：model_dump_json() 默认会把中文转成 \\uXXXX，
       如果要做成人类可读的文件，应该用 json.dumps(model_dump(), ensure_ascii=False)
    """
    # TODO 4a：返回中文可读的 JSON 字符串
    # 提示：
    #   import json 已在文件顶部？没有的话直接在这里用
    #   写法：json.dumps(config.model_dump(), ensure_ascii=False, indent=2)
    # ---- 在下面写你的代码 ----
    pass


def config_from_json(text: str) -> AgentConfig:
    """
    JSON 字符串 → 模型（自动校验）。

    Args:
        text: JSON 字符串

    Returns:
        AgentConfig: 校验通过的模型实例

    💡 model_validate_json 一步完成「解析 + 校验 + 转换」，
       ≈ TS 的 XSchema.parse(JSON.parse(text))
    """
    # TODO 4b：从 JSON 字符串还原并校验
    # 提示写法：return AgentConfig.model_validate_json(text)
    # ---- 在下面写你的代码 ----
    pass


# ============================================================
# TODO 5：BaseSettings —— 从环境变量 / .env 读配置
# ============================================================
# 生产场景：API Key 绝不能写进代码，必须从环境变量读
# 项目根目录的 .env 大概长这样：
#   LLM_API_KEY=sk-xxxxxxxx
#   LLM_MODEL=deepseek-chat
#   MAX_RETRIES=3
#   DEBUG=false
#
# 💡 JS/Node 类比：
#   require('dotenv').config();            // 加载 .env
#   const apiKey = process.env.LLM_API_KEY; // 但这是字符串，没校验
#   BaseSettings = dotenv + 类型校验 + 默认值，三合一
class AppSettings(BaseSettings):
    """
    应用配置（从环境变量读取）。

    💡 SettingsConfigDict 的配置项：
      - env_file=".env"      ：从 .env 文件读（文件不存在不报错）
      - extra="ignore"       ：环境里有别的变量时忽略，不报错
      - case_sensitive=False ：LLM_API_KEY 能匹配 llm_api_key（默认就是 False）

    字段要求：
      - llm_api_key: str，必填（没有默认值 = 没配就启动失败，这正是我们要的）
      - llm_model: str，默认 "deepseek-chat"
      - max_retries: int，默认 3
      - debug: bool，默认 False
    """

    # TODO 5a：配置 SettingsConfigDict
    # 提示：
    #   model_config = SettingsConfigDict(env_file=".env", extra="ignore")
    # ---- 在下面写你的代码 ----

    # TODO 5b：llm_api_key 字段（str，必填）
    # ---- 在下面写你的代码 ----

    # TODO 5c：llm_model 字段（str，默认 "deepseek-chat"）
    # ---- 在下面写你的代码 ----

    # TODO 5d：max_retries 字段（int，默认 3）
    # ---- 在下面写你的代码 ----

    # TODO 5e：debug 字段（bool，默认 False）
    # ---- 在下面写你的代码 ----


# ============================================================
# 本地自测入口
# ============================================================
if __name__ == "__main__":
    print("=" * 60)
    print("Day 4 练习自测")
    print("=" * 60)

    # ── TODO 1 ───────────────────────────────────────────────────────────
    try:
        cfg = SubAgentConfig(
            name="市场情报助手",
            description="搜索市场信息",
            system_prompt="你是市场分析专家",
        )
        print(f"[1] SubAgentConfig：{cfg.name} | kind={cfg.kind} | tools={cfg.tools}")
    except Exception as e:
        print(f"[1] 未完成或失败：{type(e).__name__}: {e}")

    # ── TODO 2 ───────────────────────────────────────────────────────────
    try:
        tool = ToolConfig(name="search", timeout=10)
        print(f"[2] ToolConfig：{tool.model_dump()}")
        # 故意传错误数据，验证校验真的生效
        try:
            ToolConfig(name="", timeout=10)
            print("    ⚠️ 空 name 竟然通过了，约束没生效")
        except ValidationError:
            print("    ✅ 空 name 被正确拒绝")
    except Exception as e:
        print(f"[2] 未完成或失败：{type(e).__name__}: {e}")

    # ── TODO 3 ───────────────────────────────────────────────────────────
    try:
        agent = AgentConfig(
            main_prompt="你是主调度 Agent",
            sub_agents=[
                {"name": "市场情报助手", "description": "搜索", "system_prompt": "你是市场专家"},
                {"name": "数据分析助手", "description": "查库", "system_prompt": "你是数据专家"},
            ],
        )
        print(f"[3] AgentConfig：{len(agent.sub_agents)} 个子 Agent")
    except Exception as e:
        print(f"[3] 未完成或失败：{type(e).__name__}: {e}")

    # ── TODO 4 ───────────────────────────────────────────────────────────
    try:
        text = config_to_json(agent)
        back = config_from_json(text)
        print(f"[4] JSON 往返：{back.sub_agents[0].name}（长度 {len(text)} 字符）")
    except Exception as e:
        print(f"[4] 未完成或失败：{type(e).__name__}: {e}")

    # ── TODO 5 ───────────────────────────────────────────────────────────
    # 先临时注入一个环境变量，模拟 .env
    os.environ.setdefault("LLM_API_KEY", "sk-test-from-env")
    try:
        settings = AppSettings()
        print(f"[5] AppSettings：model={settings.llm_model} | retries={settings.max_retries}")
        print(f"    api_key 已从环境变量读取：{settings.llm_api_key[:6]}...")
    except Exception as e:
        print(f"[5] 未完成或失败：{type(e).__name__}: {e}")

    print("\n完成后运行：python 验收_day4.py")
