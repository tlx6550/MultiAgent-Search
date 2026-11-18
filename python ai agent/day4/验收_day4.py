"""
╔══════════════════════════════════════════════════════════════════════╗
║  Day 4 自动验收脚本                                                    ║
╠══════════════════════════════════════════════════════════════════════╣
║  用法：                                                                 ║
║    python 验收_day4.py                          # 验收你的练习文件      ║
║    python 验收_day4.py --file 参考实现_day4.py   # 验收参考实现          ║
║                                                                         ║
║  通过标准：6/6 PASS                                                     ║
╚══════════════════════════════════════════════════════════════════════╝
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import os
import sys
import traceback
from pathlib import Path

from pydantic import ValidationError

HERE = Path(__file__).resolve().parent
DEFAULT_FILE = HERE / "今日练习_Pydantic与配置管理.py"


def load_module(file_path: Path):
    """动态导入练习/参考实现文件。"""
    spec = importlib.util.spec_from_file_location("day4_exercise", file_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"无法加载文件：{file_path}")
    module = importlib.util.module_from_spec(spec)
    # 注册到 sys.modules，避免 Pydantic 解析前向引用时找不到模块
    sys.modules["day4_exercise"] = module
    spec.loader.exec_module(module)
    return module


def check(name: str, fn):
    """统一测试入口。"""
    try:
        detail = fn()
        print(f"[PASS] {name}" + (f" -> {detail}" if detail else ""))
        return True
    except NotImplementedError:
        print(f"[FAIL] {name} -> 还没实现，去补 TODO")
        return False
    except Exception as e:
        print(f"[FAIL] {name} -> {type(e).__name__}: {e}")
        return False


def expect_validation_error(fn, hint: str):
    """断言 fn() 必须抛 ValidationError。"""
    try:
        fn()
    except ValidationError:
        return
    raise AssertionError(f"应该被拒绝但通过了：{hint}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--file", default=str(DEFAULT_FILE), help="要验收的 Python 文件")
    args = parser.parse_args()

    target = Path(args.file)
    if not target.is_absolute():
        target = HERE / target
    if not target.exists():
        print(f"找不到文件：{target}")
        return 1

    print("=" * 64)
    print(f"验收目标：{target.name}")
    print("=" * 64)

    try:
        m = load_module(target)
    except Exception:
        print("[FAIL] 导入失败，先修复语法错误：")
        traceback.print_exc()
        return 1

    results = []

    # ═══════════════════════════════════════════════════════════════════════
    # 测试 1：BaseModel 基础
    # ═══════════════════════════════════════════════════════════════════════
    def t1():
        cfg = m.SubAgentConfig(
            name="市场情报助手",
            description="搜索市场信息",
            system_prompt="你是市场分析专家",
        )
        assert cfg.name == "市场情报助手", "name 字段不正确"
        assert cfg.tools == [], f"tools 默认应为空列表，实际 {cfg.tools}"
        assert cfg.kind == "search", f"kind 默认应为 'search'，实际 {cfg.kind}"

        # 关键：两个实例的 tools 不能共享（Pydantic 会自动深拷贝）
        a = m.SubAgentConfig(name="a", description="d", system_prompt="p")
        b = m.SubAgentConfig(name="b", description="d", system_prompt="p")
        a.tools.append("x")
        assert b.tools == [], "默认 list 被实例共享了（Pydantic 本应自动隔离）"

        # 必填字段缺失必须报错
        expect_validation_error(
            lambda: m.SubAgentConfig(name="只有名字"),
            "缺 description / system_prompt 应报错",
        )

        # kind 只接受三选一
        expect_validation_error(
            lambda: m.SubAgentConfig(
                name="x", description="d", system_prompt="p", kind="unknown"
            ),
            "kind='unknown' 应被 Literal 拒绝",
        )

        return "字段默认值、实例隔离、必填校验、Literal 限制全部正确"

    results.append(check("1. BaseModel 基础建模", t1))

    # ═══════════════════════════════════════════════════════════════════════
    # 测试 2：Field 约束
    # ═══════════════════════════════════════════════════════════════════════
    def t2():
        tool = m.ToolConfig(name="search", timeout=10)
        assert tool.retries == 3, f"retries 默认应为 3，实际 {tool.retries}"
        assert tool.enabled is True, "enabled 默认应为 True"

        # 空 name（违反 min_length=1）
        expect_validation_error(lambda: m.ToolConfig(name="", timeout=10), "空 name")

        # name 超长（违反 max_length=50）
        expect_validation_error(
            lambda: m.ToolConfig(name="x" * 51, timeout=10), "name 超过 50 字符"
        )

        # timeout 越界
        expect_validation_error(lambda: m.ToolConfig(name="a", timeout=0), "timeout=0")
        expect_validation_error(lambda: m.ToolConfig(name="a", timeout=61), "timeout=61")

        # retries 越界
        expect_validation_error(
            lambda: m.ToolConfig(name="a", timeout=10, retries=6), "retries=6"
        )

        # 合法边界值应通过
        m.ToolConfig(name="a", timeout=1, retries=0)
        m.ToolConfig(name="a" * 50, timeout=60, retries=5)

        return "5 类非法输入全部拒绝，边界值正常通过"

    results.append(check("2. Field 约束校验", t2))

    # ═══════════════════════════════════════════════════════════════════════
    # 测试 3：嵌套模型
    # ═══════════════════════════════════════════════════════════════════════
    def t3():
        agent = m.AgentConfig(
            main_prompt="你是主调度 Agent",
            sub_agents=[
                {"name": "市场情报助手", "description": "搜索", "system_prompt": "市场专家"},
                {"name": "数据分析助手", "description": "查库", "system_prompt": "数据专家"},
            ],
        )
        assert len(agent.sub_agents) == 2, "应解析出 2 个子 Agent"
        # 关键：dict 应被自动转成 SubAgentConfig 实例，而不是保持 dict
        assert isinstance(agent.sub_agents[0], m.SubAgentConfig), (
            f"子配置应自动转成 SubAgentConfig，实际 {type(agent.sub_agents[0]).__name__}"
        )

        # 子配置非法 → 整体失败（嵌套校验）
        expect_validation_error(
            lambda: m.AgentConfig(
                main_prompt="p",
                sub_agents=[{"name": "缺字段的助手"}],
            ),
            "子 Agent 缺 description 时整体应失败",
        )

        # 默认空列表
        assert m.AgentConfig(main_prompt="p").sub_agents == [], "sub_agents 默认应为空"

        return "2 个子配置自动转模型 + 嵌套校验生效"

    results.append(check("3. 嵌套模型校验", t3))

    # ═══════════════════════════════════════════════════════════════════════
    # 测试 4：序列化往返
    # ═══════════════════════════════════════════════════════════════════════
    def t4():
        agent = m.AgentConfig(
            main_prompt="主提示词",
            sub_agents=[
                {"name": "市场情报助手", "description": "搜索", "system_prompt": "市场专家",
                 "tools": ["internet_search"], "kind": "search"},
            ],
        )
        text = m.config_to_json(agent)
        assert isinstance(text, str), "config_to_json 必须返回 str"

        # 中文不能被转义成 \uXXXX
        assert "市场情报助手" in text, "JSON 里的中文被转义了，检查 ensure_ascii=False"

        # 必须是合法 JSON
        parsed = json.loads(text)
        assert parsed["sub_agents"][0]["name"] == "市场情报助手", "JSON 内容不正确"

        # 往返
        back = m.config_from_json(text)
        assert isinstance(back, m.AgentConfig), "还原结果应为 AgentConfig"
        assert back.main_prompt == "主提示词", "main_prompt 往返后不一致"
        assert back.sub_agents[0].tools == ["internet_search"], "tools 往返后不一致"
        assert back.sub_agents[0].kind == "search", "kind 往返后不一致"

        # 非法 JSON 内容应报错（这里用违反 Literal 约束的数据，不依赖 extra 配置）
        expect_validation_error(
            lambda: m.config_from_json(json.dumps({
                "main_prompt": "p",
                "sub_agents": [{"name": "x", "description": "d",
                                "system_prompt": "p", "kind": "unknown"}],
            })),
            "kind='unknown' 的 JSON 应被拒绝",
        )

        return f"往返一致，JSON 长度 {len(text)}"

    results.append(check("4. model_dump / model_validate 往返", t4))

    # ═══════════════════════════════════════════════════════════════════════
    # 测试 5：BaseSettings 环境变量
    #   注意：切到 day4 目录，确保 env_file=".env" 不会读到项目根的 .env
    # ═══════════════════════════════════════════════════════════════════════
    def t5():
        old_cwd = os.getcwd()
        old_key = os.environ.pop("LLM_API_KEY", None)
        old_model = os.environ.pop("LLM_MODEL", None)
        old_retries = os.environ.pop("MAX_RETRIES", None)
        old_debug = os.environ.pop("DEBUG", None)
        try:
            os.chdir(HERE)  # day4 目录下没有 .env

            # ① 注入环境变量，应能读到
            os.environ["LLM_API_KEY"] = "sk-verify-key"
            s = m.AppSettings()
            assert s.llm_api_key == "sk-verify-key", f"llm_api_key 读取失败：{s.llm_api_key}"
            assert s.llm_model == "deepseek-chat", f"llm_model 默认值错误：{s.llm_model}"
            assert s.max_retries == 3, f"max_retries 默认值错误：{s.max_retries}"
            assert s.debug is False, f"debug 默认值错误：{s.debug}"

            # ② 环境变量覆盖默认值
            os.environ["LLM_MODEL"] = "glm-4"
            os.environ["MAX_RETRIES"] = "5"
            os.environ["DEBUG"] = "true"
            s2 = m.AppSettings()
            assert s2.llm_model == "glm-4", "环境变量未覆盖 llm_model"
            assert s2.max_retries == 5, "环境变量未转成 int"
            assert s2.debug is True, "DEBUG=true 未转成 bool"

            # ③ 缺必填的 llm_api_key 应报错（生产环境启动即失败）
            del os.environ["LLM_API_KEY"]
            expect_validation_error(lambda: m.AppSettings(), "缺 LLM_API_KEY 时应启动失败")

            return "env 读取 / 类型转换 / 必填校验全部正确"
        finally:
            os.chdir(old_cwd)
            for k, v in [("LLM_API_KEY", old_key), ("LLM_MODEL", old_model),
                         ("MAX_RETRIES", old_retries), ("DEBUG", old_debug)]:
                if v is None:
                    os.environ.pop(k, None)
                else:
                    os.environ[k] = v

    results.append(check("5. BaseSettings 环境变量配置", t5))

    # ═══════════════════════════════════════════════════════════════════════
    # 测试 6：整合 —— 从 JSON 加载真实结构并统计
    # ═══════════════════════════════════════════════════════════════════════
    def t6():
        raw = json.dumps({
            "main_prompt": "你是多 Agent 调度核心",
            "sub_agents": [
                {"name": "市场情报助手", "description": "搜索竞品", "system_prompt": "市场专家",
                 "kind": "search", "tools": ["internet_search"]},
                {"name": "数据分析助手", "description": "查询数据库", "system_prompt": "数据专家",
                 "kind": "db", "tools": ["list_sql_tables", "execute_sql_query"]},
                {"name": "内部知识助手", "description": "检索知识库", "system_prompt": "知识专家",
                 "kind": "rag", "tools": ["search_knowledge"]},
            ],
        }, ensure_ascii=False)

        cfg = m.config_from_json(raw)
        assert len(cfg.sub_agents) == 3, "应加载 3 个子 Agent"

        kinds = [s.kind for s in cfg.sub_agents]
        assert kinds == ["search", "db", "rag"], f"kind 解析错误：{kinds}"

        total_tools = sum(len(s.tools) for s in cfg.sub_agents)
        assert total_tools == 4, f"工具总数应为 4，实际 {total_tools}"

        # 再 dump 一次，确保二次往返仍稳定
        again = m.config_from_json(m.config_to_json(cfg))
        assert [s.name for s in again.sub_agents] == [s.name for s in cfg.sub_agents], (
            "二次往返后子 Agent 顺序/名称发生变化"
        )

        return "3 个子 Agent、4 个工具、二次往返稳定"

    results.append(check("6. 整合：JSON 配置加载", t6))

    # ── 汇总 ────────────────────────────────────────────────────────────────
    passed = sum(results)
    print("-" * 64)
    print(f"结果：{passed}/{len(results)} PASS")
    if passed == len(results):
        print("Day 4 验收通过！去看项目 .env 和 api/ 目录，你现在能读懂每个字段的作用了。")
        return 0
    print("还没通过。按上面的 FAIL 提示逐个补 TODO，再运行本脚本。")
    return 1


if __name__ == "__main__":
    sys.exit(main())
