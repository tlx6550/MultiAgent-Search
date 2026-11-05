"""
╔══════════════════════════════════════════════════════════════════════╗
║  文件：agent/subagents/database_query_agent.py                         ║
║  角色：定义「数据分析子智能体」——主 Agent 让它查数据库                  ║
║  JS 类比：≈ const databaseQueryAgent = { tools: [listSqlTables, ...] }  ║
╚══════════════════════════════════════════════════════════════════════╝

📖 语法速览：
  - list_sql_tables, get_table_data, execute_sql_query 都是 @tool 装饰过的函数
  - tools 字段是一个 list，装多个工具函数
  - 💡 JS 类比：tools: [listSqlTables, getTableData, executeSqlQuery]

🎯 读完你应该能说清：
  1. 这个子智能体有几个工具？分别干嘛？
  2. 为什么工具函数要加 @tool 装饰器？（提示：让模型知道参数 schema）
"""

# 💡 JS 类比：import { sub_agents_content } from '../prompts'
from agent.prompts import sub_agents_content

# 💡 JS 类比：import { listSqlTables, getTableData, executeSqlQuery } from '../../tools/db'
# 三个工具函数：查表名 → 看表结构 → 执行自定义 SQL
from tools.db_tools import list_sql_tables, get_table_data, execute_sql_query


# ═══════════════════════════════════════════════════════════════════════════
# 数据库查询子智能体定义
# ═══════════════════════════════════════════════════════════════════════════
# 💡 JS 类比：const database_query_agent = { name, description, prompt, tools }
#
# 三个工具的调用顺序（模型会自己决定）：
#   1. list_sql_tables   —— 先查有哪些表（否则不知道表名怎么写 SQL）
#   2. get_table_data    —— 看某张表的数据长什么样（写 SQL 前先摸清 schema）
#   3. execute_sql_query —— 写自定义 SQL 执行查询
database_query_agent = {
    "name":          sub_agents_content['db']['name'],
    "description":   sub_agents_content['db']['description'],
    "system_prompt": sub_agents_content['db']['system_prompt'],
    "tools":         [list_sql_tables, get_table_data, execute_sql_query]  # 三个工具，顺序有讲究
}
