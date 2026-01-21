import json
import os

def filter_duplicate_samples(input_file_1, input_file_2, output_file):
    # 读取输入文件
    with open(input_file_1, 'r', encoding='utf-8') as f:
        data_1 = json.load(f)
    
    with open(input_file_2, 'r', encoding='utf-8') as f:
        data_2 = json.load(f)
    
    print(f"输入文件1样本数量: {len(data_1)}")
    print(f"输入文件2样本数量: {len(data_2)}")

    # 使用question作为唯一key进行去重
    unique_samples_dict = {}
    
    for sample in data_1 + data_2:
        # 获取question字段作为唯一键
        question = sample.get('sql', '')
        # 如果question为空，使用样本的JSON字符串作为备选键
        if not question:
            question = json.dumps(sample, ensure_ascii=False, sort_keys=True)
        unique_samples_dict[question] = sample
    
    # 提取去重后的样本
    unique_samples = list(unique_samples_dict.values())

    print(f"去重后样本数量: {len(unique_samples)}")
    print(f"重复样本数量: {len(data_1 + data_2) - len(unique_samples)}")
    
    # 保存结果到输出文件
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(unique_samples, f, ensure_ascii=False, indent=2)
    
    print(f"去重结果已保存到: {output_file}")

if __name__ == "__main__":
    # 输入文件路径
    input_file_1 = "./data/results/test/olympics/0112/success_samples.json"
    input_file_2 = "./data/results/test/olympics/merged_data.json"
    # 输出文件路径（避免覆盖原始文件，使用新的文件名）
    output_file = "./data/results/test/olympics/0112/unique_samples.json"
    
    filter_duplicate_samples(input_file_1, input_file_2, output_file)
