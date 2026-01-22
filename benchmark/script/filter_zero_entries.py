#!/usr/bin/env python3

import json
import os

def filter_zero_recall_samples(benchmark_file_path, data_file_path, output_file_path):
    """
    从基准测试结果文件中提取recall=0.0的样本编号，然后从原始数据文件中提取对应的完整样本
    
    Args:
        benchmark_file_path (str): 基准测试结果JSON文件路径
        data_file_path (str): 原始数据JSON文件路径
        output_file_path (str): 输出JSON文件路径
    """
    # 检查输入文件是否存在
    if not os.path.exists(benchmark_file_path):
        print(f"错误: 基准测试结果文件不存在 - {benchmark_file_path}")
        return False
    
    if not os.path.exists(data_file_path):
        print(f"错误: 原始数据文件不存在 - {data_file_path}")
        return False
    
    try:
        # 读取基准测试结果文件
        with open(benchmark_file_path, 'r', encoding='utf-8') as f:
            benchmark_data = json.load(f)
        
        # 检查基准测试数据结构
        if not isinstance(benchmark_data, dict) or 'details' not in benchmark_data:
            print("错误: 基准测试数据格式不正确，缺少'details'字段")
            return False
        
        # 提取recall=0.0的sample_id
        details = benchmark_data['details']
        zero_recall_samples = [item for item in details if item.get('recall') == 0.0]
        
        # 统计过滤前的条目数
        total_samples = len(details)
        zero_recall_count = len(zero_recall_samples)
        
        print(f"基准测试结果总样本数: {total_samples}")
        print(f"recall=0.0的样本数: {zero_recall_count}")
        
        if zero_recall_count == 0:
            print("警告: 没有找到recall=0.0的样本")
            return False
        
        # 提取sample_id并转换为索引（sample_id从1开始，索引从0开始）
        sample_ids = [item['sample_id'] for item in zero_recall_samples]
        indices = [sample_id - 1 for sample_id in sample_ids]
        
        print(f"recall=0.0的sample_id: {sample_ids}")
        print(f"对应的原始数据索引: {indices}")
        
        # 读取原始数据文件
        with open(data_file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # 检查数据是否为列表
        if not isinstance(data, list):
            print("错误: 原始数据不是数组格式")
            return False
        
        # 检查索引是否有效
        max_index = len(data) - 1
        invalid_indices = [idx for idx in indices if idx < 0 or idx > max_index]
        if invalid_indices:
            print(f"错误: 以下索引无效 - {invalid_indices}")
            return False
        
        # 从原始数据中提取对应的样本
        filtered_samples = [data[idx] for idx in indices]
        
        # 将提取的样本保存到输出文件
        with open(output_file_path, 'w', encoding='utf-8') as f:
            json.dump(filtered_samples, f, ensure_ascii=False, indent=4)
        
        print("过滤完成!")
        print(f"成功提取的样本数: {len(filtered_samples)}")
        print(f"结果已保存到: {output_file_path}")
        
        return True
        
    except json.JSONDecodeError as e:
        print(f"错误: JSON文件解析失败 - {e}")
        return False
    except Exception as e:
        print(f"错误: {e}")
        return False

if __name__ == "__main__":
    # 指定要处理的JSON文件路径
    benchmark_file_path = './1223/benchmark_results-20251224-223035.json'
    data_file_path = './data/results/test/olympics/synthesis_data.json'
    output_file_path = './data/results/test/olympics/synthesis_data_zero.json'
    
    # 执行过滤操作
    filter_zero_recall_samples(benchmark_file_path, data_file_path, output_file_path)
