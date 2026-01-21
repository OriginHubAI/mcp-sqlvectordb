import json
import requests
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

API_KEY = os.getenv("API_KEY")
DIFY_URL = os.getenv("DIFY_URL", "https://api.dify.ai/v1/chat-messages")

def get_dify_answer_detailed(question: str):
    """调用 Dify Agent 并打印详细的流程信息"""
    payload = {
        "inputs": {},
        "query": question,
        "response_mode": "streaming",
        "user": "benchmark_user"
    }
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }

    try:
        resp = requests.post(
            DIFY_URL,
            headers=headers,
            json=payload,
            stream=True,
            timeout=60
        )
        resp.raise_for_status()

        print("=" * 80)
        print(f"查询: {question}")
        print("=" * 80)

        for line in resp.iter_lines(chunk_size=512):
            if not line:
                continue
            line_str = line.decode('utf-8').strip()

            if line_str.startswith("data: "):
                try:
                    data = json.loads(line_str[6:])
                    event_type = data.get("event", "")

                    print(f"\n[Event: {event_type}]")

                    if event_type == "agent_thought":
                        print(f"  Thought: {data.get('thought', '')}")
                        print(f"  Tool: {data.get('tool', '')}")
                        print(f"  Tool Input: {data.get('tool_input', '')}")

                    elif event_type == "agent_message":
                        print(f"  Answer: {data.get('answer', '')}")

                    elif event_type == "message":
                        print(f"  Answer: {data.get('answer', '')}")

                    elif event_type == "error":
                        print(f"  ❌ Error: {data.get('message', '')}")
                        print(f"  Code: {data.get('code', '')}")

                    elif event_type == "tool":
                        print(f"  Tool: {data.get('tool_name', '')}")
                        print(f"  Tool Output: {str(data.get('tool_output', ''))[:200]}")

                except json.JSONDecodeError as e:
                    print(f"  JSON解析错误: {e}")

    except Exception as e:
        print(f"ERROR: {str(e)}")

if __name__ == "__main__":
    # 测试几个不同的查询
    queries = [
        "列出数据库中所有的表",
        "Articles表有多少条记录？",
        "给我返回一篇文章的标题"
    ]

    for q in queries:
        get_dify_answer_detailed(q)
        print("\n\n")
