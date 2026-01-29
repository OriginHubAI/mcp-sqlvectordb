import json
import requests

API_KEY = "app-O1vzdkyNbfYBrG4aDjHb0VQl"
DIFY_URL = "https://api.dify.ai/v1/chat-messages"


def test_dify_response():
    """测试Dify API的实际响应格式"""
    payload = {
        "inputs": {},
        "query": "列出数据库中所有的表",
        "response_mode": "streaming",
        "user": "test_user",
    }
    headers = {"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}

    try:
        resp = requests.post(DIFY_URL, headers=headers, json=payload, stream=True, timeout=30)
        resp.raise_for_status()

        print("=" * 80)
        print("原始流式响应数据:")
        print("=" * 80)

        for i, line in enumerate(resp.iter_lines(chunk_size=512)):
            if not line:
                continue
            line_str = line.decode("utf-8").strip()
            print(f"\n[Line {i + 1}]")
            print(line_str)

            # 尝试解析JSON
            if line_str.startswith("data: "):
                try:
                    data = json.loads(line_str[6:])
                    print(f"  -> 解析后的event: {data.get('event', 'N/A')}")
                    print(f"  -> 包含answer字段: {'answer' in data}")
                    if "answer" in data:
                        print(f"  -> answer内容: {data['answer'][:100]}")
                except Exception as e:
                    print(f"  -> JSON解析失败: {e}")

    except Exception as e:
        print(f"ERROR: {str(e)}")


if __name__ == "__main__":
    test_dify_response()
