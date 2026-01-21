#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
解析日志文件，提取每个样本的相关信息
"""

import re
import json
from typing import Dict, List, Any

def parse_log_file(log_path: str) -> List[Dict[str, Any]]:
    """
    解析日志文件，提取每个样本的信息
    
    Args:
        log_path: 日志文件路径
        
    Returns:
        包含每个样本信息的列表
    """
    with open(log_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    samples = []
    
    # 使用样本标记分割样本
    sample_pattern = r'📝 样本 (\d+)/(\d+)'
    sample_matches = list(re.finditer(sample_pattern, content))
    
    for i in range(len(sample_matches)):
        start = sample_matches[i].end()
        end = sample_matches[i+1].start() if i < len(sample_matches) - 1 else len(content)
        sample_content = content[start:end]
        
        # 提取问题
        question_pattern = r'问题: (.+?)\s*\n\n'
        question_match = re.search(question_pattern, sample_content, re.DOTALL)
        question = question_match.group(1).strip() if question_match else None
        
        # 提取标准SQL
        standard_sql_pattern = r'    标准SQL: ([\s\S]+?)\s*    预测SQL:'
        standard_sql_match = re.search(standard_sql_pattern, sample_content)
        standard_sql = standard_sql_match.group(1).strip() if standard_sql_match else None
        
        # 提取预测SQL
        predicted_sql_pattern = r'    预测SQL: ([\s\S]+?)\s*    步骤3:'
        predicted_sql_match = re.search(predicted_sql_pattern, sample_content)
        predicted_sql = predicted_sql_match.group(1).strip() if predicted_sql_match else None
        
        # 提取test_values
        test_values_pattern = r'test_values:  (.+?)\s*golden_values:  '
        test_values_match = re.search(test_values_pattern, sample_content, re.DOTALL)
        test_values = test_values_match.group(1).strip() if test_values_match else None
        
        # 提取golden_values
        golden_values_pattern = r'golden_values:  (.+?)\s*intersection:  '
        golden_values_match = re.search(golden_values_pattern, sample_content, re.DOTALL)
        golden_values = golden_values_match.group(1).strip() if golden_values_match else None
        
        # 提取intersection
        intersection_pattern = r'intersection:  (.+?)\s*    ✅ 评估结果:'
        intersection_match = re.search(intersection_pattern, sample_content, re.DOTALL)
        intersection = intersection_match.group(1).strip() if intersection_match else None
        
        # 提取评估指标
        metrics_pattern = r'       Exact Match: (\d+\.\d+)\s+Precision:   (\d+\.\d+)\s+Recall:      (\d+\.\d+)\s+F1:          (\d+\.\d+)\s+MAP:         (\d+\.\d+)\s+MRR:         (\d+\.\d+)\s+NDCG:        (\d+\.\d+)\s+LLM Overall: (\d+\.\d+)'
        metrics_match = re.search(metrics_pattern, sample_content, re.DOTALL)
        metrics = {
            'Exact Match': float(metrics_match.group(1)) if metrics_match else None,
            'Precision': float(metrics_match.group(2)) if metrics_match else None,
            'Recall': float(metrics_match.group(3)) if metrics_match else None,
            'F1': float(metrics_match.group(4)) if metrics_match else None,
            'MAP': float(metrics_match.group(5)) if metrics_match else None,
            'MRR': float(metrics_match.group(6)) if metrics_match else None,
            'NDCG': float(metrics_match.group(7)) if metrics_match else None,
            'LLM Overall': float(metrics_match.group(8)) if metrics_match else None
        } if metrics_match else None
        
        sample_info = {
            'sample_id': i + 1,
            'question': question,
            'standard_sql': standard_sql,
            'predicted_sql': predicted_sql,
            'test_values': test_values,
            'golden_values': golden_values,
            'intersection': intersection,
            'metrics': metrics
        }
        
        samples.append(sample_info)
    
    return samples

def main():
    log_path = './log/CleanData/0119_100.log'
    samples = parse_log_file(log_path)
    
    # 输出结果
    print(f"共提取到 {len(samples)} 个样本")
    
    # 打印前几个样本的信息
    for i, sample in enumerate(samples[:5]):
        print(f"\n=== 样本 {sample['sample_id']} ===")
        print(f"问题: {sample['question'][:50]}..." if sample['question'] and len(sample['question']) > 50 else f"问题: {sample['question']}")
        print(f"标准SQL: {'存在' if sample['standard_sql'] else 'None'}")
        print(f"预测SQL: {'存在' if sample['predicted_sql'] else 'None'}")
        print(f"test_values: {sample['test_values']}")
        print(f"golden_values: {sample['golden_values']}")
        print(f"intersection: {sample['intersection']}")
        print(f"评估指标: {sample['metrics']}")
    
    # 保存为JSON文件
    output_path = './tools/log_analysis_result.json'
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(samples, f, ensure_ascii=False, indent=2)
    
    print(f"\n结果已保存到: {output_path}")

if __name__ == "__main__":
    main()
