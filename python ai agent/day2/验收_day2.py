"""
╔══════════════════════════════════════════════════════════════════════╗
║  Day 2 自动验收脚本                                                    ║
╠══════════════════════════════════════════════════════════════════════╣
║  用法：                                                                 ║
║    python 验收_day2.py                          # 验收你的练习文件      ║
║    python 验收_day2.py --file 参考实现_day2.py   # 验收参考实现          ║
║                                                                         ║
║  通过标准：6/6 PASS                                                     ║
╚══════════════════════════════════════════════════════════════════════╝

📖 本脚本用到的 Python 语法（Day 2 新增）：
┌───────────────────────────┬──────────────────────────────────────────┐
│ Python                    │ JavaScript                               │
├───────────────────────────┼──────────────────────────────────────────┤
│ import importlib.util     │ dynamic import()                         │
│ isinstance(x, Callable)   │ typeof x === 'function'                  │
│ isinstance(x, type)       │ typeof x === 'function' (class)          │
│ .__wrapped__              │ functools.wraps 保存的原函数引用          │
│ .__name__                 │ fn.name                                  │
│ .__doc__                  │ fn.toString() 或注释                     │
└───────────────────────────┴──────────────────────────────────────────┘
"""

from __future__ import annotations

import argparse
import importlib.util
import sys
import traceback
from pathlib import Path

HERE = Path(__file__).resolve().parent
DEFAULT_FILE = HERE / "今日练习_Python进阶与装饰器.py"


def load_module(file_path: Path):
    """动态导入任意 .py 文件（三步法：spec → module → exec）。"""
    spec = importlib.util.spec_from_file_location("day2_exercise", file_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"无法加载文件：{file_path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def check(name: str, fn):
    """统一测试入口，捕获 PASS/FAIL 并输出。"""
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
    # 测试 1：retry 装饰器
    # ═══════════════════════════════════════════════════════════════════════
    def t1():
        # flaky_search 默认前 2 次失败，重试 3 次，应该能成功
        fail_count = [2]
        result = m.flaky_search("test", fail_count=fail_count)
        assert "搜索成功" in result, f"应返回搜索成功，实际 {result}"
        assert fail_count[0] == 0, f"重试后 fail_count 应为 0，实际 {fail_count[0]}"

        # 测 @functools.wraps 是否保留了原函数名
        assert m.flaky_search.__name__ == "flaky_search", "装饰器应保留原函数名（@wraps）"
        return "retry 装饰器重试成功 + @wraps 保留函数名"

    results.append(check("1. retry 装饰器重试逻辑", t1))

    # ═══════════════════════════════════════════════════════════════════════
    # 测试 2：list_subagents_compact 列表推导式
    # ═══════════════════════════════════════════════════════════════════════
    def t2():
        fake_config = {
            "sub_agents": {
                "tavily": {"name": "市场情报助手", "description": " 搜索市场信息 ", "system_prompt": "p" * 20},
                "db": {"name": "数据分析助手", "description": "查询数据库", "system_prompt": "p" * 30},
            }
        }
        subs = m.list_subagents_compact(fake_config)
        assert isinstance(subs, list) and len(subs) == 2, "应返回 2 个子智能体"

        names = [s["name"] for s in subs]
        assert "市场情报助手" in names and "数据分析助手" in names, "名称必须正确"

        # 验证 .strip() 是否生效
        market = next(s for s in subs if s["name"] == "市场情报助手")
        assert market["description"] == "搜索市场信息", "description 应 strip() 去掉首尾空格"

        # 验证 prompt_chars 是正整数
        for s in subs:
            assert s["prompt_chars"] > 0, "prompt_chars 应为正整数"

        return f"推导式子智能体 {names}"

    results.append(check("2. 列表推导式子智能体", t2))

    # ═══════════════════════════════════════════════════════════════════════
    # 测试 3：register_tools *args/**kwargs
    # ═══════════════════════════════════════════════════════════════════════
    def t3():
        # 不传 registry，应该新建
        reg = m.register_tools("tool_a", "tool_b", name="测试集", version="1.0")
        assert isinstance(reg, dict), "应返回 dict"
        assert reg.get("name") == "测试集", "meta 应被合并进 registry"
        assert reg.get("version") == "1.0", "meta 应被合并进 registry"
        assert "tools" in reg and "tool_a" in reg["tools"], "tools 元组应存进 registry"
        assert "tool_b" in reg["tools"], "tools 元组应存进 registry"

        # 传入已有 registry，应该合并
        existing = {"owner": "alice"}
        reg2 = m.register_tools("tool_c", registry=existing, env="prod")
        assert reg2.get("owner") == "alice", "应保留原有 registry 内容"
        assert reg2.get("env") == "prod", "meta 应追加进已有 registry"
        assert "tool_c" in reg2["tools"], "新 tools 应追加"

        return f"registry keys: {list(reg.keys())}"

    results.append(check("3. register_tools *args/**kwargs", t3))

    # ═══════════════════════════════════════════════════════════════════════
    # 测试 4：safe_search 异常处理
    # ═══════════════════════════════════════════════════════════════════════
    def t4():
        # 正常情况
        success = m.safe_search("正常查询")
        assert isinstance(success, dict), "应返回 dict"
        assert "results" in success, "成功时应有 results 字段"
        assert "搜索成功" in success.get("results", ""), "成功信息应包含'搜索成功'"

        # 异常情况
        fail = m.safe_search("触发异常", mock_fail=True)
        assert isinstance(fail, dict), "应返回 dict"
        assert "error" in fail, "失败时应有 error 字段"
        assert fail.get("fallback") is True, "失败时 fallback 应为 True"

        return f"正常有 results, 异常有 error+fallback"

    results.append(check("4. safe_search 异常处理", t4))

    # ═══════════════════════════════════════════════════════════════════════
    # 测试 5：ToolRegistry 类 — 注册与调用
    # ═══════════════════════════════════════════════════════════════════════
    def t5():
        tr = m.ToolRegistry()
        tr.register("greet", lambda name: f"Hello, {name}!")

        result = tr.call("greet", "World")
        assert result == "Hello, World!", f"调用工具应返回正确结果，实际 {result}"

        # 不存在的工具应返回 None
        missing = tr.call("nonexist")
        assert missing is None, f"不存在的工具应返回 None，实际 {missing}"

        # 带 **kwargs 调用
        tr.register("calc", lambda a, b, op="+": f"{a}{op}{b}")
        calc = tr.call("calc", 3, 5, op="*")
        assert calc == "3*5", f"kwargs 应正确传递，实际 {calc}"

        return f"call('greet')='{result}', 不存在返回 None"

    results.append(check("5a. ToolRegistry 注册与调用", t5))

    # ═══════════════════════════════════════════════════════════════════════
    # 测试 6：ToolRegistry 类 — list_tools
    # ═══════════════════════════════════════════════════════════════════════
    def t6():
        tr = m.ToolRegistry()
        tr.register("tool_a", lambda: None)
        tr.register("tool_b", lambda: None)

        tools = tr.list_tools()
        assert isinstance(tools, list), "应返回 list"
        assert set(tools) == {"tool_a", "tool_b"}, f"应包含所有注册工具，实际 {tools}"

        # 空 registry 应返回空列表
        empty = m.ToolRegistry().list_tools()
        assert empty == [], f"空 registry 应返回空列表，实际 {empty}"

        return f"list_tools: {tools}"

    results.append(check("5b. ToolRegistry list_tools", t6))

    # ── 汇总 ────────────────────────────────────────────────────────────────
    passed = sum(results)
    print("-" * 64)
    print(f"结果：{passed}/{len(results)} PASS")
    if passed == len(results):
        print("Day 2 验收通过！现在试着给项目里的 @retry_with_backoff 和 @tool 写一句费曼笔记。")
        return 0
    print("还没通过。按上面的 FAIL 提示逐个补 TODO，再运行本脚本。")
    return 1


if __name__ == "__main__":
    sys.exit(main())
