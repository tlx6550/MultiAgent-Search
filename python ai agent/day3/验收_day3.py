"""
╔══════════════════════════════════════════════════════════════════════╗
║  Day 3 自动验收脚本                                                    ║
╠══════════════════════════════════════════════════════════════════════╣
║  用法：                                                                 ║
║    python 验收_day3.py                          # 验收你的练习文件      ║
║    python 验收_day3.py --file 参考实现_day3.py   # 验收参考实现          ║
║                                                                         ║
║  通过标准：6/6 PASS                                                     ║
║  注意：其中第 4 项验收的是 mini_agent/__init__.py，不是本练习文件         ║
╚══════════════════════════════════════════════════════════════════════╝
"""

from __future__ import annotations

import argparse
import asyncio
import importlib
import importlib.util
import sys
import time
import traceback
from pathlib import Path

# 验收脚本所在目录就是 day3/，把它加进 sys.path 才能 import mini_agent
HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

DEFAULT_FILE = HERE / "今日练习_异步编程与模块化.py"


def load_module(file_path: Path):
    """动态导入练习/参考实现文件。"""
    spec = importlib.util.spec_from_file_location("day3_exercise", file_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"无法加载文件：{file_path}")
    module = importlib.util.module_from_spec(spec)
    # ⚠️ 关键一步：必须先注册到 sys.modules，再 exec_module
    #    原因：@dataclass 内部会查 sys.modules[cls.__module__]，
    #    不注册就会拿到 None 并报 AttributeError（Day 1/2 没用到 dataclass 所以没暴露）
    sys.modules["day3_exercise"] = module
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
    # 测试 1：asyncio.gather 并发
    #   验收点：① 结果顺序与输入一致 ② 总耗时接近最慢的那个（说明真并发）
    # ═══════════════════════════════════════════════════════════════════════
    def t1():
        names = ["市场情报助手", "数据分析助手", "内部知识助手"]
        start = time.perf_counter()
        # 每个子 Agent 默认耗时 0.1s，并发总耗时应在 0.25s 内；串行则 > 0.3s
        out = asyncio.run(m.run_parallel(names))
        elapsed = time.perf_counter() - start

        assert isinstance(out, list) and len(out) == 3, f"应返回 3 条结果，实际 {out}"
        # 顺序必须和输入一致（gather 保证顺序，不是完成顺序）
        for i, name in enumerate(names):
            assert name in out[i], f"第 {i} 条结果应为 {name}，实际 {out[i]}"
        # 并发判断：串行至少 0.3s，这里放宽到 0.25s
        assert elapsed < 0.25, f"耗时 {elapsed:.2f}s 不像并发（应 < 0.25s）"

        return f"3 个子 Agent 并发完成，耗时 {elapsed:.2f}s（串行需 0.30s）"

    results.append(check("1. asyncio.gather 并发调度", t1))

    # ═══════════════════════════════════════════════════════════════════════
    # 测试 2：异步生成器 + async for
    # ═══════════════════════════════════════════════════════════════════════
    def t2():
        expected = "你好Agent"
        got = asyncio.run(m.collect_stream(expected))
        assert got == expected, f"流式拼回应为「{expected}」，实际「{got}」"

        # 再确认 stream_tokens 真的是「逐块」而不是一次性返回
        async def count_chunks():
            n = 0
            async for _ in m.stream_tokens("abcde"):
                n += 1
            return n

        chunks = asyncio.run(count_chunks())
        assert chunks == 5, f"5 个字符应产出 5 个 chunk，实际 {chunks}"

        return f"「{expected}」流式还原成功，共 {chunks} 个 chunk"

    results.append(check("2. 异步生成器流式输出", t2))

    # ══════════════════════════════════════════════════════════════════════
    # 测试 3：async with 资源管理
    # ═══════════════════════════════════════════════════════════════════════
    def t3():
        info = asyncio.run(m.use_session("temp_session", "差旅标准？"))

        assert info["entered"] is True, "__aenter__ 没有被执行（entered 应为 True）"
        assert info["exited"] is True, "__aexit__ 没有被执行（exited 应为 True）"
        assert "temp_session" in info["answer"], "ask 应带上会话名"

        # 额外验证：即使块内抛异常，__aexit__ 也要执行
        async def raise_inside():
            async with m.MockSession("err_session") as s:
                raise RuntimeError("故意报错")
            return s

        try:
            asyncio.run(raise_inside())
        except RuntimeError:
            pass  # __aexit__ 返回 False 时异常继续抛出，这是预期行为

        return f"enter/exit 均触发，answer={info['answer'][:24]}..."

    results.append(check("3. async with 上下文管理器", t3))

    # ═══════════════════════════════════════════════════════════════════════
    # 测试 4：包导出（验收 mini_agent/__init__.py，不是练习文件）
    # ═══════════════════════════════════════════════════════════════════════
    def t4():
        # 清掉可能存在的旧缓存，确保读到最新的 __init__.py
        for mod_name in list(sys.modules):
            if mod_name == "mini_agent" or mod_name.startswith("mini_agent."):
                del sys.modules[mod_name]
        importlib.invalidate_caches()

        pkg = importlib.import_module("mini_agent")

        for name in ["search_tool", "db_tool", "rag_tool", "quick_answer"]:
            assert hasattr(pkg, name), f"mini_agent 没有导出 {name}，检查 __init__.py"

        # __all__ 必须存在且包含四个名字
        assert hasattr(pkg, "__all__"), "__init__.py 缺少 __all__"
        for name in ["search_tool", "db_tool", "rag_tool", "quick_answer"]:
            assert name in pkg.__all__, f"__all__ 里缺少 {name}"

        # 实际调用一次，确认导出的是真函数
        answer = asyncio.run(pkg.quick_answer("查一下上月销量"))
        assert "查询结果" in answer, f"quick_answer 应路由到 db_tool，实际 {answer}"

        return f"__init__.py 导出正确，__all__={pkg.__all__}"

    results.append(check("4. mini_agent 包导出（__init__.py）", t4))

    # ═══════════════════════════════════════════════════════════════════════
    # 测试 5：dataclass 字段与默认值
    # ═══════════════════════════════════════════════════════════════════════
    def t5():
        # 只传必填字段，检查默认值
        cfg = m.SubAgentConfig(
            name="市场情报助手",
            description="搜索市场信息",
            system_prompt="你是市场专家",
        )
        assert cfg.name == "市场情报助手", "name 字段不正确"
        assert cfg.tools == [], f"tools 默认应为空列表，实际 {cfg.tools}"
        assert cfg.kind == "search", f"kind 默认应为 'search'，实际 {cfg.kind}"
        assert cfg.tool_count() == 0, "tool_count 应为 0"

        # 显式传 tools 和 kind
        cfg2 = m.SubAgentConfig(
            name="数据分析助手",
            description="查库",
            system_prompt="你是数据专家",
            tools=["list_sql_tables", "execute_sql_query"],
            kind="db",
        )
        assert cfg2.tool_count() == 2, "tools 应被正确赋值"
        assert cfg2.kind == "db", "kind 应被正确赋值"

        # 关键坑验证：两个实例的 tools 不能共享同一个 list
        a = m.SubAgentConfig(name="a", description="d", system_prompt="p")
        b = m.SubAgentConfig(name="b", description="d", system_prompt="p")
        a.tools.append("x")
        assert b.tools == [], "默认 list 被实例共享了！必须用 field(default_factory=list)"

        return "默认值、tools、kind、可变默认值隔离全部正确"

    results.append(check("5. dataclass 配置对象", t5))

    # ═══════════════════════════════════════════════════════════════════════
    # 测试 6：整合 —— 并发跑流式输出 + 包内 Agent
    # ═══════════════════════════════════════════════════════════════════════
    def t6():
        async def scenario():
            # 同时跑三条流式输出（模拟前端三个会话并发）
            tasks = [m.collect_stream(t) for t in ["甲", "乙丙", "丁戊己"]]
            streams = await asyncio.gather(*tasks)

            # 同时调用包里的 quick_answer
            answers = await asyncio.gather(
                m_pkg.quick_answer("搜索竞品"),
                m_pkg.quick_answer("查一下库存"),
            )
            return streams, answers

        m_pkg = sys.modules.get("mini_agent")
        assert m_pkg is not None, "mini_agent 未导入，先完成 TODO 4"

        streams, answers = asyncio.run(scenario())
        assert streams == ["甲", "乙丙", "丁戊己"], f"并发流式结果错误：{streams}"
        assert "搜索结果" in answers[0], f"第一条应走 search_tool，实际 {answers[0]}"
        assert "查询结果" in answers[1], f"第二条应走 db_tool，实际 {answers[1]}"

        return f"3 条流式 + 2 个 Agent 调用并发完成"

    results.append(check("6. 并发整合场景", t6))

    # ── 汇总 ────────────────────────────────────────────────────────────────
    passed = sum(results)
    print("-" * 64)
    print(f"结果：{passed}/{len(results)} PASS")
    if passed == len(results):
        print("Day 3 验收通过！现在去读 agent/main_agent.py 的 async for 那段，你会发现全看懂了。")
        return 0
    print("还没通过。按上面的 FAIL 提示逐个补 TODO，再运行本脚本。")
    return 1


if __name__ == "__main__":
    sys.exit(main())
