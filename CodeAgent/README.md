# Code Analysis Agent

一个基于大模型的AI Agent，能够接收代码和需求，对代码进行分析，并输出结构化的分析报告。支持动态验证功能，能够自动生成和执行测试代码来验证功能的正确性。

## 🚀 功能特性

### 核心功能
- ✅ 接收自然语言描述的功能需求
- ✅ 接收包含项目完整源代码的ZIP压缩文件
- ✅ 分析代码并生成结构化的功能定位报告
- ✅ 使用ModelScope的大模型API进行代码分析
- ✅ 支持多种编程语言 (Python, JavaScript, TypeScript, Java, C#, Go等)

### 增强功能 (加分项)
- 🎯 **动态验证功能**: 自动验证功能的正确性
- 🧪 **测试代码生成**: 根据代码自动生成可执行的测试代码
- ⚡ **测试执行**: 自动执行生成的测试代码
- 📊 **验证结果**: 返回测试执行结果和日志
- 🔄 **多项目类型支持**: 自动检测项目类型并选择合适的测试框架

## 📋 API接口

### 分析接口
```bash
POST /analyze
Content-Type: multipart/form-data

参数:
- problem_description (string): 描述项目应实现功能的自然语言文字
- code_zip (file): 包含项目完整源代码的zip压缩文件
- enable_verification (boolean, 可选): 是否启用动态验证功能
```

### 响应格式

#### 基本响应
```json
{
  "feature_analysis": [
    {
      "feature_description": "实现`创建频道`功能",
      "implementation_location": [
        {
          "file": "src/modules/channel/channel.resolver.ts",
          "function": "createChannel",
          "lines": "13-16"
        }
      ]
    }
  ],
  "execution_plan_suggestion": "要执行此项目，应首先执行 `npm install` 安装依赖，然后执行 `npm run start:dev` 来启动服务。"
}
```

#### 增强响应 (启用验证)
```json
{
  "feature_analysis": [...],
  "execution_plan_suggestion": "...",
  "functional_verification": {
    "generated_test_code": "const request = require('supertest');\nconst assert = require('assert');\n\ndescribe('GraphQL API', () => {\n  it('should create a channel and then a message in it', async () => {\n    const server = 'http://localhost:3000';\n    const createChannelQuery = `mutation { createChannel(createChannelInput: { name: \"New Channel\" }) { id, name } }`;\n    const channelRes = await request(server).post('/graphql').send({ query: createChannelQuery });\n    const channelId = channelRes.body.data.createChannel.id;\n\n    const createMessageQuery = `mutation { createMessage(createMessageInput: { channelId: ${channelId}, title: \"Hello\", content: \"World\" }) { id, title } }`;\n    const messageRes = await request(server).post('/graphql').send({ query: createMessageQuery });\n\n    assert.equal(messageRes.body.data.createMessage.title, 'Hello');\n  });\n});",
    "execution_result": {
      "tests_passed": true,
      "log": "1 passing (2s)"
    }
  }
}
```

## 🚀 快速启动

### 方式1: Docker运行 (推荐)

#### 一键启动
```bash
# 构建镜像
docker build -t code-analysis-agent .

# 运行容器
docker run -p 8000:8000 code-analysis-agent
```

#### 使用Docker Compose
```bash
# 启动服务
docker-compose up -d

# 查看日志
docker-compose logs -f

# 停止服务
docker-compose down
```

#### 测试服务
```bash
# 测试服务器
curl http://localhost:8000/

# 运行完整测试
python test.py
```

### 方式2: 本地运行

#### 1. 安装依赖
```bash
pip install -r requirements.txt
```

#### 2. 启动服务
```bash
python app.py
```

#### 3. 测试服务
```bash
curl http://localhost:8000/
```

## 🧪 功能测试

### 测试服务器健康状态
```bash
curl http://localhost:8000/
```
**预期响应**: `{"message":"Enhanced Code Analysis Agent is running"}`

### 运行完整测试
```bash
python test.py
```
**测试内容**:
- ✅ 服务器健康检查
- ✅ 基本分析功能
- ✅ 动态验证功能
- ✅ 测试代码生成
- ✅ 测试执行验证

### 测试分析接口
```bash
curl -X POST "http://localhost:8000/analyze" \
  -F "problem_description=实现用户注册登录功能" \
  -F "code_zip=@your_code.zip" \
  -F "enable_verification=true"
```

## 🔧 故障排除

### 问题1: 无法连接到服务器
```bash
# 检查容器是否运行
docker ps

# 查看容器日志
docker logs code-analysis-agent
```

### 问题2: 端口被占用
```bash
# 使用其他端口
docker run -p 8001:8000 code-analysis-agent
```

### 问题3: 构建失败
```bash
# 清理Docker缓存
docker system prune -f

# 重新构建
docker build --no-cache -t code-analysis-agent .
```

### 成功标志
当看到以下输出时，说明Agent已成功启动：
```
INFO:     Started server process [1]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000
```

## 🎯 使用示例

### 基本分析
```bash
curl -X POST "http://localhost:8000/analyze" \
  -F "problem_description=实现用户注册登录功能" \
  -F "code_zip=@your_code.zip"
```

### 增强分析 (启用动态验证)
```bash
curl -X POST "http://localhost:8000/analyze" \
  -F "problem_description=实现用户注册登录功能" \
  -F "code_zip=@your_code.zip" \
  -F "enable_verification=true"
```

### Python示例
```python
import requests

# 发送分析请求
with open('your_code.zip', 'rb') as f:
    files = {'code_zip': ('code.zip', f, 'application/zip')}
    data = {
        'problem_description': '实现用户注册登录功能',
        'enable_verification': True
    }
    
    response = requests.post(
        'http://localhost:8000/analyze',
        files=files,
        data=data
    )
    
    result = response.json()
    print(f"功能分析数量: {len(result.get('feature_analysis', []))}")
    
    if result.get('functional_verification'):
        verification = result['functional_verification']
        print(f"测试代码: {verification['generated_test_code']}")
        print(f"测试结果: {verification['execution_result']}")
```

## 🔧 技术实现

### 动态验证流程
1. **代码分析**: 使用大模型分析代码结构和功能
2. **测试生成**: 根据分析结果生成适合的测试代码
3. **项目检测**: 自动检测项目类型 (Python, Node.js, Java等)
4. **依赖安装**: 自动安装项目依赖
5. **测试执行**: 执行生成的测试代码
6. **结果返回**: 返回测试执行结果和日志

### 支持的测试框架
- **Node.js**: Jest, Mocha, Supertest
- **Python**: pytest, unittest
- **Java**: JUnit
- **其他**: 根据项目类型自动选择

### 技术栈
- **Python 3.10**
- **FastAPI** (Web框架)
- **OpenAI Python SDK** (用于调用ModelScope API)
- **Uvicorn** (ASGI服务器)
- **Docker** (容器化部署)

## 📊 项目结构

```
tuya/
├── app.py                      # 增强版Agent (主程序)
├── requirements.txt           # Python依赖
├── Dockerfile                 # Docker配置
├── docker-compose.yml         # Docker Compose配置
├── .dockerignore              # Docker忽略文件
└── README.md                  # 项目文档
```

## 🔧 配置说明

### API配置
Agent使用ModelScope API，已内置API密钥：
```python
client = OpenAI(
    base_url='https://api-inference.modelscope.cn/v1',
    api_key='ms-3e77e144-197b-44f3-93be-87c5d0f0ce16'  # 已内置
)
```

### 环境变量
- `HOST`: 服务主机 (默认: 0.0.0.0)
- `PORT`: 服务端口 (默认: 8000)
- `LOG_LEVEL`: 日志级别 (默认: INFO)

## 🚀 快速开始

1. **克隆项目**
   ```bash
   git clone <repository-url>
   cd tuya
   ```

2. **Docker运行**
   ```bash
   docker build -t code-analysis-agent .
   docker run -p 8000:8000 code-analysis-agent
   ```

3. **访问服务**
   - 服务地址: http://localhost:8000
   - API文档: http://localhost:8000/docs

## 📝 注意事项

1. **API限制**: ModelScope API有调用频率限制，请合理使用
2. **文件大小**: 单个ZIP文件限制为50MB
3. **测试执行**: 动态验证功能需要网络连接来安装依赖
4. **安全性**: 测试代码会在临时目录中执行，请确保代码安全

## 🎉 总结

这个Agent不仅能够分析代码并生成功能定位报告，还能够：

1. **自动生成测试代码** - 根据代码分析结果生成适合的测试代码
2. **执行测试验证** - 自动执行生成的测试代码来验证功能正确性
3. **返回验证结果** - 提供详细的测试执行结果和日志
4. **支持多种项目类型** - 自动检测项目类型并选择合适的测试框架

这使得Agent具备了完整的代码分析和验证能力，能够为用户提供更加全面和可靠的分析结果。