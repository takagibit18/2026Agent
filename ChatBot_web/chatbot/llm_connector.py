import os
import requests
from dotenv import load_dotenv
import dashscope

# 加载 .env 文件中的环境变量
load_dotenv()

# 获取 API 密钥和 base URL
QWEN_API_KEY = os.getenv('QWEN_API_KEY')
QWEN_BASE_URL = os.getenv('QWEN_BASE_URL')
QWEN_MODEL = os.getenv('QWEN_MODEL', 'qwen-7b-chat')

def get_qwen_response(prompt):
    try:
        response = dashscope.Generation.call(
            api_key=QWEN_API_KEY,
            model=QWEN_MODEL,
            messages=[{'role': 'user', 'content': prompt}]
        )
        if response.status_code == 200:
            return response.output.text
        else:
            return f"Error: {response.status_code} - {response.message}"
    except Exception as e:
        return f"Error: {str(e)}"

if __name__ == "__main__":
    prompt = "你好，Qwen！"
    response = get_qwen_response(prompt)
    print(response)