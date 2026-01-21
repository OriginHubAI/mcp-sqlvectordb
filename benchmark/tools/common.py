#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Common utilities for the Text2VectorSQL Benchmark
"""

import re
from typing import List, Tuple
from clickhouse_connect import get_client



def get_dify_answer(question: str, api_key: str, dify_url: str) -> str:
    """
    调用 Dify API 获取回答
    
    Args:
        question: 自然语言问题
        api_key: Dify API 密钥
        dify_url: Dify API URL
        
    Returns:
        Dify 回答内容
    """
    payload = {
        "inputs": {},
        "query": question,
        "response_mode": "streaming",
        "user": "benchmark_user"
    }
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    try:
        import requests
        import json
        resp = requests.post(dify_url, headers=headers, json=payload, stream=True, timeout=60)
        resp.raise_for_status()

        full_answer = ""
        for line in resp.iter_lines(chunk_size=512, decode_unicode=True):
            if not line:
                continue
            line = line.strip()
            if line.startswith("data: "):
                try:
                    chunk = json.loads(line[6:])
                    if chunk.get("event") in {"message", "agent_message", "agent_thought"}:
                        full_answer += chunk.get("answer") or chunk.get("thought") or ""
                except json.JSONDecodeError:
                    continue
        return full_answer or "ERROR: empty answer"

    except Exception as e:
        return f"ERROR: {str(e)}"


def unify_lembed_clauses(standard_sql, predicted_sql):
    """
    统一标准SQL和预测SQL的lembed子句
    
    Args:
        standard_sql: 标准SQL语句
        predicted_sql: 预测SQL语句
        
    Returns:
        统一后的预测SQL语句
    """
    # 改进的lembed子句提取模式，能够处理包含单引号的文本
    # 匹配模式：lembed(模型名, 文本内容)，支持单引号和双引号
    lembed_pattern = r'lembed\s*\(\s*([^,]+?),\s*(["\'])(.*?)\2\s*\)'
    
    # 提取标准SQL中的lembed子句
    standard_matches = list(re.finditer(lembed_pattern, standard_sql, re.DOTALL))
    # 提取预测SQL中的lembed子句
    predicted_matches = list(re.finditer(lembed_pattern, predicted_sql, re.DOTALL))
    
    # 如果两者都只有一句lembed子句，则进行替换
    if len(standard_matches) == 1 and len(predicted_matches) == 1:
        # 提取标准SQL的lembed子句信息
        standard_match = standard_matches[0]
        standard_text = standard_match.group(3)
        
        # 提取预测SQL的lembed子句信息
        predicted_match = predicted_matches[0]
        predicted_model = predicted_match.group(1).strip()
        predicted_quote = predicted_match.group(2)  # 预测SQL使用的引号类型
        predicted_lembed_full = predicted_match.group(0)
        
        # 处理文本中的引号：如果标准文本中包含预测SQL使用的引号，则转义
        if predicted_quote in standard_text:
            # 转义标准文本中的引号
            escaped_text = standard_text.replace(predicted_quote, f'\\{predicted_quote}')
        else:
            escaped_text = standard_text
        
        # 构建统一后的lembed子句：使用标准SQL的文本内容，预测SQL的模型名和引号类型
        unified_lembed = f"lembed({predicted_model}, {predicted_quote}{escaped_text}{predicted_quote})"
        
        # 将预测SQL中的lembed子句替换为统一后的lembed子句
        unified_sql = predicted_sql.replace(predicted_lembed_full, unified_lembed)
        
        return unified_sql
    
    return predicted_sql

