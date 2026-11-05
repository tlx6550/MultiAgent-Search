"""
╔══════════════════════════════════════════════════════════════════════╗
║  文件：tools/markdown_tools.py                                         ║
║  角色：生成 Markdown 文件——让 Agent 能把结果写成 .md 存下来              ║
║  JS 类比：≈ fs.writeFileSync(`${sessionDir}/${filename}.md`, content)  ║
║  被谁用：agent/main_agent.py 的 tools 列表（主 Agent 自己的工具）       ║
╚══════════════════════════════════════════════════════════════════════╝

📖 语法速览（重点：Annotated 类型注解 + Path 文件操作）：
  - from typing import Annotated       ← Python 3.9+ 的类型注解（≈ TS 的 type annotations）
  - Annotated[str, "说明文字"]        ← 类型 + 描述，@tool 会把描述传给模型
  - Path(x).write_text(content)       ← 写文件（比 open + write 更清爽）
  - Path(x).parent                    ← 取父目录（≈ path.dirname(x)）

🎯 读完你应该能说清：
  1. Annotated 为什么比 docstring 更有用？（提示：它把每个参数的说明传给模型）
  2. 为什么要先 resolve_path？（提示：安全！防止路径穿越攻击）
  3. get_session_context 从哪来的？（提示：ContextVar，存当前会话的目录）
"""

import logging
from pathlib import Path

# 💡 JS 类比：import { Annotated } from 'types'（但 Python 3.9+ 内置，老版本从 typing_extensions 来）
try:
    from typing import Annotated
except ImportError:
    from typing_extensions import Annotated

# 💡 JS 类比：import { tool } from '@langchain/langchain'
from langchain_core.tools import tool
from api.monitor import monitor
from api.context import get_session_context
from utils.path_utils import resolve_path


# ═══════════════════════════════════════════════════════════════════════════
# generate_markdown：写一个 .md 文件
# ═══════════════════════════════════════════════════════════════════════════
# 💡 JS 类比：
#   export const generateMarkdown = tool({
#     description: '根据提供的文本内容生成 Markdown 文件',
#     schema: z.object({
#       content: z.string().describe('要写入的文本内容'),
#       filename: z.string().describe('Markdown文件名'),
#       path: z.string().optional().default('').describe('保存路径')
#     }),
#     execute: async ({ content, filename, path }) => { ... }
#   });
#
# 💡 Annotated[str, "说明"] = 把参数类型 + 描述一起写
#    @tool 会自动把第二个参数变成模型能读的参数说明
#    所以模型知道：content 是要写的文本，filename 是文件名
@tool
def generate_markdown(
        content: Annotated[str, "要写入Markdown文档的文本内容"],
        filename: Annotated[str, "Markdown文档的文件名（不包含扩展名或包含.md）"],
        path: Annotated[str, "文件保存的绝对路径"] = ""
):
    """根据提供的文本内容，生成对应的Markdown(.md)文件"""
    monitor.report_tool("Markdown文档生成工具", {"写入的文本内容": content})

    # 💡 自动补 .md 后缀（模型可能会忘写）
    if not filename.endswith('.md'):
        filename += '.md'

    # 💡 从 ContextVar 拿当前会话的目录（每个用户独立，不会串台）
    session_dir = get_session_context()

    # ── 路径清洗与重定向 ─────────────────────────────────────────────────────
    # 💡 JS 类比：const fullPath = path.resolve(path.join(path, filename), sessionDir)
    # resolve_path 做了两件事：
    #   1. 防止路径穿越攻击（比如 filename = '../../etc/passwd' 这种危险路径）
    #   2. 如果传的是相对路径，自动拼到 session_dir 下
    if path and path != ".":
        full_input_path = str(Path(path) / filename)
    else:
        full_input_path = filename
    full_path_str = resolve_path(full_input_path, session_dir)
    file_path = Path(full_path_str)

    # 💡 确保父目录存在（mkdir 不存在就创建，存在就跳过）
    parent_dir = file_path.parent
    try:
        if not parent_dir.exists():
            parent_dir.mkdir(parents=True, exist_ok=True)

        # 💡 Path.write_text = open().write() 的简写
        file_path.write_text(content, encoding='utf-8')

        return f"Markdown文件 '{file_path}' 已成功生成并保存。"
    except Exception as e:
        logging.error(f"写入Markdown文件失败: {e}", exc_info=True)
        return f"生成Markdown文件失败: {str(e)}"


# ── 测试代码（Python 脚本调试神器：if __name__ == "__main__":）──
# 💡 JS 类比：if (import.meta.url === `file://${process.argv[1]}`) { ... }
# 这段只在你直接 python markdown_tools.py 时执行，被 import 时不执行
if __name__ == "__main__":
    def get_session_context():
        return "./test_session_123"  # 测试时给个固定值

    test_content = "# 测试文档\n这是测试内容"
    test_filename = "测试文件"

    print("===== 开始测试 =====")
    result = generate_markdown.invoke({"content": test_content, "filename": test_filename})
    print(f"\n调用结果：{result}")
