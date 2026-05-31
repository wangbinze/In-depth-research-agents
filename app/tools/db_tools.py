"""
MySQL 数据库查询工具模块

封装数据库查询助手使用的三个 LangChain 工具：
list_sql_tables 用于发现真实表名，get_table_data 用于预览字段 and 样例数据，
execute_sql_query 用于在确认结构后执行自定义查询。
"""

import os
import sys
import re
from pathlib import Path
from dotenv import find_dotenv, load_dotenv
from langchain_core.tools import tool
from mysql.connector import Error
from mysql.connector.pooling import MySQLConnectionPool

# 允许直接运行本文件进行调试：python app/tools/db_tools.py
# 正常从项目根目录以模块方式导入时，app 已经在 Python 搜索路径中。
if __package__ in {None, ""}:
    project_root = Path(__file__).resolve().parents[2]
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))
from app.api.monitor import monitor

# find_dotenv 会从当前目录向上查找 .env，适合脚本和 Web 服务从不同入口启动的场景
load_dotenv(find_dotenv())

# 全局数据库连接池和配置
_db_pool = None


def get_db_config() -> dict:
    """
    从环境变量读取数据库配置
    """
    return {
        "host": os.getenv("MYSQL_HOST", "localhost"),
        "port": int(os.getenv("MYSQL_PORT", 3307)),
        "user": os.getenv("MYSQL_USER", "root"),
        "password": os.getenv("MYSQL_PASSWORD", "123456"),
        "database": os.getenv("MYSQL_DATABASE", "deepsearch_db"),
        "charset": os.getenv("MYSQL_CHARSET", "utf8mb4"),
        "collation": os.getenv("MYSQL_COLLATION", "utf8mb4_unicode_ci"),
        "sql_mode": os.getenv("MYSQL_SQL_MODE", "TRADITIONAL"),
    }


def get_db_connection():
    """
    安全获取或初始化数据库连接池中的连接
    """
    global _db_pool
    if _db_pool is None:
        config = get_db_config()
        pool_size = int(os.getenv("MYSQL_POOL_SIZE", "5"))
        # 初始化连接池
        _db_pool = MySQLConnectionPool(
            pool_name="db_pool", pool_size=pool_size, **config
        )
    return _db_pool.get_connection()


def is_safe_sql(query: str) -> tuple[bool, str]:
    """
    检查 SQL 语句是否安全且仅执行只读操作。
    """
    # 1. 过滤 SQL 注释，防止注释混淆/绕过
    # 过滤单行注释: -- comment 或 # comment
    cleaned = re.sub(r"(--.*|#.*)", "", query)
    # 过滤多行注释: /* comment */
    cleaned = re.sub(r"/\*.*?\*/", "", cleaned, flags=re.DOTALL)

    cleaned = cleaned.strip()
    if not cleaned:
        return False, "SQL 语句不能为空"

    # 2. 检查多语句（防止堆叠注入）
    # 允许最后一个字符是分号，但如果分号后面还有其他非空字符/语句则拒绝
    statements = [s.strip() for s in cleaned.split(";") if s.strip()]
    if len(statements) > 1:
        return False, "安全违规：禁止执行多条 SQL 语句 (堆叠查询)"
    elif not statements:
        return False, "SQL 语句无有效内容"

    single_stmt = statements[0]

    # 3. 校验首个单词（必须是 SELECT, SHOW, DESCRIBE, EXPLAIN）
    # 忽略大小写
    match = re.match(r"^([a-zA-Z]+)", single_stmt)
    if not match:
        return False, "安全违规：无法识别 SQL 语句的起始命令"

    first_word = match.group(1).upper()
    allowed_verbs = {"SELECT", "SHOW", "DESCRIBE", "EXPLAIN"}
    if first_word not in allowed_verbs:
        return (
            False,
            f"安全违规：禁止执行非查询/只读操作。命令 '{first_word}' 不被允许。",
        )

    # 4. 严格匹配禁止的写入/敏感操作关键字（使用 \b 单词边界）
    forbidden_keywords = {
        "INSERT",
        "UPDATE",
        "DELETE",
        "DROP",
        "ALTER",
        "CREATE",
        "REPLACE",
        "TRUNCATE",
        "RENAME",
        "GRANT",
        "REVOKE",
        "INTO",
        "LOAD_FILE",
    }
    # 在整条语句中查找任何可能导致写操作的关键字
    pattern = r"\b(" + "|".join(forbidden_keywords) + r")\b"
    found = re.findall(pattern, single_stmt, flags=re.IGNORECASE)
    if found:
        return (
            False,
            f"安全违规：检测到禁止的写操作/定义关键字: {', '.join(set(found))}",
        )

    return True, ""


@tool
def list_sql_tables() -> str:
    """
    列出数据库中所有可用的表。

    作用：让模型先识别真实可用的表名，方便后续预览表结构和编写自定义 SQL。
    :return: 有表：可用的表有：表1,表2,表3...
             没有表：没有可用的表
             出现异常：查询出现异常：异常信息
    """
    # 埋点：工具一被调用，前端可以展示当前正在查询数据库表名
    monitor.report_tool(tool_name="数据库表名查询工具：list_sql_tables", args={})

    try:
        # 使用连接池获取连接，with 结束自动 close 返回连接池
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                sql = "SHOW TABLES"
                cursor.execute(sql)
                tables = cursor.fetchall()

                if not tables:
                    return "没有可用的表"

                # 取每个元组的第一个元素，拼成模型容易阅读的表名列表
                table_names = [table[0] for table in tables]
                return f"可用的表有：{', '.join(table_names)}"
    except Error as e:
        return f"查询出现异常：{str(e)}"


@tool
def get_table_data(table_name) -> str:
    """
    查询指定表的前 100 行数据

    当前工具调用之前，应先调用 list_sql_tables 完成表名校验。
    此工具的作用：
    1. 完成单表样例数据查询
    2. 为多表查询提供表结构信息和数据格式参考
    :param table_name: 表名
    :return: CSV 格式数据
             1. 第一行是列信息，列之间使用英文逗号分隔
             2. 第二行开始是表数据，值之间也使用英文逗号分隔
             3. 行和行之间使用 \n 分隔
             4. 至多查询 100 条表数据
             例如：
                id,name,age\n -> 列头
                1,张三,18\n
                1,张三,18\n
                1,张三,18\n -> 至多查询 100 条
    """
    # 埋点：工具二被调用，前端可以展示当前正在预览哪张表
    monitor.report_tool(
        tool_name="数据库表数据查询工具：get_table_data",
        args={"table_name": table_name},
    )

    # 额外安全性校验：校验 table_name 是否合法（由字母、数字、下划线组成），防 SQL 注入
    if not re.match(r"^[a-zA-Z0-9_]+$", str(table_name)):
        return f"安全违规：非法的表名 '{table_name}'，只能包含字母、数字和下划线。"

    try:
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                # 使用反引号包裹表名，表名已通过安全字符校验
                sql = f"SELECT * FROM `{table_name}` LIMIT 100"
                cursor.execute(sql)

                description = cursor.description
                if not description:
                    return f"数据表 {table_name} 暂无数据。"

                columns = [desc[0] for desc in description]
                rows = cursor.fetchall()

                # 把每一行数据从元组转成 CSV 行文本
                results = [",".join(map(str, row)) for row in rows]

                header_str = ",".join(columns)
                data_str = "\n".join(results)
                return f"{header_str}\n{data_str}"
    except Error as e:
        return f"查询出现异常：{str(e)}"


@tool
def execute_sql_query(query) -> str:
    """
    执行自定义 SQL 查询

    切记：执行之前，需要通过 list_sql_tables 明确真实表名，
    再通过 get_table_data 明确表结构和数据格式。
    适合多表关联、筛选、聚合、排序等复杂查询。
    :param query: 要执行的自定义 SQL 语句
    :return: CSV 格式数据
             1. 第一行是列信息，列之间使用英文逗号分隔
             2. 第二行开始是表数据，值之间也使用英文逗号分隔
             3. 行和行之间使用 \n 分隔
             例如：
                id,name,age\n -> 列头
                1,张三,18\n
                1,张三,18\n
    """
    # 埋点：记录模型最终生成的 SQL，便于观察是否真的落到了正确表字段上
    monitor.report_tool(
        tool_name="数据库表数据查询工具：execute_sql_query", args={"query": query}
    )

    # 安全看守校验
    is_safe, error_msg = is_safe_sql(query)
    if not is_safe:
        return error_msg

    try:
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(query)

                # 非查询类 SQL 没有结果集描述
                description = cursor.description
                if not description:
                    return f"执行自定义 SQL 语句没有查询结果，SQL 为：{query}"

                columns = [desc[0] for desc in description]
                rows = cursor.fetchall()

                # 每行元组统一转为逗号分隔文本
                results = [",".join(map(str, row)) for row in rows]

                # 第一行是列名，后续是查询数据
                header_str = ",".join(columns)
                data_str = "\n".join(results)
                return f"{header_str}\n{data_str}"
    except Error as e:
        return f"查询出现异常：{str(e)}"


if __name__ == "__main__":
    # 本地调试入口：直接运行本文件可验证 .env 中的 MySQL 连接配置是否可用
    print("Testing read-only sql verification...")
    # Safe query test
    safe_query = (
        "SELECT * FROM `drugs` dgs join sales_records srd on dgs.drug_id = srd.drug_id"
    )
    is_safe, msg = is_safe_sql(safe_query)
    print(f"Safe query is safe: {is_safe}, msg: {msg}")

    # Dangerous query test
    unsafe_query = "SELECT * FROM `drugs`; DROP TABLE `drugs`;"
    is_safe, msg = is_safe_sql(unsafe_query)
    print(f"Unsafe query is safe: {is_safe}, msg: {msg}")

    unsafe_query2 = "INSERT INTO drugs (name) VALUES ('dangerous');"
    is_safe, msg = is_safe_sql(unsafe_query2)
    print(f"Unsafe query 2 is safe: {is_safe}, msg: {msg}")
