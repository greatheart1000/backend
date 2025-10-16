# orchestrator.py
import os
import requests
from openai import OpenAI

API = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
AI_BASE = "http://localhost:8001"

# 声明四个“函数”元数据，GPT-4o 会根据需要自动调用
FUNCTIONS = [
  {
    "name": "text_reasoning",
    "description": "文本推理",
    "parameters": {
      "type": "object",
      "properties": {
        "prompt": {"type": "string", "description": "推理输入文本"}
      },
      "required": ["prompt"]
    }
  },
  {
    "name": "image_generation",
    "description": "文生图",
    "parameters": {
      "type": "object",
      "properties": {
        "prompt": {"type": "string"},
        "width": {"type": "integer"},
        "height": {"type": "integer"}
      },
      "required": ["prompt"]
    }
  },
  {
    "name": "video_generation",
    "description": "文生视频",
    "parameters": {
      "type": "object",
      "properties": {
        "prompt": {"type": "string"},
        "duration_sec": {"type": "integer"}
      },
      "required": ["prompt"]
    }
  },
  {
    "name": "tts",
    "description": "文字转语音",
    "parameters": {
        "type": "object",
        "properties": {
          "text": {"type": "string"},
          "voice": {"type": "string"}
        },
        "required": ["text"]
    }
  }
]

def invoke_ai(func_name, args):
    # 转发到 AI 服务
    mapping = {
      "text_reasoning":    (f"{AI_BASE}/text_reasoning",    args),
      "image_generation":  (f"{AI_BASE}/image_generation",  args),
      "video_generation":  (f"{AI_BASE}/video_generation",  args),
      "tts":               (f"{AI_BASE}/tts",               args),
    }
    url, payload = mapping[func_name]
    r = requests.post(url, json=payload, timeout=30)
    return r.json()

def orchestrate(user_request: str):
    # 第一步：让 LLM 决定调用哪个函数
    resp = API.chat.completions.create(
      model="gpt-4o-mini",
      messages=[{"role":"user", "content": user_request}],
      functions=FUNCTIONS,
      stream=False
    )
    msg = resp.choices[0].message
    if msg.get("function_call"):
      name = msg.function_call.name
      args = msg.function_call.arguments
      # 调用本地微服务
      result = invoke_ai(name, args)
      return {"called": name, "result": result}
    else:
      return {"called": None, "result": msg.content}

# 测试
if __name__=="__main__":
    print(orchestrate("请帮我把这段文字翻译并生成一张插图：‘Hello World’"))