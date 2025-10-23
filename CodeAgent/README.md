# Code Analysis Agent

一个基于大模型的AI代码分析Agent，能够接收代码和需求描述，自动分析代码结构并生成功能定位报告。

## 🚀 快速开始

### Docker部署（推荐）

```bash
# 1. 启动服务
docker-compose up -d

# 2. 快速测试（3秒验证）
bash quick_test.sh          # Linux/Mac
# 或
./quick_test.ps1             # Windows PowerShell

# 3. 完整测试（可选）
python test_agent.py
```

**验证成功标志**：看到 `✓ 基础测试全部通过！`

### 本地运行

```bash
pip install -r requirements.txt
python app.py
```

## 📋 功能特性

- ✅ 代码结构分析和功能定位
- ✅ 自动生成功能实现报告
- ✅ 支持多种编程语言（Python, Node.js, TypeScript, Java等）
- ✅ 可选的测试代码生成和执行
- ✅ 内置API密钥，开箱即用

## 🐳 Docker使用

### 启动服务
```bash
docker-compose up -d
```

### 查看日志
```bash
docker-compose logs -f
```

### 停止服务
```bash
docker-compose down
```

### 重启服务
```bash
docker-compose restart
```

## 📡 API使用

### 健康检查
```bash
curl http://localhost:8000/health
```

### 代码分析
```bash
curl -X POST "http://localhost:8000/analyze" \
  -F "problem_description=实现用户登录和注册功能" \
  -F "code_zip=@./your_project.zip"
```

### 带测试验证
```bash
curl -X POST "http://localhost:8000/analyze" \
  -F "problem_description=实现用户登录和注册功能" \
  -F "code_zip=@./your_project.zip" \
  -F "enable_verification=true"
```

### Python示例
```python
import requests

with open('project.zip', 'rb') as f:
    files = {'code_zip': f}
    data = {'problem_description': '实现用户登录功能'}
    response = requests.post('http://localhost:8000/analyze', files=files, data=data)
    print(response.json())
```

## 📊 响应格式

```json
{
  "feature_analysis": [
    {
      "feature_description": "实现用户登录功能",
      "implementation_location": [
        {
          "file": "src/auth/login.py",
          "function": "login",
          "lines": "10-25"
        }
      ]
    }
  ],
  "execution_plan_suggestion": "1. 安装依赖\n2. 运行项目",
  "functional_verification": {
    "generated_test_code": "...",
    "execution_result": {
      "tests_passed": true,
      "log": "测试通过"
    }
  }
}
```

## 🧪 测试

运行完整功能测试：

```bash
python test_agent.py
```

测试会自动创建示例项目并验证所有功能。

## ⚙️ 配置

### 默认配置（已内置）
- API地址: `https://api-inference.modelscope.cn/v1`
- 模型: `Qwen/Qwen3-VL-30B-A3B-Instruct`
- API密钥: 已内置（无需配置）

### 可选配置
通过环境变量自定义（参考`env.example`）：

```bash
export PORT=8000
export MAX_FILE_SIZE_MB=50
export LLM_API_TIMEOUT=120
```

或创建`.env`文件：
```bash
cp env.example .env
# 编辑配置
```

## 📁 项目结构

```
CodeAgent/
├── app.py              # 主应用程序
├── config.py           # 配置管理
├── requirements.txt    # Python依赖
├── Dockerfile          # Docker配置
├── docker-compose.yml  # Docker编排
├── test_agent.py       # 功能测试
└── README.md           # 本文件
```

## 🔍 端点说明

| 端点 | 方法 | 说明 |
|------|------|------|
| `/` | GET | 服务状态 |
| `/health` | GET | 健康检查 |
| `/analyze` | POST | 代码分析 |
| `/docs` | GET | API文档 |

## 🌍 支持的语言

| 语言 | 代码分析 | 测试执行 |
|------|----------|----------|
| Python | ✅ | ✅ |
| Node.js/TypeScript | ✅ | ✅ |
| Java | ✅ | ⚠️ |
| Go/Rust/C# | ✅ | ❌ |

## 🔧 故障排查

### 端口被占用
```bash
# 使用其他端口
docker run -d -p 8001:8000 code-analysis-agent
```

### 查看详细日志
```bash
docker logs code-analysis-agent
```

### 进入容器调试
```bash
docker exec -it code-analysis-agent /bin/bash
```

## 📝 注意事项

1. ZIP文件默认限制50MB
2. 确保ZIP包含完整项目目录结构
3. 大型项目分析可能需要1-2分钟
4. 测试执行需要网络连接（安装依赖）

## 🎯 使用场景

- 快速理解新项目的代码结构
- 定位特定功能的实现位置
- 生成项目执行指导
- 辅助代码审查和文档编写

## 📖 API文档

启动服务后访问：http://localhost:8000/docs

## 🏗️ 技术栈

- Python 3.10
- FastAPI
- OpenAI SDK
- Docker
- Uvicorn

---

**版本**: 2.1.0 | **许可**: MIT | **更新**: 2025-10-23
