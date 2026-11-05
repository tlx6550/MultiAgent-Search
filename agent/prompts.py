"""
╔══════════════════════════════════════════════════════════════════════╗
║  文件：agent/prompts.py                                                ║
║  角色：加载 YAML 配置文件，把提示词变成 Python 字典                     ║
║  JS 类比：≈ import yaml from '../config/prompts.yml'                  ║
╚══════════════════════════════════════════════════════════════════════╝

📖 语法速览（前端工程师版）：
  - def 函数名(参数):          ≈ JS 的 function funcName(param) {}
  - 函数体缩进用 4 空格（Python 语法要求！不像 JS 靠大括号）
  - with open(...) as f:       ≈ JS 的 fs.readFileSync('path', 'utf-8')（自动关闭文件）
  - yaml.safe_load(f)          ≈ JS 的 YAML.parse(content)（但安全，不执行嵌入代码）
  - Path(__file__).parents[N]  ≈ JS 的 path.resolve(__dirname, '../' * N)

🎯 读完你应该能说清：
  1. load_yaml 函数干嘛的？返回什么类型？
  2. project_root_path 怎么算出来的？（为什么是 parents[1]）
  3. 为什么要用 safe_load 而不是 load？（安全问题）
"""

# ── 导入依赖 ────────────────────────────────────────────────────────────────
# 💡 JS 类比：import yaml from 'js-yaml'
# Python 里用 pip install pyyaml 装，import 时叫 yaml
import yaml

# 💡 JS 类比：import path from 'path'
# pathlib 是 Python 3.4+ 推荐的路径操作库，比 os.path 更优雅
from pathlib import Path


# ═══════════════════════════════════════════════════════════════════════════
# load_yaml：加载 YAML 配置文件
# ═══════════════════════════════════════════════════════════════════════════
# 💡 JS 类比：
#   function loadYaml(filePath) {
#     const content = fs.readFileSync(filePath, 'utf-8');
#     return yaml.parse(content);
#   }
#
# 语法点：
#   - def 定义函数，参数后面可以加类型注解 file_path: str（告诉 IDE 这是字符串）
#   - 函数体用 4 空格缩进，不需要大括号
#   - with ... as f 是上下文管理器，用完自动关闭文件（不像 JS 要 try/finally）
#   - yaml.safe_load 只解析 YAML 数据，不会执行里面的嵌入代码
#     🔑 为什么不用 yaml.load？因为它可能执行 YAML 里嵌入的 Python 函数，有安全风险！
def load_yaml(file_path):
    """
    加载指定位置的 yaml 配置文件

    Args:
        file_path: 加载的文件的地址（Path 对象或字符串都行）

    Returns:
        dict: 解析后的 Python 字典（和 YAML 的层级一一对应）
    """
    with open(file_path, 'r', encoding='utf-8') as f:
        # safe_load vs load 的区别：
        #   safe_load 只会解析数据（安全！推荐用这个）
        #   load     可能执行 YAML 里嵌入的 Python 对象（危险！有注入攻击风险）
        return yaml.safe_load(f)


# ═══════════════════════════════════════════════════════════════════════════
# 项目根目录计算
# ═══════════════════════════════════════════════════════════════════════════
# 💡 JS 类比：path.resolve(__dirname, '..')  // 向上一层
#
# __file__       = 当前文件路径  .../MultiAgent-Search/agent/prompts.py
# Path(__file__).parents[0] = .../MultiAgent-Search/agent    ← 当前文件所在目录
# Path(__file__).parents[1] = .../MultiAgent-Search          ← 项目根目录（我们要的）
#
# 🔑 为什么不用 parents[2]？因为 prompts.py 在 agent/ 下，向上一层就是根
project_root_path = Path(__file__).parents[1]


# ═══════════════════════════════════════════════════════════════════════════
# 拼出 YAML 文件路径并加载
# ═══════════════════════════════════════════════════════════════════════════
# 💡 JS 类比：path.join(projectRoot, 'prompt', 'prompts.yml')
# Path 对象可以用 / 运算符拼接路径（比 os.path.join 更清爽）
yaml_file_path = project_root_path / "prompt" / "prompts.yml"

# 💡 JS 类比：const promptYamlContent = loadYaml(yamlFilePath)
prompt_yaml_content = load_yaml(yaml_file_path)


# ═══════════════════════════════════════════════════════════════════════════
# 从 YAML 字典里取出我们需要的部分
# ═══════════════════════════════════════════════════════════════════════════
# 💡 JS 类比：
#   const mainAgentContent = promptYamlContent.main_agent;
#   const subAgentsContent = promptYamlContent.sub_agents;
#
# sub_agents_content 里会有：
#   sub_agents_content['tavily']  —— 市场情报助手
#   sub_agents_content['db']      —— 数据分析助手
#   sub_agents_content['ragflow'] —— 内部知识助手
main_agent_content = prompt_yaml_content["main_agent"]
sub_agents_content = prompt_yaml_content["sub_agents"]
