"""
╔══════════════════════════════════════════════════════════════════════╗
║  文件：tools/upload_file_read_tool.py                                   ║
║  角色：读取用户上传的文件——让 Agent 能看 .md / .docx / .pdf / .xlsx     ║
║  JS 类比：≈ fs.readFileSync + xlsx.parse + pdf-parse                   ║
║  被谁用：agent/main_agent.py 的 tools 列表                              ║
╚══════════════════════════════════════════════════════════════════════╝

📖 语法速览（重点：可选依赖的 try/except 导入）：
  - try: import docx; except ImportError: docx = None   ← 可选依赖，没装也能跑
  - file_path.suffix.lower()                           ← 取文件后缀（统一小写）
  - [para.text for para in doc.paragraphs]             ← 列表推导式（≈ JS 的 .map）

🎯 读完你应该能说清：
  1. 为什么 docx / pypdf / pandas 要用 try/except 导入？（提示：这些是可选的重型依赖）
  2. 怎么判断文件类型？（提示：看 file_path.suffix）
  3. Excel 返回什么格式？为什么？（提示：CSV + 统计描述，模型读着方便）
"""

import logging
from pathlib import Path
from typing import Annotated, Optional

from langchain_core.tools import tool
from api.monitor import monitor
from api.context import get_session_context
from utils.path_utils import resolve_path


# ── 可选依赖（try/except 导入，没装也能跑，只是对应格式读不了）──
# 💡 JS 类比：
#   let docx = null;
#   try { docx = require('docx'); } catch { /* 没装，docx 读取会报错 */ }
try:
    import docx
except ImportError:
    docx = None

try:
    import pypdf
except ImportError:
    pypdf = None

try:
    import pandas as pd
except ImportError:
    pd = None


# ═══════════════════════════════════════════════════════════════════════════
# read_file_content：万能文件读取
# ═══════════════════════════════════════════════════════════════════════════
@tool
def read_file_content(
        filename: Annotated[str, "要读取的文件名或路径（支持 .md, .docx, .pdf, .xlsx, .xls）"],
        instruction: Annotated[str, "对提取内容的具体指令（例如：'提取摘要', '统计数据'）"] = "提取全部内容"
) -> str:
    """
    读取指定文件的内容。支持 Markdown、Word、PDF 和 Excel。
    Excel 会自动提供数据统计信息（head 和 describe）。
    """
    monitor.report_tool("文件内容读取工具", {"filename": filename, "instruction": instruction})

    # 💡 从 ContextVar 拿当前会话目录
    session_dir = get_session_context()
    file_path = Path(resolve_path(filename, session_dir))

    # 💡 exists() 判断文件是否存在
    if not file_path.exists():
        return f"错误：文件 '{filename}' 不存在 (解析路径: {file_path})。"

    # 💡 suffix 取文件后缀（.md / .pdf / .docx），lower() 统一小写防止大小写问题
    ext = file_path.suffix.lower()

    try:
        # ── .md / .txt：纯文本，直接读 ──────────────────────────────────────
        if ext in ['.md', '.txt']:
            return file_path.read_text(encoding='utf-8')

        # ── .docx：Word 文档 ────────────────────────────────────────────────
        elif ext == '.docx':
            if docx is None:
                return "错误：未安装 'python-docx' 库，无法读取 Word 文件。"
            # 💡 JS 类比：docx.Document(file).paragraphs.map(p => p.text).join('\n')
            doc = docx.Document(str(file_path))
            full_text = [para.text for para in doc.paragraphs]  # 列表推导式
            return '\n'.join(full_text)

        # ── .pdf：PDF ───────────────────────────────────────────────────────
        elif ext == '.pdf':
            if pypdf is None:
                return "错误：未安装 'pypdf' 库，无法读取 PDF 文件。"
            reader = pypdf.PdfReader(str(file_path))
            # 💡 JS 类比：reader.pages.map(p => p.extractText()).join('\n')
            text = "\n".join([page.extract_text() or "" for page in reader.pages])
            return text

        # ── .xlsx / .xls：Excel ─────────────────────────────────────────────
        elif ext in ['.xlsx', '.xls']:
            if pd is None:
                return "错误：未安装 'pandas' 库，无法读取 Excel 文件。"

            df = pd.read_excel(str(file_path))

            # 💡 给模型返回：行数/列数/列名 + 前 5 行预览 + 统计描述
            # 模型读这些就能知道 Excel 里装的是什么数据
            result = [
                f"文件: {filename}",
                f"行数: {len(df)}, 列数: {len(df.columns)}",
                f"列名: {', '.join(df.columns.astype(str))}",
                "\n[前5行数据预览]:",
                df.head().to_string(index=False),
                "\n[统计描述]:",
                df.describe().to_string()
            ]
            return "\n".join(result)

        # ── 兜底：尝试当纯文本读 ─────────────────────────────────────────────
        else:
            try:
                return file_path.read_text(encoding='utf-8')
            except UnicodeDecodeError:
                return f"错误：不支持的文件格式 '{ext}'，且无法作为文本读取。"

    except Exception as e:
        return f"读取文件出错: {str(e)}"


if __name__ == '__main__':
    def get_session_context():
        return "./test_session_123"

    result = read_file_content.invoke({"filename": "测试文件.md"})
    print("===== 读取 MD 文件结果 =====")
    print(result)
