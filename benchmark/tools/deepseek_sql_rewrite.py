#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
使用DeepSeek API批量改写SQL并执行的脚本

功能特性：
- ✅ 批量处理：支持从文件读取多个SQL语句
- ✅ JSON格式：支持从JSON文件提取SQL语句
- ✅ 交互式输入：支持手动输入SQL语句
- ✅ 环境变量：支持通过环境变量设置配置
- ✅ 批量执行：自动执行所有改写后的SQL
- ✅ 结果展示：详细展示每个SQL的处理结果

使用示例：
1. 从普通文件批量处理（分号分隔）：
   python deepseek_sql_rewrite.py --sqls sql_file.txt --prompt "请帮我优化这些SQL查询"

2. 从JSON文件批量处理：
   python deepseek_sql_rewrite.py --sqls json_file.json --prompt "请帮我将这些SQL改写为带Rerank的SQL"

3. 交互式输入：
   python deepseek_sql_rewrite.py
   请输入SQL语句（输入'GO'结束，支持多行输入）:
   SELECT * FROM city LIMIT 10
   GO

文件格式支持：

1. 普通SQL文件格式（分号分隔）：
   SELECT * FROM city LIMIT 10;
   SELECT * FROM event WHERE year > 2020;
   SELECT city_name FROM city WHERE country = 'China';

2. JSON文件格式（数组）：
   [
     {
       "question": "问题1",
       "sql": "SELECT * FROM city LIMIT 10;"
     },
     {
       "question": "问题2",
       "sql": "SELECT * FROM event WHERE year > 2020;"
     }
   ]

3. JSON文件格式（单个对象）：
   {
     "question": "问题",
     "sql": "SELECT * FROM city LIMIT 10;"
   }
"""

import os
import json
import requests
import argparse
from clickhouse_connect import get_client
from typing import List, Tuple


def call_deepseek_api(original_sql: str) -> str:
    """
    调用DeepSeek API改写SQL

    Args:
        original_sql: 原始SQL语句
        prompt: 提示词
        api_key: DeepSeek API密钥

    Returns:
        改写后的SQL语句
    """
    prompt = """因为向量查询精度不高，我需要给我的sql按照我的语法，加上rerank方法。
    1. 例如例如将vector sql：WITH
    lembed('intfloat/E5-Mistral-7B-Instruct', 'bustling, vibrant, cultural, and have historical sites') AS ref_vec

SELECT 
    city_name, 
    city_description, 
    distance(city_description_embedding, ref_vec) AS distance
FROM 
    olympics.city
ORDER BY 
    distance
LIMIT 3;改写成这种rerank的格式：WITH
  -- 步骤 1：缓存带行号的原始候选集
  candidate_set_with_rownum AS (
    SELECT
      -- 生成连续行号（从 1 开始），与 Rerank 返回的行号一一对应
      rowNumberInAllBlocks() AS candidate_rownum,
      city_name,
      city_description  -- 可添加其他需要的原始字段
    FROM (
      SELECT
        city_name,
        city_description
      FROM olympics.city
      ORDER BY distance(
        city_description_embedding,
        lembed('intfloat/E5-Mistral-7B-Instruct', 'A bustling metropolis with lots of cultural landmarks')
      )
      LIMIT 10  -- 必须与 Rerank 中的候选集 LIMIT 保持一致，确保行号匹配
    )
  )
-- 步骤 2：提取 Rerank 行号 + 关联原始数据（无缝衔接你已验证成功的逻辑）
SELECT
  -- Rerank 解析结果
  tupleElement(single_rerank_tuple, 1) AS rerank_seq_num,  -- Rerank 返回的行号
  tupleElement(single_rerank_tuple, 3) AS relevance_score,  -- 可选：Rerank 相关性得分（用于排序）
  -- 原始表数据（从候选集中关联提取）
  cs.city_name,
  cs.city_description
FROM
  (
    -- 你的原始 Rerank 调用（已验证成功，无需修改）
    SELECT
      Rerank(
        'A bustling metropolis with lots of cultural landmarks',
        (
          SELECT groupArray(city_description)
          FROM (
            SELECT city_description
            FROM olympics.city
            ORDER BY distance(
              city_description_embedding,
              lembed('intfloat/E5-Mistral-7B-Instruct', 'A bustling metropolis with lots of cultural landmarks')
            )
            LIMIT 10
          )
        ),
        5, --最后需要返回的行数，也就是limit k,重写你需要按照原始sql更改这个值
        'Cohere',
        'https://api.cohere.ai/v1/rerank',
        'FtrW8La5zmyq05H14x6JV2vbYGBrFG9ILyAH3iI7',
        '{"model": "rerank-multilingual-v3.0", "top_k": 20}'
      ) AS reranked_result
  ) AS rerank_data
-- 步骤 3：展开 Rerank 集合（你已验证成功的 ARRAY JOIN）
ARRAY JOIN reranked_result AS single_rerank_tuple
-- 步骤 4：通过行号关联原始候选集（核心：匹配 Rerank 行号与原始候选集行号）
JOIN candidate_set_with_rownum cs 
  ON cs.candidate_rownum = tupleElement(single_rerank_tuple, 1)
-- 可选：按 Rerank 得分降序排序（得到最终重排序结果）
ORDER BY relevance_score DESC;
2. 改写后需要检查一下sql里表的别名对不对，能不能使用。
3. 改写后sql返回的数据格式，也就是列名与行数（limit k值），需要与原始sql一致。
4. 你需要注意，如果sql中嵌套了向量查询的子句，你也需要按照语义分别改写向量查询的子句为上面的rerank格式。
"""
    url = os.getenv("LLM_API_URL", "https://api.deepseek.com/chat/completions")
    api_key = os.getenv("LLM_API_KEY")
    headers = {"Content-Type": "application/json", "Authorization": f"Bearer {api_key}"}

    messages = [
        {
            "role": "user",
            "content": f"{prompt}\n\n原始SQL: {original_sql}\n\n请只返回改写后的可执行的SQL语句，不要包含其他多余的字符。",
        }
    ]

    data = {
        "model": "deepseek-chat",
        "messages": messages,
        "temperature": 0.1,
        "max_tokens": 1000,
        "stream": False,
    }

    try:
        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()

        result = response.json()
        if "choices" in result and len(result["choices"]) > 0:
            return result["choices"][0]["message"]["content"].strip()[
                7:-5
            ]  # 需要去掉开头的‘’‘sql 和末尾的‘’‘和分号和一个空格
        else:
            raise ValueError("DeepSeek API返回格式错误")

    except requests.RequestException as e:
        print(f"DeepSeek API调用失败: {str(e)}")
        return ""
    except Exception as e:
        print(f"DeepSeek API处理失败: {str(e)}")
        return ""


def run_sql_with_columns(
    sql: str, host: str, port: int, user: str, password: str, database: str
) -> Tuple[List[tuple], List[str]]:
    """
    执行SQL查询并返回结果和列名

    Args:
        sql: SQL查询语句
        host: 数据库主机
        port: 数据库端口
        user: 数据库用户名
        password: 数据库密码
        database: 数据库名称

    Returns:
        (查询结果数据, 查询结果列名)
    """
    client = None
    try:
        client = get_client(host=host, port=port, user=user, password=password, database=database)

        result = client.query(sql)

        if not result.result_set:
            return [], []

        column_names = result.column_names

        # 过滤掉distance和embedding字段（可选）
        distance_indices = [i for i, col in enumerate(column_names) if "distance" in col.lower()]
        embedding_indices = [i for i, col in enumerate(column_names) if "embedding" in col.lower()]
        exclude_indices = set(distance_indices + embedding_indices)

        data = []
        for row in result.result_set:
            filtered_row = tuple(
                value for idx, value in enumerate(row) if idx not in exclude_indices
            )
            data.append(filtered_row)

        filtered_columns = [
            col for idx, col in enumerate(column_names) if idx not in exclude_indices
        ]

        return data, filtered_columns

    except Exception as e:
        print(f"SQL执行失败: {str(e)}")
        return [], []
    finally:
        if client:
            client.close()


def main():
    """
    主函数
    """
    # 默认配置（来自用户提供的信息）
    DEFAULT_DEEPSEEK_API_KEY = os.getenv("LLM_API_KEY")
    DEFAULT_MYSCALE_HOST = os.getenv("MYSCALE_HOST")
    DEFAULT_MYSCALE_PORT = int(os.getenv("MYSCALE_PORT"))
    DEFAULT_MYSCALE_USER = os.getenv("MYSCALE_USER")
    DEFAULT_MYSCALE_PASSWORD = os.getenv("MYSCALE_PASSWORD")
    DEFAULT_MYSCALE_DATABASE = os.getenv("MYSCALE_DATABASE")
    DEFAULT_SQL_PATH = "./data/results/test/olympics/olympics_qs.json"
    parser = argparse.ArgumentParser(description="使用DeepSeek API批量改写SQL并执行")
    parser.add_argument(
        "--sqls", help="包含多个SQL语句的文件名（使用;分隔）", default=DEFAULT_SQL_PATH
    )
    parser.add_argument("--api-key", help="DeepSeek API密钥", default=DEFAULT_DEEPSEEK_API_KEY)
    parser.add_argument("--host", help="数据库主机", default=DEFAULT_MYSCALE_HOST)
    parser.add_argument("--port", help="数据库端口", type=int, default=DEFAULT_MYSCALE_PORT)
    parser.add_argument("--user", help="数据库用户名", default=DEFAULT_MYSCALE_USER)
    parser.add_argument("--password", help="数据库密码", default=DEFAULT_MYSCALE_PASSWORD)
    parser.add_argument("--database", help="数据库名称", default=DEFAULT_MYSCALE_DATABASE)

    args = parser.parse_args()

    sql_statements = []

    # 处理文件输入
    if args.sqls:
        try:
            with open(args.sqls, "r", encoding="utf-8") as f:
                file_content = f.read().strip()

                # 检测是否为JSON格式
                if file_content.startswith("{") or file_content.startswith("["):
                    # JSON格式解析
                    json_data = json.loads(file_content)
                    sql_statements = []

                    # 处理数组格式 [{}, {}, ...]
                    if isinstance(json_data, list):
                        for item in json_data:
                            if isinstance(item, dict) and "sql" in item:
                                sql_statements.append(item["sql"].strip())
                    # 处理单个对象格式 {}
                    elif isinstance(json_data, dict) and "sql" in json_data:
                        sql_statements.append(json_data["sql"].strip())
                    else:
                        print("JSON格式不正确，无法提取SQL语句")
                        return
                else:
                    # 普通分号分隔格式解析
                    sql_statements = file_content.split(";")
                    # 过滤掉空语句
                    sql_statements = [sql.strip() for sql in sql_statements if sql.strip()]

        except json.JSONDecodeError as e:
            print(f"JSON解析失败: {str(e)}")
            return
        except Exception as e:
            print(f"读取文件失败: {str(e)}")
            return
    else:
        # 处理交互式输入
        print("请输入SQL语句（输入'GO'结束，支持多行输入）:")
        sql_lines = []
        while True:
            line = input().strip()
            if line.upper() == "GO":
                break
            sql_lines.append(line)
        sql_text = " ".join(sql_lines).strip()
        if sql_text:
            sql_statements = [sql_text]

    if not sql_statements:
        print("没有有效的SQL语句可以处理")
        return

    if not args.api_key:
        print("请提供DeepSeek API密钥，可以使用 --api-key 参数或者设置DEEPSEEK_API_KEY环境变量")
        return

    print("=== 开始批量处理 ===")
    print(f"总共要处理 {len(sql_statements)} 个SQL语句\n")

    # 循环处理每个SQL语句
    for idx, sql in enumerate(sql_statements[40:50], 1):
        print(
            f"\n==================== 处理第 {idx}/{len(sql_statements)} 个SQL ===================="
        )
        print(f"原始SQL: {sql}")

        # 调用DeepSeek API改写SQL
        print("\n正在调用DeepSeek API改写SQL...")
        rewritten_sql = call_deepseek_api(sql)

        if not rewritten_sql:
            print("改写失败，跳过此SQL")
            continue
        print("*" * 80)
        print(f"改写后的SQL: {rewritten_sql}")
        print("*" * 80)
        # 执行改写后的SQL
        print("\n正在执行改写后的SQL...")
        data, columns = run_sql_with_columns(
            rewritten_sql, args.host, args.port, args.user, args.password, args.database
        )

        if data and columns:
            print("\n=== 执行结果 ===")
            print(f"返回列名: {columns}")
            print(f"返回行数: {len(data)}")
            print("\n结果示例:")
            # 打印前5行
            for i, row in enumerate(data[:5]):
                print(f"  行{i + 1}: {row}")
            if len(data) > 5:
                print(f"  ... 还有{len(data) - 5}行")
        else:
            print("\n执行结果为空或执行失败")

    print("\n=== 批量处理完成 ===")


if __name__ == "__main__":
    main()
