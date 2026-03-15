import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate, PromptTemplate
from langchain_core.messages import HumanMessage, SystemMessage

# Load environment variables from .env file
load_dotenv()

# Initialize LangChain ChatOpenAI
llm = ChatOpenAI(
    model="qwen-plus",
    api_key=os.getenv("API_KEY"),
    base_url=os.getenv("BASE_URL", "https://dashscope.aliyuncs.com/compatible-mode/v1"),
    temperature=0.7,
)

print("=" * 60)
print("示例 1: 基础调用（非流式）")
print("=" * 60)

# Method 1: Direct invoke with string
response = llm.invoke("用三句话介绍一下自然语言处理")
print(f"\n响应类型: {type(response)}")
print(f"回答内容:\n{response.content}")

# print("\n" + "=" * 60)
# print("示例 2: 使用消息对象调用")
# print("=" * 60)

# # Method 2: Using message objects
# messages = [
#     SystemMessage(content="你是一个知识渊博的助手。"),
#     HumanMessage(content="用一句话介绍一下机器学习")
# ]
# print("提问内容:"+messages[1].content)
# resp=llm.invoke(messages)
# print("回答内容:"+resp.content)

# print("\n" + "=" * 60)
# print("示例 3: 使用 PromptTemplate")
# print("=" * 60)

# # Method 3: Using PromptTemplate
# template = "用{num}句话介绍{topic}"
# prompt = PromptTemplate(
#     template=template,
#     input_variables=["num", "topic"]
# )
# formatted_prompt = prompt.format(num=2, topic="自然语言处理")
# response = llm.invoke(formatted_prompt)
# print(f"\n回答内容:\n{response.content}")

# print("\n" + "=" * 60)
print("示例 4: 流式输出")
print("=" * 60)

# Method 4: Stream output
print("\n流式回答：")
for chunk in llm.stream("用三句话介绍一下机器学习"):
    print(chunk.content, end="", flush=True)
print("\n")

print("=" * 60)
# print("示例 5: ChatPromptTemplate 链式调用")
# print("=" * 60)

# # Method 5: ChatPromptTemplate with chain
# chat_template = ChatPromptTemplate.from_messages([
#     ("system", "You are an expert in {field}."),
#     ("human", "{question}")
# ])
# chain = chat_template | llm
# response = chain.invoke({
#     "field": "machine learning",
#     "question": "What is a neural network?"
# })
# print(f"\n回答内容:\n{response.content}")



