import re

def rewrite_single_table_to_hybrid_search(sql):
    """
    单表 SQL 改写为 HybridSearch 格式（仅处理纯向量检索的单表 SQL）
    :param sql: 原始单表向量检索 SQL
    :return: 改写后的 HybridSearch 格式 SQL
    """
    # 步骤 1：提取关键信息（通过正则匹配）
    # 匹配 lembed 中的模型和查询语义
    lembed_pattern = r'lembed\(\'([^\']+)\', \'([^\']+)\'\)'
    lembed_match = re.search(lembed_pattern, sql)
    if not lembed_match:
        return sql  # 无 lembed 语法，返回原 SQL
    
    model_name = lembed_match.group(1)
    query_text = lembed_match.group(2)
    
    # 匹配 distance 函数中的向量字段
    distance_pattern = r'distance\(([^,]+), [^\)]+\)'
    distance_match = re.search(distance_pattern, sql)
    if not distance_match:
        return sql  # 无 distance 语法，返回原 SQL
    
    embedding_field = distance_match.group(1).strip()
    # 推导文本字段（向量字段去除 _embedding 后缀，如 city_description_embedding → city_description）
    text_field = embedding_field.replace('_embedding', '')
    if text_field == embedding_field:
        # 若无 _embedding 后缀，默认与向量字段同名（兜底方案）
        text_field = embedding_field
    
    # 匹配表名（FROM 后的表名）
    from_pattern = r'FROM\s+([^\s]+)'
    from_match = re.search(from_pattern, sql, re.IGNORECASE)
    if not from_match:
        return sql
    
    table_name = from_match.group(1).strip()
    # 处理表别名（如 city AS c → city）
    table_name = re.sub(r'\s+AS\s+[^\s]+', '', table_name, flags=re.IGNORECASE)
    
    # 匹配 SELECT 字段（保留原查询字段，去除 distance 相关字段）
    select_pattern = r'SELECT\s+(.*?)\s+FROM'
    select_match = re.search(select_pattern, sql, re.DOTALL | re.IGNORECASE)
    if not select_match:
        return sql
    
    select_fields = select_match.group(1).strip()
    # 移除原 distance 字段（避免重复）
    select_fields = re.sub(
        r'distance\([^)]+\)\s+AS\s+distance\s*,?\s*',
        '',
        select_fields,
        flags=re.IGNORECASE
    )
    # 移除末尾多余的逗号
    select_fields = re.sub(r',\s*$', '', select_fields)
    if not select_fields:
        select_fields = '*'  # 兜底：若 SELECT 字段为空，使用 *
    
    # 匹配 LIMIT 数值
    limit_pattern = r'LIMIT\s+(\d+)'
    limit_match = re.search(limit_pattern, sql, re.IGNORECASE)
    limit_num = limit_match.group(1) if limit_match else '5'
    
    # 步骤 2：构造 HybridSearch 语句
    hybrid_search_clause = f"""
    HybridSearch(
        'fusion_type=RSF',
        'fusion_weight=0.4'
    )(
        {embedding_field},
        {text_field},
        lembed('{model_name}', '{query_text}'),
        '{query_text}'
    ) AS score
    """
    
    # 步骤 3：拼接最终 SQL（去除原 WITH 子句和 ORDER BY distance）
    final_sql = f"""SELECT 
    {select_fields},
    {hybrid_search_clause}
FROM {table_name}
ORDER BY score DESC
LIMIT {limit_num};"""
    
    # 格式化 SQL（去除多余空行和空格，提升可读性）
    final_sql = re.sub(r'\n\s+', '\n  ', final_sql)
    final_sql = re.sub(r'\s+', ' ', final_sql).strip()
    final_sql = final_sql.replace(';', '\n;')
    
    return final_sql

def process_sql_list(sql_list):
    """
    批量处理 SQL 列表，单表改写，多表返回原文
    :param sql_list: 原始 SQL 字典列表（格式与用户输入一致）
    :return: 处理后的 SQL 结果列表
    """
    processed_results = []
    for item in sql_list:
        original_sql = item.get('sql', '')
        question = item.get('question', '')
        
        # 判断是否为多表查询：包含 JOIN 关键字即为多表，直接返回原 SQL
        if 'JOIN' in original_sql.upper():
            processed_sql = original_sql
        else:
            # 单表查询：改写为 HybridSearch 格式
            processed_sql = rewrite_single_table_to_hybrid_search(original_sql)
        
        # 构造结果项
        processed_results.append({
            'question': question,
            'original_sql': original_sql,
            'processed_sql': processed_sql
        })
    
    return processed_results

# ---------------------- 示例使用 ----------------------
if __name__ == "__main__":
    # 你的原始 SQL 数据（可直接替换为完整数据）
    sample_sql_data = [
        {
            "question": "Could you show me the 5 cities that are most representative of a capital city with a rich history and vibrant culture?",
            "sql": "WITH\n    lembed('all-MiniLM-L6-v2', 'Capital city with rich history and vibrant culture') AS ref_vec_0\n\nSELECT city_name, distance(city.city_description_embedding, ref_vec_0) AS distance\nFROM city\nORDER BY distance\nLIMIT 5;"
        },
        {
            "question": "Could you show me the top 5 cities that hosted games most associated with winter conditions in a snowy region, and list their names and IDs?",
            "sql": "WITH\n    lembed('all-MiniLM-L6-v2', 'The Winter games occurred in a snowy region.') AS ref_vec_0,\n\nRankedGames AS (\n    SELECT \n        g.id AS games_id, \n        g.games_name AS games_name, \n        g.games_year AS games_year, \n        g.season AS season, \n        distance(g.games_description_embedding, ref_vec_0) AS games_distance\n      FROM games AS g\n    ORDER BY games_distance\n    LIMIT 5\n),\n\nCityGames AS (\n    SELECT \n        c.id AS city_id, \n        c.city_name AS city_name, \n        cg.games_id AS games_id\n      FROM city AS c\n      JOIN games_city AS cg ON toString(c.id) = toString(cg.city_id)\n      WHERE cg.games_id IN (SELECT games_id FROM RankedGames)\n)\n\nSELECT \n  c.city_id AS city_id, \n  c.city_name AS city_name\nFROM CityGames AS c\nJOIN RankedGames AS rg ON toString(c.games_id) = toString(rg.games_id)\nORDER BY rg.games_distance\nLIMIT 5;"
        }
    ]
    
    # 批量处理 SQL
    result = process_sql_list(sample_sql_data)
    
    # 打印处理结果
    for idx, item in enumerate(result, 1):
        print(f"===== 第 {idx} 条结果 =====")
        print(f"问题：{item['question'][:50]}...")
        print(f"\n原始 SQL：\n{item['original_sql'][:100]}...")
        print(f"\n处理后 SQL：\n{item['processed_sql']}")
        print("-" * 80 + "\n")