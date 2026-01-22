import re
import json


def filter_poor_recall_samples():
    # 定义文件路径
    log_file = "./log/CleanData/0120_lembed_sql.log"
    data_file = "./data/results/test/olympics/olympics_qs.json"
    output_file = "./data/results/test/olympics/poor_less_than_06.json"

    # 读取日志文件并提取样本信息
    poor_samples = []

    with open(log_file, "r") as f:
        log_content = f.read()

    # 使用正则表达式匹配每个完整的样本块
    sample_block_pattern = r"📝 样本 (\d+)/\d+.*?预测SQL: (.*?)\s+步骤3: 使用metrics.py进行评估.*?test_values:  (.*?)\ngolden_values:  (.*?)\nintersection:  (.*?)\n.*?Recall:\s+([\d.]+)"
    sample_blocks = re.findall(sample_block_pattern, log_content, re.DOTALL)

    # 筛选出recall<=0.2的样本并提取所有需要的字段
    for block in sample_blocks:
        sample_id = int(block[0])
        predicted_sql = block[1].strip()
        test_values_str = block[2]
        golden_values_str = block[3]
        intersection_str = block[4]
        recall = float(block[5])

        if recall < 0.6:
            # 解析集合字符串为Python对象
            try:
                # 处理可能的JSON格式字符串（如使用双引号的情况）
                if test_values_str.startswith('{"'):
                    test_values = eval(test_values_str.replace('"', "'"))
                else:
                    test_values = eval(test_values_str)

                if golden_values_str.startswith('{"'):
                    golden_values = eval(golden_values_str.replace('"', "'"))
                else:
                    golden_values = eval(golden_values_str)

                if intersection_str == "set()":
                    intersection = set()
                elif intersection_str.startswith('{"'):
                    intersection = eval(intersection_str.replace('"', "'"))
                else:
                    intersection = eval(intersection_str)
            except Exception:
                # 如果解析失败，使用空集合
                test_values = set()
                golden_values = set()
                intersection = set()

            poor_samples.append(
                {
                    "sample_id": sample_id,
                    "recall": recall,
                    "predicted_sql": predicted_sql,
                    "test_values": list(test_values),
                    "golden_values": list(golden_values),
                    "intersection": list(intersection),
                }
            )

    print(f"共找到 {len(poor_samples)} 个recall<=0.6的样本")

    # 读取原始数据文件
    with open(data_file, "r") as f:
        raw_data = json.load(f)

    # 映射样本ID到原始数据（注意：原始数据索引从0开始，样本ID从1开始）
    results = []
    for sample in poor_samples:
        raw_index = sample["sample_id"] - 1
        if raw_index < 0 or raw_index >= len(raw_data):
            print(f"警告：样本ID {sample['sample_id']} 超出原始数据范围！")
            continue

        raw_sample = raw_data[raw_index].copy()  # 复制原始样本的所有数据
        # # 添加样本ID、recall值和新字段
        # raw_sample['sample_id'] = sample['sample_id']
        # raw_sample['recall'] = sample['recall']
        # raw_sample['predicted_sql'] = sample['predicted_sql']
        # raw_sample['test_values'] = sample['test_values']
        # raw_sample['golden_values'] = sample['golden_values']
        # raw_sample['intersection'] = sample['intersection']
        # # 保留原始的sql字段，添加一个standard_sql的别名
        # raw_sample['standard_sql'] = raw_sample.get('sql', '')
        results.append(raw_sample)

    # 将结果保存到JSON文件
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    # 打印结果摘要
    print(f"已将 {len(results)} 个样本的详细信息保存到 {output_file}")
    # print("\n样本详情：")
    # for result in results:
    #     print(f"\n样本ID: {result['sample_id']}")
    #     print(f"Recall: {result['recall']}")
    #     print(f"问题: {result['question'][:100]}...")
    #     print(f"SQL复杂度: {result['sql_complexity']}")
    #     print(f"集成级别: {result['integration_level']}")


if __name__ == "__main__":
    filter_poor_recall_samples()
