from langchain_openai import OpenAI
import os
from openai import OpenAI
from my_llm import Qwen_api_key
from my_llm import Qwen_base_url


client = OpenAI(
    # 若没有配置环境变量，请用百炼API Key将下行替换为：api_key="sk-xxx"
    api_key=Qwen_api_key,
    base_url=Qwen_base_url,
)

completion = client.chat.completions.create(
    model="qwen-plus",
    messages=[
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "What’s the weather like today?"}
    ]
)

print(completion.choices[0].message.content)

