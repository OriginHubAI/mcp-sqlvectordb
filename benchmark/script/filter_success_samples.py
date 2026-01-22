#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
根据Recall值过滤样本的脚本

用途：从JSON格式的基准测试结果中，根据Recall值过滤样本

使用方法：
python filter_success_samples.py
"""

import json
import os

def filter_samples_by_recall(input_file, output_file, recall_threshold=0.6, operator="<"):
    """
    根据Recall值过滤样本
    
    Args:
        input_file (str): 输入JSON文件路径
        output_file (str): 输出JSON文件路径
        recall_threshold (float): Recall阈值，默认0.6
        operator (str): 比较操作符，可以是"<", "<=", ">", ">=", "==", "!="，默认"<"
    
    Returns:
        None
    """
    # 参数验证
    if not os.path.exists(input_file):
        print(f"错误：输入文件 {input_file} 不存在！")
        return
    
    if operator not in ["<", "<=", ">", ">=", "==", "!="]:
        print(f"错误：无效的操作符 {operator}，请使用 <, <=, >, >=, ==, !=")
        return
    
    try:
        # 读取输入文件
        with open(input_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # 从'details'字段获取样本列表
        samples = data.get('details', [])
        print(f"成功读取输入文件，共 {len(samples)} 个样本")
        
        # 过滤样本
        filtered_samples = []
        for i, sample in enumerate(samples):
            # 跳过非字典类型的样本
            if not isinstance(sample, dict):
                print(f"警告：样本 {i+1} 不是字典类型，跳过处理")
                continue
            
            # 获取evaluation字段
            evaluation = sample.get('evaluation')
            if evaluation is None:
                continue
            
            # 跳过evaluation不是字典的样本
            if not isinstance(evaluation, dict):
                print(f"警告：样本 {i+1} 的evaluation不是字典类型，跳过处理")
                continue
            
            # 获取recall值（注意字段名是小写的'recall'）
            recall = evaluation.get('recall', 0.0)
            
            # 确保recall是数值类型
            if not isinstance(recall, (int, float)):
                print(f"警告：样本 {i+1} 的recall值不是数值类型，跳过处理")
                continue
            
            # 根据操作符过滤
            match operator:
                case "<":
                    if recall < recall_threshold:
                        filtered_samples.append(sample)
                case "<=":
                    if recall <= recall_threshold:
                        filtered_samples.append(sample)
                case ">":
                    if recall > recall_threshold:
                        filtered_samples.append(sample)
                case ">=":
                    if recall >= recall_threshold:
                        filtered_samples.append(sample)
                case "==":
                    if recall == recall_threshold:
                        filtered_samples.append(sample)
                case "!=":
                    if recall != recall_threshold:
                        filtered_samples.append(sample)
        
        # 保存结果到输出文件
        with open(output_file, 'w', encoding='utf-8') as f:
            # 先将filtered_samples中的SQL字符串处理一下，让换行符更美观
            for sample in filtered_samples:
                # 处理standard_sql
                if 'standard_sql' in sample and isinstance(sample['standard_sql'], str):
                    # 确保SQL中的换行符被正确处理
                    sample['standard_sql'] = sample['standard_sql'].strip()
                # 处理predicted_sql
                if 'predicted_sql' in sample and isinstance(sample['predicted_sql'], str):
                    # 确保SQL中的换行符被正确处理
                    sample['predicted_sql'] = sample['predicted_sql'].strip()
                # 确保evaluation字段的所有信息都被保留
                if 'evaluation' in sample:
                    # 确保evaluation是字典类型
                    if isinstance(sample['evaluation'], dict):
                        # 保留evaluation字段的所有内容，包括golden_data和golden_columns
                        pass
            
            # 生成JSON并写入文件
            json_str = json.dumps(filtered_samples, ensure_ascii=False, indent=2)
            f.write(json_str)
            
            # 同时生成一个SQL可读版本的文件，方便查看
            readable_output_file = output_file.replace('.json', '_readable.json')
            with open(readable_output_file, 'w', encoding='utf-8') as rf:
                # 生成一个更易读的版本，适合直接查看
                for i, sample in enumerate(filtered_samples):
                    rf.write(f"\n{'='*80}\n")
                    rf.write(f"样本 {i+1}: {sample.get('sample_id', 'N/A')}\n")
                    rf.write(f"{'='*80}\n")
                    rf.write(f"问题: {sample.get('question', 'N/A')}\n\n")
                    rf.write(f"标准SQL:\n{sample.get('standard_sql', 'N/A')}\n\n")
                    rf.write(f"预测SQL:\n{sample.get('predicted_sql', 'N/A')}\n\n")
                    
                    # 打印evaluation字段的详细信息，包括golden_data和golden_columns
                    evaluation = sample.get('evaluation', {})
                    if evaluation:
                        rf.write("评估结果:\n")
                        rf.write(f"  Recall: {evaluation.get('recall', 'N/A')}\n")
                        rf.write(f"  Precision: {evaluation.get('precision', 'N/A')}\n")
                        rf.write(f"  F1: {evaluation.get('f1', 'N/A')}\n")
                        rf.write(f"  Exact Match: {evaluation.get('exact_match', 'N/A')}\n")
                        
                        # 打印golden_data和golden_columns
                        if 'golden_data' in evaluation:
                            rf.write(f"  Golden Data: {evaluation['golden_data']}\n")
                        if 'golden_columns' in evaluation:
                            rf.write(f"  Golden Columns: {evaluation['golden_columns']}\n")
                            
            
            print(f"\n可读版本已保存到: {readable_output_file}")
        
        print("过滤完成！")
        print(f"原始样本数量: {len(samples)}")
        print(f"过滤后样本数量: {len(filtered_samples)}")
        print(f"结果已保存到: {output_file}")
        print(f"过滤条件: Recall {operator} {recall_threshold}")
    
    except json.JSONDecodeError:
        print(f"错误：输入文件 {input_file} 不是有效的JSON格式！")
    except Exception as e:
        print(f"错误：处理文件时发生异常 - {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    # 输入文件路径
    input_file = "./0120/CleanData/benchmark_results-20260120-235803.json"
    # 输出文件路径
    output_file = "./tools/recall_less_than_06.json"
    
    # 过滤Recall < 0.6的样本
    filter_samples_by_recall(input_file, output_file, recall_threshold=0.6, operator="<")
