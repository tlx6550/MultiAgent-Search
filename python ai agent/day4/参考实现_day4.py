"""
╔══════════════════════════════════════════════════════════════════════╗
║  Day 4 参考实现（仅供参考！自己先写，卡住 10 分钟再看）                   ║
╠══════════════════════════════════════════════════════════════════════╣
║  使用方式：                                                             ║
║    1. 先自己写 今日练习_Pydantic与配置管理.py                           ║
║    2. 卡住超过 10 分钟再看这里                                          ║
║    3. 看完关掉，凭记忆重写一遍                                          ║
║    4. 验收通过后，再回来对照看为什么这样写                               ║
╚══════════════════════════════════════════════════════════════════════╝

📖 Day 4 Python ↔ TS/zod 对照（参考实现版本）：
┌──────────────────────────────────┬────────────────────────────────────────────┐
│ Pydantic                         │ zod / TypeScript                           │
├──────────────────────────────────┼────────────────────────────────────────────┤
│ class X(BaseModel)               │ z.object({ ... })                          │
│ Field(min_length=1)              │ z.string().min(1)                          │
│ Field(ge=1, le=60)               │ z.number().min(1).max(60)                  │
│ Literal["a","b"]                 │ z.enum(['a','b'])                          │
│ X(**data)                        │ XSchema.parse(data)                        │
│ model_validate_json(s)           │ XSchema.parse(JSON.parse(s))               │
│ model_dump()                     │ plain object / zod .parse 输出             │
│ BaseSettings                     │ dotenv + zod 校验环境变量                   │
└──────────────────────────────────┴────────────────────────────────────────────┘
"""

from __future__ import annotations

import json
import os
from typing import Literal

from pydantic import BaseModel, Field, ValidationError
from pydantic_settings import BaseSettings, SettingsConfigDict


# ═══════════════════════════════════════════════════════════════════════════
# TODO 1：BaseModel 基础
# ═══════════════════════════════════════════════════════════════════════════
class SubAgentConfig(BaseModel):
    """子 Agent 配置（Pydantic 版，自动校验）。"""

    name: str
    description: str
    system_prompt: str
    # 💡 Pydantic 里直接写 = [] 是安全的：
    #    内部会为每个实例深拷贝默认值，不会像 dataclass 那样共享同一个 list
    tools: list[str] = []
    # 💡 Literal 限定取值 ≈ TS 的 'search' | 'db' | 'rag'
    kind: Literal["search", "db", "rag"] = "search"

    # 💡 进阶（本次不强制）：加这行可以拒绝未知字段，防止配置里字段名写错却静默通过
    # model_config = ConfigDict(extra="forbid")


# ═══════════════════════════════════════════════════════════════════════════
# TODO 2：Field 约束
# ═══════════════════════════════════════════════════════════════════════════
class ToolConfig(BaseModel):
    """工具配置（带长度 / 范围约束）。"""

    # 💡 min_length / max_length 对字符串是字符数限制
    name: str = Field(min_length=1, max_length=50)
    # 💡 ge = greater or equal（>=），le = less or equal（<=）
    timeout: int = Field(ge=1, le=60)
    retries: int = Field(default=3, ge=0, le=5)
    enabled: bool = True


# ═══════════════════════════════════════════════════════════════════════════
# TODO 3：嵌套模型
# ═══════════════════════════════════════════════════════════════════════════
class AgentConfig(BaseModel):
    """主配置：一个主提示词 + 若干子 Agent。"""

    main_prompt: str
    # 💡 传入的 dict 会被自动转成 SubAgentConfig 并逐项校验
    #    ≈ zod 的 z.array(SubAgentConfig)
    sub_agents: list[SubAgentConfig] = []


# ═══════════════════════════════════════════════════════════════════════════
# TODO 4：序列化往返
# ═══════════════════════════════════════════════════════════════════════════
def config_to_json(config: AgentConfig) -> str:
    """模型 → 中文可读的 JSON 字符串。"""
    # 💡 model_dump() 先转成普通 dict（≈ {...model}），再用 json.dumps 控制格式
    #    为什么不直接用 model_dump_json()？
    #    因为它默认把中文转义成 \uXXXX，存文件后人类看不懂
    return json.dumps(config.model_dump(), ensure_ascii=False, indent=2)


def config_from_json(text: str) -> AgentConfig:
    """JSON 字符串 → 模型（解析 + 校验 + 转嵌套模型，一步完成）。"""
    # 💡 ≈ zod 的 XSchema.parse(JSON.parse(text))
    return AgentConfig.model_validate_json(text)


# ═══════════════════════════════════════════════════════════════════════════
# TODO 5：BaseSettings 环境变量配置
# ═══════════════════════════════════════════════════════════════════════════
class AppSettings(BaseSettings):
    """
    应用配置，从环境变量 / .env 读取。

    .env 示例（放在项目根目录）：
      LLM_API_KEY=sk-xxxxxxxx
      LLM_MODEL=deepseek-chat
      MAX_RETRIES=3
      DEBUG=false
    """

    # 💡 env_file：文件不存在不报错（本地开发可以先不建）
    #    extra="ignore"：环境里有多余变量时忽略，不报错
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # 💡 没有默认值 = 必填：没配 KEY 时启动就失败，这正是生产想要的效果
    llm_api_key: str
    llm_model: str = "deepseek-chat"
    max_retries: int = 3
    debug: bool = False


# ── 本地自测 ────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("=" * 60)
    print("Day 4 参考实现自测")
    print("=" * 60)

    # TODO 1
    cfg = SubAgentConfig(
        name="市场情报助手",
        description="搜索市场信息",
        system_prompt="你是市场分析专家",
    )
    print(f"[1] SubAgentConfig：{cfg.name} | kind={cfg.kind} | tools={cfg.tools}")

    # TODO 2
    tool = ToolConfig(name="search", timeout=10)
    print(f"[2] ToolConfig：{tool.model_dump()}")
    try:
        ToolConfig(name="", timeout=10)
    except ValidationError as e:
        print(f"    ✅ 空 name 被拒绝（{e.error_count()} 条错误）")

    # TODO 3
    agent = AgentConfig(
        main_prompt="你是主调度 Agent",
        sub_agents=[
            {"name": "市场情报助手", "description": "搜索", "system_prompt": "市场专家"},
            {"name": "数据分析助手", "description": "查库", "system_prompt": "数据专家"},
        ],
    )
    print(f"[3] AgentConfig：{len(agent.sub_agents)} 个子 Agent，"
          f"首个类型={type(agent.sub_agents[0]).__name__}")

    # TODO 4
    text = config_to_json(agent)
    back = config_from_json(text)
    print(f"[4] JSON 往返：{back.sub_agents[0].name}（{len(text)} 字符）")

    # TODO 5
    os.environ.setdefault("LLM_API_KEY", "sk-test-from-env")
    settings = AppSettings()
    print(f"[5] AppSettings：model={settings.llm_model} | retries={settings.max_retries}")
