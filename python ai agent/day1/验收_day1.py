"""
╔══════════════════════════════════════════════════════════════════════╗
║  Day 1 自动验收脚本                                                    ║
╠══════════════════════════════════════════════════════════════════════╣
║  用法：                                                                 ║
║    python 验收_day1.py                          # 验收你的练习文件      ║
║    python 验收_day1.py --file 参考实现_day1.py   # 验收参考实现          ║
║                                                                         ║
║  通过标准：6/6 PASS                                                     ║
╚══════════════════════════════════════════════════════════════════════╝

📖 Python ↔ JS 对照速查（验收脚本用到的语法）：
┌───────────────────────────┬──────────────────────────────────────────┐
│ Python                    │ JavaScript                               │
├───────────────────────────┼──────────────────────────────────────────┤
│ import argparse           │ import yargs from 'yargs'                │
│ import importlib.util     │ dynamic import() 或 require              │
│ sys.exit(1)               │ process.exit(1)                          │
│ isinstance(x, dict)       │ typeof x === 'object' && x !== null      │
│ assert cond, msg          │ if (!cond) throw new Error(msg)          │
│ set(x.keys())             │ new Set(Object.keys(x))                  │
│ traceback.print_exc()     │ console.error(err.stack)                │
│ Path(x).parent            │ path.dirname(x)                          │
│ .is_absolute()            │ path.isAbsolute(x)                       │
│ .exists()                 │ fs.existsSync(x)                         │
│ asyncio.run(fn)           │ (async () => { await fn() })()           │
└───────────────────────────┴──────────────────────────────────────────┘
"""

# 允许在类型注解里直接用字符串（如 -> dict），不需要 from __future__ import annotations 也能跑
# 但保留它可以让注解在模块加载时就被解析，某些 linter 会更友好
from __future__ import annotations

import argparse          # 💡 JS 类比：import yargs from 'yargs'（命令行参数解析）
import asyncio           # 💡 JS 类比：原生 async/await 支持
import importlib.util    # 💡 JS 类比：动态 import() 或 require（运行时加载任意文件）
import sys               # 💡 JS 类比：process（系统相关）
import traceback         # 💡 JS 类比：console.error(err.stack)（打印完整堆栈）
from pathlib import Path  # 💡 JS 类比：import path from 'path'（路径操作）

# ── 模块级常量 ──────────────────────────────────────────────────────────────
HERE = Path(__file__).resolve().parent  # 💡 JS 类比：__dirname（当前脚本所在目录，即 day1/）
DEFAULT_FILE = HERE / "今日练习_python基础与Agent入门.py"  # 💡 JS 类比：path.join(__dirname, '今日练习.py')
EXPECTED_NAMES = ["市场情报助手", "数据分析助手", "内部知识助手"]  # 验收用的预期子智能体名称


# ═══════════════════════════════════════════════════════════════════════════
# load_module：动态导入任意 .py 文件
# ═══════════════════════════════════════════════════════════════════════════
# 💡 JS 类比：
#   async function loadModule(filePath) {
#     return await import(filePath);  // JS 动态 import
#   }
def load_module(file_path: Path):
    """动态导入任意 .py 文件，返回它的 module 对象。

    因为练习文件的文件名不是固定的（可以用 --file 指定），所以不能用普通 import。
    这里用 importlib 三步法：
      1. spec_from_file_location — 构造一个描述文件位置的 spec
      2. module_from_spec         — 根据 spec 创建空 module
      3. exec_module              — 真正执行文件内容，把函数/变量装进 module
    """

    #     # 假设目标文件里有这些顶层代码：
    # ROUTE_RULES = {...}       # 执行后 → module.ROUTE_RULES = {...}

    # def route_query(query):   # 执行后 → module.route_query = <那个函数对象>
    #     ...

    # class ToolRegistry:       # 执行后 → module.ToolRegistry = <那个类>
    #     ...
    # 💡 JS 类比：给动态模块起内部名字（不是文件名）
    spec = importlib.util.spec_from_file_location("day1_exercise", file_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"无法加载文件：{file_path}")
    module = importlib.util.module_from_spec(spec)
    # 💡 JS 类比：执行文件内容，把导出的函数/变量装进 module
    spec.loader.exec_module(module)
    return module


# ═══════════════════════════════════════════════════════════════════════════
# check：统一测试入口
# ═══════════════════════════════════════════════════════════════════════════
# 💡 JS 类比：
#   function check(name: string, fn: () => any): boolean {
#     try {
#       const detail = fn();
#       console.log(`[PASS] ${name}${detail ? ' -> ' + detail : ''}`);
#       return true;
#     } catch (e) {
#       if (e instanceof NotImplementedError) {
#         console.log(`[FAIL] ${name} -> 还没实现，去补 TODO`);
#       } else {
#         console.log(`[FAIL] ${name} -> ${e.name}: ${e.message}`);
#       }
#       return false;
#     }
#   }
def check(name: str, fn):
    """运行一条测试用例 fn，统一输出 PASS/FAIL 并返回布尔值。

    设计成统一入口的好处：
      - 每条用例只写 assert 就行，不用自己 try/except
      - 输出格式一致，肉眼一眼能扫过
    """
    try:
        detail = fn()  # fn 内部跑完所有 assert 后可以返回一段描述，附在 PASS 后面
        print(f"[PASS] {name}" + (f" -> {detail}" if detail else ""))
        return True
    except NotImplementedError:
        # 专门识别 "还没写" 这种情况，提示用户去补 TODO
        print(f"[FAIL] {name} -> 还没实现，去补 TODO")
        return False
    except Exception as e:
        # 其他所有异常（AssertionError / KeyError / TypeError 等）统一捕获
        print(f"[FAIL] {name} -> {type(e).__name__}: {e}")
        return False


# ═══════════════════════════════════════════════════════════════════════════
# main：验收主流程
# ═══════════════════════════════════════════════════════════════════════════
def main() -> int:
    # 💡 JS 类比：const args = yargs.option('file', {default: DEFAULT_FILE}).parseSync()
    parser = argparse.ArgumentParser()
    parser.add_argument("--file", default=str(DEFAULT_FILE), help="要验收的 Python 文件")
    args = parser.parse_args()

    # ── 路径处理 ────────────────────────────────────────────────────────────
    target = Path(args.file)
    if not target.is_absolute():
        target = HERE / target  # 💡 JS 类比：如果不是绝对路径，拼到当前脚本目录
    if not target.exists():     # 💡 JS 类比：if (!fs.existsSync(target))
        print(f"找不到文件：{target}")
        return 1

    print("=" * 64)
    print(f"验收目标：{target.name}")
    print("=" * 64)

    # HERE = "d:\Ai学习\MultiAgent-Search\python ai agent\day1"
    #          │
    #          ├── 场景1: 默认路径（本身就是绝对的）
    #          │    target = HERE / "今日练习_python基础与Agent入门.py"
    #          │          = "d:\...\day1\今日练习_python基础与Agent入门.py" ✅
    #          │
    #          ├── 场景2: 相对路径（用户传 "参考实现_day1.py"）
    #          │    target = HERE / "参考实现_day1.py"
    #          │          = "d:\...\day1\参考实现_day1.py" ✅
    #          │
    #          └── 场景3: 绝对路径（用户传 "d:\...\day2\xxx.py"）
    #               target 直接就是 "d:\...\day2\xxx.py" ✅
    #               HERE 完全不参与拼接

    # ── 动态导入 ────────────────────────────────────────────────────────────
    try:
        m = load_module(target)  # m 就是导入后的 module 对象，m.load_config() 这样调用
    except Exception:
        print("[FAIL] 导入失败，先修复语法错误：")
        traceback.print_exc()  # 💡 JS 类比：console.error(err.stack)
        return 1

    results = []

    # ── 测试 1：load_config ────────────────────────────────────────────────
    # 💡 JS 类比：
    #   function t1() {
    #     const config = m.load_config();
    #     assert(typeof config === 'object');
    #     assert('main_agent' in config);
    #     assert('sub_agents' in config);
    #     assert(config.main_agent.system_prompt.trim() !== '');
    #     return `顶层键 ${Object.keys(config)}`;
    #   }
    def t1():
        config = m.load_config()
        # 💡 JS 类比：typeof config === 'object'
        assert isinstance(config, dict), "load_config 必须返回 dict"
        # 💡 JS 类比：'main_agent' in config
        assert "main_agent" in config, "缺少 main_agent"
        assert "sub_agents" in config, "缺少 sub_agents"
        # 💡 JS 类比：config.main_agent.system_prompt.trim() !== ''
        assert config["main_agent"]["system_prompt"].strip(), "main_agent.system_prompt 为空"
        return f"顶层键 {list(config.keys())}"

    results.append(check("1. 读取 YAML 配置", t1))

    # 提前 load_config 一次，供后面 t2/t3 复用
    config = None
    try:
        config = m.load_config()
    except Exception:
        pass

    # ── 测试 2：list_subagents — 名称校验 ────────────────────────────────────
    def t2():
        subs = m.list_subagents(config)
        # 💡 JS 类比：Array.isArray(subs) && subs.length === 3
        assert isinstance(subs, list) and len(subs) == 3, "应返回 3 个子智能体"
        # 💡 JS 类比：subs.map(s => s.name)
        names = [s["name"] for s in subs]
        # 💡 JS 类比：JSON.stringify(names) === JSON.stringify(EXPECTED_NAMES)
        # Python 的 == 对 list 做逐项比较，顺序必须一致
        assert names == EXPECTED_NAMES, f"名称应为 {EXPECTED_NAMES}，实际 {names}"
        return "、".join(names)

    results.append(check("2. 子智能体名称", t2))

    # ── 测试 3：list_subagents — 内容校验 ────────────────────────────────────
    def t3():
        subs = m.list_subagents(config)
        # 💡 JS 类比：for (const s of subs) { ... }
        for s in subs:
            assert isinstance(s["description"], str) and s["description"], "description 不能为空"
            assert isinstance(s["prompt_chars"], int) and s["prompt_chars"] > 0, "prompt_chars 必须为正整数"
        return f"{len(subs)} 条描述与提示词长度均有效"

    results.append(check("3. 子智能体描述与提示词长度", t3))

    # ── 测试 4：route_query ───────────────────────────────────────────────────
    def t4():
        cases = [
            ("最近竞品有什么动作", ["市场情报助手"]),                  # 单路由
            ("查一下上月销量和库存", ["数据分析助手"]),                # 单路由
            ("找一下运营SOP文档", ["内部知识助手"]),                   # 单路由
            ("结合竞品动态和我们的库存数据", ["市场情报助手", "数据分析助手"]),  # 多路由
            ("帮我分析一下", ["市场情报助手"]),                        # 兜底
        ]
        for query, expected in cases:
            actual = m.route_query(query)
            assert actual == expected, f"「{query}」应为 {expected}，实际 {actual}"
        return f"{len(cases)} 个路由用例全部正确"

    results.append(check("4. 关键词路由", t4))

    # ── 测试 5：build_tool_call ──────────────────────────────────────────────
    def t5():
        call = m.build_tool_call("市场情报助手", "搜索竞品动态")
        assert call["name"] == "task", "tool_call.name 必须是 task"
        assert call["args"]["subagent_type"] == "市场情报助手", "subagent_type 不正确"
        assert call["args"]["description"] == "搜索竞品动态", "description 不正确"
        return str(call)

    results.append(check("5. 构造 tool_call", t5))

    # ── 测试 6：run_mock_agent ────────────────────────────────────────────────
    def t6():
        # 💡 JS 类比：要在同步代码里跑 async 函数，用 IIFE 立即执行
        #   const result = await (async () => m.run_mock_agent(...))();
        # Python 用 asyncio.run() 来启动事件循环
        result = asyncio.run(m.run_mock_agent("查一下上月销量"))

        assert isinstance(result, dict), "run_mock_agent 必须返回 dict"
        # 💡 JS 类比：new Set(Object.keys(result))
        # set() 创建集合，集合间用 == 比较元素是否相同（忽略顺序）
        assert set(result.keys()) == {"query", "routes", "steps", "answer"}, "返回字段不完整"
        assert result["routes"] == ["数据分析助手"], "routes 应复用 route_query"
        assert len(result["steps"]) == len(result["routes"]), "每个子智能体应有一条执行步骤"
        assert "数据分析助手" in result["answer"], "answer 应包含调用的助手名称"
        return "异步执行结果结构正确"

    results.append(check("6. 异步 mock 执行", t6))

    # ── 汇总结果 ────────────────────────────────────────────────────────────
    passed = sum(results)  # True + True + True = 3（Python 里 True=1, False=0）
    print("-" * 64)
    print(f"结果：{passed}/{len(results)} PASS")
    if passed == len(results):
        print("Day 1 验收通过。现在去做费曼笔记：用 3 句话讲清 Agent / Tool / 多 Agent。")
        return 0
    print("还没通过。按上面的 FAIL 提示逐个补 TODO，再运行本脚本。")
    return 1


# 💡 JS 类比：if (import.meta.url === `file://${process.argv[1]}`) { process.exit(main()); }
if __name__ == "__main__":
    sys.exit(main())  # 💡 JS 类比：process.exit(main())
