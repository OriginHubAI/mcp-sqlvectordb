import json
import shutil

def filter_synthea_samples(file_path):
    # 读取原始文件
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # 筛选出db_id为"synthea"且execution_status为"success"的样本
    synthea_samples = [sample for sample in data if sample.get('db_id') == 'synthea' and sample.get('execution_status') == 'success']
    
    print(f"原始样本数量: {len(data)}")
    print(f"筛选后样本数量: {len(synthea_samples)}")
    print(f"保留比例: {len(synthea_samples)/len(data)*100:.2f}%")
    
    # 备份原始文件
    backup_path = file_path + '.backup'
    shutil.copy2(file_path, backup_path)
    print(f"原始文件已备份到: {backup_path}")
    
    # 将筛选结果保存回原文件
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(synthea_samples, f, ensure_ascii=False, indent=2)
    
    print(f"筛选结果已保存到: {file_path}")

if __name__ == "__main__":
    # 文件路径
    file_path = "./data/results/test/synthea/candidate_sql.json"
    
    # 执行筛选
    filter_synthea_samples(file_path)