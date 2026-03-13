import os
import requests
from dotenv import load_dotenv

# 加载 .env 文件中的环境变量
load_dotenv()

# 获取 API 密钥和 base URL
QWEN_API_KEY = os.getenv('QWEN_API_KEY')
QWEN_BASE_URL = os.getenv('QWEN_BASE_URL')
QWEN_MODEL = os.getenv('QWEN_MODEL', 'qwen-7b-chat')

def get_qwen_response(prompt):
    headers = {
        'Authorization': f'Bearer {QWEN_API_KEY}',
        'Content-Type': 'application/json'
    }
    data = {
        'model': QWEN_MODEL,
        'messages': [{'role': 'user', 'content': prompt}]
    }
    response = requests.post(f'{QWEN_BASE_URL}/chat/completions', headers=headers, json=data)
    if response.status_code == 200:
        return response.json().get('choices', [{}])[0].get('message', {}).get('content', '')
    else:
        return f"Error: {response.status_code} - {response.text}"

if __name__ == "__main__":
    prompt = "你好，Qwen！"
    response = get_qwen_response(prompt)
    print(response)