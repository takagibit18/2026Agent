
import os
from dotenv import load_dotenv

# Load environment variables from .env file in project root
load_dotenv(dotenv_path="../.env")

# Configuration constants
API_KEY = os.getenv("API_KEY")
BASE_URL = os.getenv("BASE_URL", "https://dashscope.aliyuncs.com/compatible-mode/v1")
MODEL_NAME = os.getenv("MODEL_NAME", "qwen-plus")

# Validate critical variables
if not API_KEY:
    raise ValueError("API_KEY not set. Please create a .env file with your credentials.")
