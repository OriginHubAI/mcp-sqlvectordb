import json
import matplotlib.pyplot as plt

# 加载数据
with open("./1223/benchmark_results-20251225-220322.json", "r", encoding="utf-8") as f:
    data = json.load(f)
recall_list = [item["recall"] for item in data["details"]]
print("召回率列表:", recall_list)
print("The number of samples:", len(recall_list))
print("Recall Average:", sum(recall_list) / len(recall_list))
print("The number of 0.0 in Recall List", recall_list.count(0.0))

# 绘制直方图
plt.figure(figsize=(8, 5))
plt.hist(recall_list, bins=20, range=(0, 1), edgecolor="black", alpha=0.75)
plt.xlabel("Recall")
plt.ylabel("Samples")
plt.title("Recall Distribution")
plt.grid(axis="y", linestyle="--", alpha=0.5)
plt.tight_layout()
plt.show()
plt.savefig("recall_hist.png", dpi=200)
print("已生成 recall_hist.png，请下载查看。")
