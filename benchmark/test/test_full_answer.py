import json
import requests

API_KEY = "app-O1vzdkyNbfYBrG4aDjHb0VQl"
DIFY_URL = "https://api.dify.ai/v1/chat-messages"

def get_full_answer(question: str):
    """获取完整答案"""
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

        full_answer = ""
        has_error = False
        error_message = ""

        for line in resp.iter_lines(chunk_size=512):
            if not line:
                continue
            line_str = line.decode('utf-8').strip()

            if line_str.startswith("data: "):
                try:
                    data = json.loads(line_str[6:])
                    event_type = data.get("event", "")

                    if event_type == "error":
                        has_error = True
                        error_message = data.get("message", "Unknown error")
                        break

                    if "answer" in data:
                        full_answer += data.get("answer", "")

                except json.JSONDecodeError:
                    continue

        if has_error:
            return f"ERROR: {error_message}"

        return full_answer

    except Exception as e:
        return f"ERROR: {str(e)}"

if __name__ == "__main__":
    question = "Hey! Could you give me the list of all the article titles you've got in the database?"
    print(f"查询: {question}\n")
    answer = get_full_answer(question)
    print(f"答案长度: {len(answer)} 字符")
    print(f"\n完整答案:\n{answer}")

    # 检查是否包含标准答案
    standard_answers = ['Test Article 0', 'Test Article 1', 'Test Article 2']
    print(f"\n\n检查标准答案:")
    for ans in standard_answers:
        if ans in answer:
            print(f"  ✅ 找到: {ans}")
        else:
            print(f"  ❌ 未找到: {ans}")
