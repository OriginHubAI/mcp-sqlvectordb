import requests
import json

# 核心配置（仅需替换 API Key，其他无需改）
API_KEY = "app-O1vzdkyNbfYBrG4aDjHb0VQl"
DIFY_URL = "https://api.dify.ai/v1/chat-messages"


def get_agent_answer(question):
    """调用 Dify Agent 模型，返回完整回答"""
    # 请求参数（Agent 模型必须用 streaming 模式）
    payload = {
        "inputs": {},  # 必填字段（空字典即可）
        "query": question,
        "response_mode": "streaming",
        "user": "test_user",
    }
    headers = {"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}

    try:
        # 发送无代理流式请求
        resp = requests.post(
            DIFY_URL,
            headers=headers,
            json=payload,
            stream=True,
            timeout=15,  # 超时保护
        )
        resp.raise_for_status()  # 有 HTTP 错误直接抛出

        # 提取并拼接完整回答（仅保留核心 agent_message 事件）
        full_answer = ""
        for line in resp.iter_lines(chunk_size=512):  # 小分片读取，提升稳定性
            if not line:
                continue
            line_str = line.decode("utf-8").strip()
            # 只处理包含核心回答的行，过滤无关事件
            if line_str.startswith("data: ") and "agent_message" in line_str:
                try:
                    data = json.loads(line_str[6:])  # 去掉 "data: " 前缀
                    full_answer += data.get("answer", "")
                except Exception:
                    continue  # 忽略解析失败的行（不影响整体）

        return full_answer

    except Exception as e:
        return f"❌ 调用失败：{str(e)[:100]}"


# ========== 测试运行 ==========
if __name__ == "__main__":
    # 测试问题
    test_question = "Find the top 5 papers about machine learning in natural language processing"

    print("🔄 调用 Dify Agent 模型（无代理）...")
    answer = get_agent_answer(test_question)

    print("\n✅ 完整回答：")
    print("-" * 60)
    print(answer if answer else "⚠️ 未提取到回答")
    print("-" * 60)
