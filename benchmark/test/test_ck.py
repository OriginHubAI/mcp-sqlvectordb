import os
import pandas as pd
from clickhouse_connect import get_client


def get_myscale_client():
    """创建并返回 MyScaleDB 客户端"""
    return get_client(
        host=os.getenv("MYSCALE_HOST"),  # 你的MyScale IP
        port=int(os.getenv("MYSCALE_PORT")),  # HTTP客户端专用端口
        user=os.getenv("MYSCALE_USER"),  # 用户名
        password=os.getenv("MYSCALE_PASSWORD"),  # 密码
        database=os.getenv("MYSCALE_DATABASE"),  # 默认数据库
    )


def run_myscale_sql(sql: str, return_df: bool = True):
    """
    执行 MyScale SQL 并返回结果（终极兼容版）
    :param sql: 要执行的SQL语句
    :param return_df: 是否返回DataFrame（False返回原生结果）
    :return: 执行结果（DataFrame/原生结果）
    """
    client = None
    try:
        # 创建客户端
        client = get_myscale_client()
        print(f"🔍 执行SQL: {sql}")

        # 执行SQL
        result = client.query(sql)

        # 处理结果（终极兼容：适配所有clickhouse-connect版本）
        if return_df:
            # 无结果集（DDL语句）
            if not result.result_set:
                print("✅ 执行成功！无返回数据（DDL语句）")
                return None
            # 有结果集：直接用column_names作为列名（兼容字符串列表格式）
            else:
                # 核心修复：column_names本身就是字符串列表，无需解析字典
                columns = result.column_names
                data = result.result_set
                df = pd.DataFrame(data, columns=columns)
                print(f"✅ 执行成功！返回 {len(df)} 行数据")
                return df
        else:
            print("✅ 执行成功！")
            return result
    except Exception as e:
        print(f"❌ SQL执行失败: {str(e)}")
        raise
    finally:
        # 确保客户端连接关闭
        if client:
            client.close()


# ========== 极简测试示例 ==========
if __name__ == "__main__":
    # 测试1：查看所有表（最基础、最易成功的测试）
    print("===== 测试1：查看数据库中所有表 =====")
    sql1 = "SHOW TABLES"
    df1 = run_myscale_sql(sql1)
    if df1 is not None:
        print(df1)

    # 测试2：执行简单查询（验证数据返回）
    print("\n===== 测试2：执行简单计数查询 =====")
    sql2 = "SELECT 1 as test_col, 'hello' as test_str"
    df2 = run_myscale_sql(sql2)
    if df2 is not None:
        print(df2)
