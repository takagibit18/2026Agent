import os
from dotenv import load_dotenv
load_dotenv('.env.example')
# Configuration module for LLM-related settings.

# API key for the 百炼/开放AI service. 真实项目中请不要直接把密钥写在代码里，
# 可以改为读取环境变量或者使用更安全的密钥管理方案。
Qwen_api_key = os.getenv("API_KEY")
Qwen_base_url= os.getenv("database_url")
