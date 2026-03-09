import json
from pathlib import Path


def verify_no_duplicates(file_path):
    """
    验证文件中的数据没有重复

    Args:
        file_path: 要验证的文件路径

    Returns:
        bool: True表示没有重复，False表示有重复
    """
    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    seen_questions = set()
    duplicates = []

    for item in data:
        question = item.get("question", "")
        if question in seen_questions:
            duplicates.append(question)
        else:
            seen_questions.add(question)

    if duplicates:
        print(f"\n警告: 发现 {len(duplicates)} 个重复的问题条目:")
        for i, dup in enumerate(duplicates[:5], 1):
            print(f"  {i}. {dup[:100]}...")
        return False
    else:
        print("\n验证通过: 文件中没有任何重复数据")
        return True


def merge_and_deduplicate(input_dir, output_file):
    """
    合并目录下的所有JSON文件并去重

    Args:
        input_dir: 输入目录路径
        output_file: 输出文件路径
    """
    input_path = Path(input_dir)
    all_data = []
    seen_questions = set()

    # 获取所有JSON文件
    json_files = sorted(input_path.glob("*.json"))

    print(f"找到 {len(json_files)} 个JSON文件:")
    for f in json_files:
        print(f"  - {f.name}")

    # 读取并合并所有文件
    for json_file in json_files:
        print(f"\n处理文件: {json_file.name}")
        with open(json_file, "r", encoding="utf-8") as f:
            data = json.load(f)

        if isinstance(data, list):
            original_count = len(data)
            for item in data:
                # 使用question作为去重键
                question = item.get("question", "")
                if question and question not in seen_questions:
                    seen_questions.add(question)
                    all_data.append(item)

            # 统计去重情况
            unique_count = sum(1 for item in data if item.get("question", "") in seen_questions)
            print(f"  原始条目: {original_count}, 新增唯一条目: {unique_count}")
        else:
            print(f"  警告: {json_file.name} 不是数组格式，跳过")

    print("\n总计:")
    print(f"  合并后总条目数: {len(all_data)}")
    print(f"  去重后唯一Question数: {len(seen_questions)}")

    # 保存合并后的结果
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(all_data, f, ensure_ascii=False, indent=2)

    print(f"\n结果已保存到: {output_file}")


if __name__ == "__main__":
    input_dir = "./data/results/test/olympics"
    output_file = "./data/results/test/olympics/merged_data.json"

    merge_and_deduplicate(input_dir, output_file)

    # 验证输出文件没有重复数据
    verify_no_duplicates(output_file)
