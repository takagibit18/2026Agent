# Qwen API 404错误排查与修复指南

## 问题现象
前端页面可正常访问，但提交消息后返回`Error: 404 -`错误，服务器日志显示请求成功(200)，但实际调用Qwen API失败。

## 根本原因分析
经过系统排查，发现是**API请求格式不匹配**导致的链式错误：

1. **错误的API端点路径**（核心问题）
   - 错误路径：`/v1/completions`
   - 正确路径：`/v1/chat/completions`
   - 原因：Qwen兼容OpenAI的API采用**chat completions**标准接口，而非基础completions

2. **请求参数结构错误**
   ```diff
   - {
   -   "prompt": "你好"
   - }
   + {
   +   "messages": [
   +     {"role": "user", "content": "你好"}
   +   ]
   + }
   ```
   - Qwen要求使用`messages`数组格式（符合OpenAI标准）
   - 原代码使用`prompt`字段导致API返回400错误（但被错误包装为404）

3. **响应解析逻辑错误**
   ```diff
   - response.json().get('choices', [{}])[0].get('text', '')
   + response.json().get('choices', [{}])[0].get('message', {}).get('content', '')
   ```
   - Qwen返回结构使用`message.content`而非`text`字段

4. **模型名称配置问题**
   - `qwen-turbo`不支持OpenAI兼容模式
   - 正确值应为`qwen-max`（需确认API文档）

## 调试过程关键节点

### 1. 验证API端点
```powershell
# 错误请求（404）
Invoke-RestMethod -Uri "https://dashscope.aliyuncs.com/compatible-mode/v1/completions" ...

# 正确请求（200）
Invoke-RestMethod -Uri "https://dashscope.aliyuncs.com/v1/chat/completions" ...
```

### 2. 捕获真实错误
当使用`/v1/completions`时：
```json
{"error": {
  "message": "Unsupported model for OpenAI compatibility mode",
  "code": "model_not_supported"
}}
```
但被错误包装为404，导致排查方向错误

### 3. 关键转折点
发现服务器日志显示：
```
127.0.0.1 - - [POST /chat] 200
```
说明**Flask路由正常**，问题出在**下游API调用**

## 修复步骤
1. 修正API请求路径：
   ```python
   # 原错误
   f'{QWEN_BASE_URL}/v1/completions'
   
   # 修正后
   f'{QWEN_BASE_URL}/chat/completions'
   ```

2. 调整请求参数结构：
   ```python
   data = {
       'model': 'qwen-max',
       'messages': [{'role': 'user', 'content': prompt}]
   }
   ```

3. 修正响应解析逻辑：
   ```python
   return response.json()['choices'][0]['message']['content']
   ```

4. 更新环境变量：
   ```env
   QWEN_BASE_URL=https://dashscope.aliyuncs.com/v1
   QWEN_MODEL=qwen-max
   ```

## 验证方法
```powershell
# 1. 直接测试API
Invoke-RestMethod -Uri "https://dashscope.aliyuncs.com/v1/chat/completions" `
  -Headers @{
    "Authorization" = "Bearer $env:QWEN_API_KEY"
    "Content-Type" = "application/json"
  } `
  -Body '{ "model": "qwen-max", "messages": [{"role":"user","content":"你好"}] }'

# 2. 测试服务端点
Invoke-RestMethod http://127.0.0.1:5000/chat -Method Post `
  -Body '{"message": "你好"}' -ContentType "application/json"
```

## 经验总结
1. **区分HTTP状态码含义**：
   - 404：资源不存在（此处是API端点错误）
   - 400：参数错误（真实问题，但被错误包装）

2. **调试技巧**：
   - 直接调用下游API验证（绕过应用层）
   - 检查完整响应内容而非仅状态码
   - 使用`print(response.text)`输出原始响应

3. **Qwen特殊要求**：
   - 必须使用`/v1/chat/completions`端点
   - 必须使用`messages`参数结构
   - 模型名称需与API文档严格匹配