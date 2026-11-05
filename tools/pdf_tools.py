"""
╔══════════════════════════════════════════════════════════════════════╗
║  文件：tools/pdf_tools.py                                              ║
║  角色：Markdown → PDF 转换                                             ║
║  JS 类比：≈ pdfkit.convert(mdPath, pdfPath)                            ║
║  被谁用：agent/main_agent.py 的 tools 列表                              ║
╚══════════════════════════════════════════════════════════════════════╝

📖 语法速览（简单！主要是路径处理）：
  - Path(x).with_suffix('.pdf')    ← 改文件后缀（path/to/test.md → path/to/test.pdf）
  - Path(x).exists()               ← 文件是否存在（≈ fs.existsSync(x)）

🎯 读完你应该能说清：
  1. 为什么要先用 with_suffix 改后缀？（提示：模型可能传 .md 也可能不传）
  2. convert_md_to_pdf_via_word 在哪定义的？（提示：utils/word_converter.py）
"""

import logging
from pathlib import Path

# 💡 JS 类比：import { Annotated, Optional } from 'types'
try:
    from typing import Annotated, Optional
except ImportError:
    from typing_extensions import Annotated, Optional

from langchain_core.tools import tool
from api.monitor import monitor
from api.context import get_session_context
from utils.path_utils import resolve_path
from utils.word_converter import convert_md_to_pdf_via_word


# ═══════════════════════════════════════════════════════════════════════════
# convert_md_to_pdf：把 .md 转成 .pdf
# ═══════════════════════════════════════════════════════════════════════════
# 💡 JS 类比：
#   export const convertMdToPdf = tool({ schema: z.object({...}), execute: async ({ mdFilename, pdfFilename }) => {...} });
@tool
def convert_md_to_pdf(
        md_filename: Annotated[str, "要转换的Markdown文档路径（包含.md后缀）"],
        pdf_filename: Annotated[Optional[str], "输出的PDF文件路径（可选，默认与源文件同名）"] = None
) -> str:
    """
    将Markdown文档转换为PDF（基于Word引擎）
    核心优化：路径与资源管理逻辑分离，只保留Tool层的基础调用
    """
    monitor.report_tool("Markdown转PDF工具")

    try:
        session_dir = get_session_context()

        # 💡 Path.with_suffix('.md') = 强制改成 .md 后缀（不管模型传的啥）
        md_path = Path(md_filename).with_suffix('.md')
        md_abs_path = Path(resolve_path(str(md_path), session_dir))

        # 💡 exists() = fs.existsSync()
        if not md_abs_path.exists():
            return f"错误：文件不存在 {md_abs_path}"

        # 💡 确定输出路径（没传 pdf_filename 就默认同名 .pdf）
        if pdf_filename:
            pdf_path = Path(pdf_filename).with_suffix('.pdf')
            pdf_abs_path = Path(resolve_path(str(pdf_path), session_dir))
        else:
            pdf_abs_path = md_abs_path.with_suffix('.pdf')

        # 💡 真正的转换逻辑在 utils/word_converter.py（本文件只做路径处理 + 调用）
        return convert_md_to_pdf_via_word(md_abs_path, pdf_abs_path)

    except Exception as e:
        logging.error(f"转换失败: {e}", exc_info=True)
        return f"转换失败: {str(e)}"


if __name__ == '__main__':
    # 💡 JS 类比：const getSessionContext = () => './test_session_123'（覆盖原来的）
    get_session_context = lambda: "./test_session_123"

    Path("./test_session_123").mkdir(parents=True, exist_ok=True)
    with open("./test_session_123/测试文件.md", "w", encoding="utf-8") as f:
        f.write("# 标题\n\n测试内容\n")

    print(convert_md_to_pdf.invoke({"md_filename": "测试文件.md"}))
