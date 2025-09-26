# TokenBucket 限流服务 CI/CD 配置

## 概述

这个TokenBucket项目现在已经配置了完整的CI/CD流水线，支持以下平台：

- **GitHub Actions** - 适用于GitHub仓库
- **GitLab CI/CD** - 适用于GitLab仓库

## 文件结构

```
TokenBucket/
├── .github/workflows/ci-cd.yml    # GitHub Actions配置
├── .gitlab-ci.yml                 # GitLab CI配置
├── Dockerfile                     # Docker镜像构建
├── docker-compose.yml             # 本地开发环境
├── requirements.txt               # Python依赖
├── tests/                         # 测试文件
│   ├── test_main.py              # API测试
│   ├── test_in_memory.py         # 内存限流测试
│   └── test_redis_bucket.py      # Redis限流测试
└── .dockerignore                  # Docker忽略文件
```

## CI/CD 流水线功能

### 🔄 自动化测试
- **单元测试**: 测试内存和Redis两种限流实现
- **API测试**: 测试FastAPI接口功能
- **限流测试**: 验证限流机制工作正常
- **集成测试**: 测试完整的应用功能

### 🐳 Docker化部署
- **多阶段构建**: 优化镜像大小
- **安全配置**: 非root用户运行
- **健康检查**: 自动监控应用状态
- **Redis支持**: 完整的Redis集成

### 🚀 自动部署
- **分支策略**: main分支自动部署到生产环境
- **环境隔离**: 测试和生产环境分离
- **回滚支持**: 支持快速回滚到之前版本

## 使用方法

### GitHub Actions

1. **设置Secrets**（在GitHub仓库设置中）:
   ```
   DOCKER_USERNAME: your-docker-hub-username
   DOCKER_PASSWORD: your-docker-hub-password
   ```

2. **推送代码**:
   ```bash
   git push origin main
   ```

3. **查看流水线**: 在GitHub的Actions标签页查看执行状态

### GitLab CI/CD

1. **设置Variables**（在GitLab项目设置中）:
   ```
   DEPLOY_SERVER: your-production-server-ip
   DEPLOY_USER: your-ssh-username
   SSH_PRIVATE_KEY: your-ssh-private-key
   ```

2. **推送代码**:
   ```bash
   git push origin main
   ```

3. **查看流水线**: 在GitLab的CI/CD > Pipelines查看执行状态

## 本地开发

### 启动开发环境
```bash
# 使用Docker Compose
docker-compose up -d

# 或直接运行
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### 运行测试
```bash
# 安装依赖
pip install -r requirements.txt

# 运行所有测试
pytest tests/ -v

# 运行特定测试
pytest tests/test_main.py -v
```

### 构建Docker镜像
```bash
docker build -t tokenbucket .
```

## 部署配置

### 环境变量
- `USE_REDIS`: 设置为 "true" 启用Redis限流，"false" 使用内存限流
- `REDIS_HOST`: Redis服务器地址（默认localhost）
- `REDIS_PORT`: Redis端口（默认6379）

### 生产部署示例
```bash
# 使用Docker运行
docker run -d \
  --name tokenbucket \
  -p 8000:8000 \
  -e USE_REDIS=true \
  -e REDIS_HOST=your-redis-host \
  --restart unless-stopped \
  tokenbucket:latest
```

## 监控和日志

### 健康检查
- **端点**: `GET /ping`
- **Docker健康检查**: 自动检测应用状态
- **Kubernetes就绪探针**: 支持K8s部署

### 日志监控
- **应用日志**: uvicorn访问日志
- **限流日志**: 自定义限流事件日志
- **错误追踪**: 详细的错误信息和堆栈跟踪

## 安全考虑

- ✅ 非root用户运行容器
- ✅ 最小化Docker镜像
- ✅ 安全扫描集成（bandit, safety）
- ✅ 依赖漏洞检查
- ✅ 敏感信息使用Secrets管理

## 扩展功能

### 添加新的测试
在 `tests/` 目录下添加新的测试文件，CI/CD会自动执行。

### 修改限流策略
在 `main.py` 中调整 `capacity` 和 `refill_rate` 参数。

### 添加新的接口
新增的FastAPI接口会自动继承限流中间件。

## 故障排除

### 常见问题
1. **Redis连接失败**: 检查Redis服务状态和网络连接
2. **Docker构建失败**: 检查Dockerfile语法和依赖
3. **测试失败**: 检查测试环境和依赖版本
4. **部署失败**: 检查服务器SSH配置和Docker环境

### 调试命令
```bash
# 查看容器日志
docker logs tokenbucket

# 进入容器调试
docker exec -it tokenbucket /bin/bash

# 测试Redis连接
redis-cli -h localhost -p 6379 ping
```

## 贡献指南

1. Fork项目
2. 创建特性分支: `git checkout -b feature/new-feature`
3. 提交更改: `git commit -am 'Add new feature'`
4. 推送分支: `git push origin feature/new-feature`
5. 创建Pull Request

CI/CD会自动运行测试，确保代码质量。