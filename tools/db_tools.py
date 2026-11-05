"""
╔══════════════════════════════════════════════════════════════════════╗
║  文件：tools/db_tools.py                                               ║
║  角色：数据库查询工具——让 Agent 能查 MySQL                              ║
║  JS 类比：≈ src/tools/mysqlQuery.ts                                    ║
║  被谁用：agent/subagents/database_query_agent.py 的 tools 列表          ║
╚══════════════════════════════════════════════════════════════════════╝

📖 语法速览（重点：with 上下文管理器 + Python 里的数据库操作模式）：
  - with connect(**config) as conn:     ← 自动关闭连接（JS 没有这个，要 try/finally）
  - with conn.cursor() as cursor:        ← 自动关闭 cursor
  - cursor.execute(sql)                 ← 执行 SQL
  - cursor.fetchall()                   ← 获取所有行（返回 list of tuple）
  - @tool                               ← 装饰器，把函数变成 Agent 工具

🎯 读完你应该能说清：
  1. 为什么数据库操作都要用 with？（提示：自动清理资源）
  2. 三个工具的调用顺序？（提示：list → get_table → execute）
  3. 为什么返回 CSV 格式的字符串？（提示：模型读自然语言比读 JSON 更可靠）

💡 Python 数据库操作的标准模式（和 JS 对比）：
  JS:  try { const conn = await mysql.connect(...); const cursor = conn.cursor(); cursor.execute(sql); ... } finally { conn.end(); }
  Py:  with connect(...) as conn: with conn.cursor() as cursor: cursor.execute(sql)
  ↑ Python 的 with 会自动调用 close()，不会忘记释放连接！
"""

import os
from dotenv import load_dotenv
from api.monitor import monitor
from mysql.connector import connect, Error
from langchain_core.tools import tool

load_dotenv()


# ═══════════════════════════════════════════════════════════════════════════
# get_db_config：从 .env 读数据库配置
# ═══════════════════════════════════════════════════════════════════════════
# 💡 JS 类比：
#   function getDbConfig() {
#     const config = {
#       host: process.env.MYSQL_HOST || 'localhost',
#       port: parseInt(process.env.MYSQL_PORT || '3306'),
#       ...
#     };
#     return Object.fromEntries(Object.entries(config).filter(([k,v]) => v !== undefined));
#   }
def get_db_config():
    """从环境变量构建 MySQL 连接配置字典（去掉 None 值，校验必需项）"""
    config = {
        "host": os.getenv("MYSQL_HOST", "localhost"),
        "port": int(os.getenv("MYSQL_PORT", "3306")),
        "user": os.getenv("MYSQL_USER"),
        "password": os.getenv("MYSQL_PASSWORD"),
        "database": os.getenv("MYSQL_DATABASE"),
        "charset": os.getenv("MYSQL_CHARSET", "utf8mb4"),
        "collation": os.getenv("MYSQL_COLLATION", "utf8mb4_unicode_ci"),
        "autocommit": True,
        "connection_timeout": int(os.getenv("MYSQL_TIMEOUT", "10")),
        "sql_mode": os.getenv("MYSQL_SQL_MODE", "TRADITIONAL"),
    }
    # 移除 None 值（os.getenv 没配的项）
    config = {k: v for k, v in config.items() if v is not None}

    # 校验必需项
    required_keys = ["user", "password", "database"]
    missing_keys = [k for k in required_keys if k not in config]
    if missing_keys:
        raise ValueError(f"缺失数据库核心配置：{', '.join(missing_keys)}")

    return config


# ═══════════════════════════════════════════════════════════════════════════
# list_sql_tables：查询当前库有哪些表
# ═══════════════════════════════════════════════════════════════════════════
# 💡 JS 类比：
#   export const listSqlTables = tool({
#     description: '查询当前库中所有可用的表',
#     execute: async () => { ... }
#   });
@tool
def list_sql_tables()->str:
    """
    查询当前库中所有可用的表！
    作用：为了模型识别有哪些可用的表，方便后续写自定义 SQL
    :return: 有表返回表名列表，无表返回"没有可用的表"，异常返回错误信息
    """
    monitor.report_tool(tool_name="数据库表名查询工具：list_sql_tables", args={})
    config = get_db_config()

    # 💡 with 上下文管理器 = JS 的 try/finally（自动关闭资源）
    #   connect() 返回的对象会在 with 块结束时自动关闭
    #   cursor 也一样，嵌套 with 自动清理
    try:
        with connect(**config) as conn:          # **config 把字典展开成关键字参数
            with conn.cursor() as cursor:
                sql = "show tables"
                cursor.execute(sql)
                # 💡 fetchall() 返回 list of tuple：[('orders',), ('products',)]
                tables = cursor.fetchall()
                if not tables:
                    return "没有可用的表"
                # 💡 [table[0] for table in tables] 列表推导式（≈ JS 的 tables.map(t => t[0])）
                table_names = [table[0] for table in tables]
                return f"可用的表有：{', '.join(table_names)}"
    except Error as e:
        # 💡 不 raise，而是返回错误字符串让模型知道发生了什么
        return f"查询出现异常：{str(e)}"


# ═══════════════════════════════════════════════════════════════════════════
# get_table_data：看某张表的数据长什么样
# ═══════════════════════════════════════════════════════════════════════════
# 💡 为什么限制 100 条？防止大表把 token 撑爆
@tool
def get_table_data(table_name)->str:
    """
    查询指定表名的数据！
    作用：1. 完成单表数据查询 2. 为多表查询提供表结构参考
    :param table_name: 表名
    :return: CSV 格式字符串（最多 100 条）
    """
    monitor.report_tool(tool_name="数据库表数据查询工具：get_table_data", args={"table_name": table_name})
    config = get_db_config()

    try:
        with connect(**config) as conn:
            with conn.cursor() as cursor:
                # 💡 f"select * from {table_name} limit 100"  ≈ JS 的 `select * from ${tableName} limit 100`
                # 🔑 安全提醒：table_name 没有参数化（MySQL 不支持表名参数化）
                #    所以这个参数不能让用户直接输入，必须让模型先查 list_sql_tables
                sql = f"select * from {table_name} limit 100"
                cursor.execute(sql)

                # 💡 cursor.description 返回列元信息：[(col1_name, ...), (col2_name, ...)]
                description = cursor.description
                if not description:
                    return f"数据表：{table_name}为空没有数据！"
                columns = [desc[0] for desc in description]  # 提取列名
                rows = cursor.fetchall()                       # 取所有行

                # 💡 ",".join(map(str, row)) 把 tuple 转成 CSV 行
                results = [",".join(map(str, row)) for row in rows]
                header_str = ",".join(columns)
                data_str = "\n".join(results)
                return f"{header_str}\n{data_str}"
    except Error as e:
        return f"查询出现异常：{str(e)}"


# ═══════════════════════════════════════════════════════════════════════════
# execute_sql_query：执行自定义 SQL
# ═══════════════════════════════════════════════════════════════════════════
# 💡 这是最强大也最危险的工具——模型写的 SQL 直接执行
#    所以前两个工具是必须的：先查有哪些表、表结构是什么，再写 SQL
@tool
def execute_sql_query(query)->str:
    """
    执行自定义查询SQL语句！
    切记：执行之前，需要先 list_sql_tables 明确表名！再 get_table_data 明确表结构！
    :param query: 要执行的自定义sql语句
    :return: CSV 格式数据
    """
    monitor.report_tool(tool_name="数据库表数据查询工具：execute_sql_query", args={"query": query})
    config = get_db_config()

    try:
        with connect(**config) as conn:
            with conn.cursor() as cursor:
                cursor.execute(query)
                description = cursor.description
                if not description:
                    return f"执行自定义SQL语句查询没有结果，sql为：{query}！"
                columns = [desc[0] for desc in description]
                rows = cursor.fetchall()
                results = [",".join(map(str, row)) for row in rows]
                header_str = ",".join(columns)
                data_str = "\n".join(results)
                return f"{header_str}\n{data_str}"
    except Error as e:
        return f"查询出现异常：{str(e)}"


if __name__ == "__main__":
    print(execute_sql_query("SELECT * FROM orders WHERE category = '数码电子'"))
