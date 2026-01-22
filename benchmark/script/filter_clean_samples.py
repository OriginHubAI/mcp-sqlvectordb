#!/usr/bin/env python3
import re
import json


def filter_clean_samples():
    """
    从日志文件中提取recall>0.2的样本ID，
    然后从原始数据文件中过滤出这些样本，
    生成格式与原始文件一致的clean_data.json
    """
    # 定义文件路径
    log_file = './log/CleanData/0113_lab.log'
    data_file = './data/results/test/olympics/clean_data.json'
    output_file = './script/clean_data.json'
    
    # 读取日志文件并提取所有样本的recall信息
    all_samples_recall = []
    
    with open(log_file, 'r') as f:
        log_content = f.read()
    
    # 使用正则表达式匹配每个样本的ID和recall值
    sample_pattern = r'📝 样本 (\d+)/\d+.*?Recall:\s+([\d.]+)'
    sample_records = re.findall(sample_pattern, log_content, re.DOTALL)
    
    # 解析所有样本的recall值
    for record in sample_records:
        sample_id = int(record[0])
        recall = float(record[1])
        all_samples_recall.append({
            'sample_id': sample_id,
            'recall': recall
        })
    
    # 筛选出recall>0.2的样本ID
    good_sample_ids = set()
    for sample in all_samples_recall:
        if sample['recall'] > 0.2:
            good_sample_ids.add(sample['sample_id'])
    
    print(f"共找到 {len(good_sample_ids)} 个recall>0.2的样本")
    
    # 读取原始数据文件
    with open(data_file, 'r') as f:
        raw_data = json.load(f)
    
    # 过滤出recall>0.2的样本（注意：原始数据索引从0开始，样本ID从1开始）
    clean_data = []
    for idx, sample in enumerate(raw_data):
        sample_id = idx + 1  # 样本ID从1开始
        if sample_id in good_sample_ids:
            clean_data.append(sample)
    
    # 将结果保存到JSON文件
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(clean_data, f, ensure_ascii=False, indent=2)
    
    # 打印结果摘要
    print(f"已将 {len(clean_data)} 个优质样本保存到 {output_file}")


if __name__ == "__main__":
    filter_clean_samples()
