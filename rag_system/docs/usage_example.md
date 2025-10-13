# RAG系统使用示例

## 1. 命令行使用

### 基本查询

```bash
# 使用命令行应用处理查询
python app.py --query "什么是人工智能？" --session_id "user_123"
```

### 启动API服务

```bash
# 启动API服务
python api.py

# 或使用启动脚本
./start.sh --api
```

### 初始化系统

```bash
# 初始化系统（创建索引等）
python init.py

# 或使用启动脚本
./start.sh --init
```

## 2. API接口使用

### Python客户端示例

```python
import requests
import json

# API服务地址
API_URL = "http://localhost:8000/query"

# 查询数据
query_data = {
    "query": "什么是机器学习？",
    "session_id": "session_001"
}

# 发送POST请求
response = requests.post(API_URL, json=query_data)

# 处理响应
if response.status_code == 200:
    result = response.json()
    print(f"查询: {result['query']}")
    print(f"答案: {result['answer']}")
    print(f"意图: {result['intent']}")
else:
    print(f"请求失败: {response.status_code}")
```

### curl命令示例

```bash
# 使用curl发送查询请求
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{
    "query": "人工智能的发展历史",
    "session_id": "user_456"
  }'
```

### JavaScript客户端示例

```javascript
// 使用fetch API发送查询请求
async function queryRAGSystem(question, sessionId) {
    try {
        const response = await fetch('http://localhost:8000/query', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                query: question,
                session_id: sessionId
            })
        });
        
        if (response.ok) {
            const result = await response.json();
            console.log('查询:', result.query);
            console.log('答案:', result.answer);
            console.log('意图:', result.intent);
            return result;
        } else {
            console.error('请求失败:', response.status);
        }
    } catch (error) {
        console.error('网络错误:', error);
    }
}

// 使用示例
queryRAGSystem("什么是深度学习？", "web_user_789");
```

## 3. 系统集成示例

### 在应用中集成RAG管道

```python
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'rag_system'))

from rag_system.services.rag_pipeline import rag_pipeline

class MyApplication:
    def __init__(self):
        self.session_counter = 0
    
    def handle_user_query(self, user_input):
        # 生成会话ID
        self.session_counter += 1
        session_id = f"app_session_{self.session_counter}"
        
        # 处理查询
        result = rag_pipeline.process_query(user_input, session_id)
        
        # 返回结果
        return result
    
    def chat_loop(self):
        print("RAG问答系统 (输入 'quit' 退出)")
        while True:
            user_input = input("> ")
            if user_input.lower() == 'quit':
                break
            
            result = self.handle_user_query(user_input)
            print(f"答案: {result['answer']}")
            print("-" * 50)

# 运行应用
if __name__ == "__main__":
    app = MyApplication()
    app.chat_loop()
```

## 4. 性能测试示例

```python
import time
from rag_system.services.rag_pipeline import rag_pipeline

def performance_test():
    # 测试查询
    test_queries = [
        "什么是人工智能？",
        "机器学习和深度学习有什么区别？",
        "Python编程语言的特点是什么？",
        "太阳系中最大的行星是哪个？",
        "如何学习数据科学？"
    ]
    
    # 性能测试
    total_time = 0
    for i, query in enumerate(test_queries):
        start_time = time.time()
        result = rag_pipeline.process_query(query, f"perf_test_{i}")
        end_time = time.time()
        
        query_time = end_time - start_time
        total_time += query_time
        
        print(f"查询 {i+1}: {query}")
        print(f"耗时: {query_time:.2f}秒")
        print(f"答案长度: {len(result['answer'])}字符")
        print("-" * 50)
    
    avg_time = total_time / len(test_queries)
    print(f"平均响应时间: {avg_time:.2f}秒")

if __name__ == "__main__":
    performance_test()
```

## 5. 缓存效果验证

```python
from rag_system.services.rag_pipeline import rag_pipeline

def cache_effectiveness_test():
    query = "什么是自然语言处理？"
    session_id = "cache_test"
    
    # 第一次查询（无缓存）
    print("第一次查询（无缓存）:")
    result1 = rag_pipeline.process_query(query, session_id)
    print(f"答案: {result1['answer']}")
    print(f"是否来自缓存: {result1['from_cache']}")
    print("-" * 50)
    
    # 第二次查询（有缓存）
    print("第二次查询（有缓存）:")
    result2 = rag_pipeline.process_query(query, session_id)
    print(f"答案: {result2['answer']}")
    print(f"是否来自缓存: {result2['from_cache']}")
    print("-" * 50)
    
    # 验证答案一致性
    if result1['answer'] == result2['answer']:
        print("✓ 缓存结果一致")
    else:
        print("✗ 缓存结果不一致")

if __name__ == "__main__":
    cache_effectiveness_test()
```

## 6. Docker部署示例

### 构建Docker镜像

```bash
# 在rag_system目录下构建镜像
docker build -t rag-system .

# 运行容器
docker run -p 8000:8000 rag-system
```

### Docker Compose部署

```yaml
version: '3.8'

services:
  rag-system:
    build: ./rag_system
    ports:
      - "8000:8000"
    environment:
      - REDIS_HOST=redis
      - ELASTICSEARCH_HOST=elasticsearch
    depends_on:
      - redis
      - elasticsearch

  redis:
    image: redis:alpine
    ports:
      - "6379:6379"

  elasticsearch:
    image: docker.elastic.co/elasticsearch/elasticsearch:8.0.0
    ports:
      - "9200:9200"
    environment:
      - discovery.type=single-node
      - xpack.security.enabled=false
```

通过以上示例，您可以根据具体需求选择合适的使用方式来集成和使用RAG系统。