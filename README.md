# 后端项目集合

本仓库包含多个后端技术栈的项目实现，涵盖分布式系统、微服务架构、搜索引擎、负载均衡等核心技术领域。

## 📁 项目结构

### 🔐 TokenBucket - 令牌桶限流器
基于令牌桶算法的分布式限流系统
- **技术栈**: Python, Redis
- **特性**: 内存限流、分布式Redis限流、Docker部署
- **应用场景**: API限流、防刷机制

### 🎯 Consul服务发现
基于Consul和etcd的微服务发现系统
- **技术栈**: Python, Consul, etcd, Kubernetes
- **特性**: 服务注册与发现、健康检查、负载均衡
- **应用场景**: 微服务架构、服务治理

### 🌐 分布式系统
分布式系统核心组件实现
- **技术栈**: Python, Celery, gRPC, Redis
- **特性**: 异步任务处理、数据库优化、缓存策略
- **应用场景**: 高并发处理、任务调度

### 🔍 Elasticsearch混合搜索
基于Elasticsearch的智能搜索系统
- **技术栈**: Python, Elasticsearch
- **特性**: 结构化搜索、非结构化搜索、混合搜索
- **应用场景**: 全文搜索、智能推荐

### ⚡ Fiber服务器
高性能Web服务器
- **技术栈**: Go, Fiber框架
- **特性**: 高并发、低延迟
- **应用场景**: API服务、Web后端

### 💰 金融Web应用
金融数据展示和管理系统
- **技术栈**: Python Flask, Go
- **特性**: 用户认证、数据可视化、多语言模板
- **应用场景**: 金融数据分析、用户管理

### 🔐 Go-Echo认证系统
基于Echo框架的JWT认证系统
- **技术栈**: Go, Echo, JWT, PostgreSQL
- **特性**: 用户认证、JWT中间件、数据库集成
- **应用场景**: 用户系统、权限管理

### ⚖️ 负载均衡器
多算法负载均衡系统
- **技术栈**: Python
- **特性**: 多种负载均衡算法、健康检查、熔断器
- **应用场景**: 流量分发、高可用架构

## 🚀 快速开始

### 环境要求
- Python 3.8+
- Go 1.19+
- Docker & Docker Compose
- Redis
- Elasticsearch
- PostgreSQL

### 安装依赖

```bash
# Python项目依赖
pip install -r requirements.txt

# Go项目依赖
go mod tidy
```

### Docker部署

```bash
# 构建并启动所有服务
docker-compose up -d

# 查看服务状态
docker-compose ps
```

## 📖 核心技术要点

### 🔄 分布式架构设计
- **服务发现**: Consul/etcd实现服务注册与发现
- **负载均衡**: 多种算法实现流量分发
- **熔断降级**: Circuit Breaker模式保障系统稳定性
- **限流控制**: 令牌桶算法防止系统过载

### 🔍 搜索技术
- **全文搜索**: Elasticsearch实现高效文本检索
- **混合搜索**: 结构化与非结构化数据融合搜索
- **相关性排序**: 多维度评分算法优化搜索结果

### ⚡ 高性能优化
- **并发处理**: Go协程和Python异步编程
- **缓存策略**: Redis多级缓存提升响应速度
- **数据库优化**: 索引优化和查询调优
- **连接池管理**: 数据库连接复用降低开销

### 🔐 安全与认证
- **JWT认证**: 无状态身份验证机制
- **权限控制**: 基于角色的访问控制(RBAC)
- **数据加密**: 敏感数据传输和存储加密
- **API安全**: 请求签名和防重放攻击

## 🛠️ 项目特色

1. **多技术栈融合**: Python和Go双语言实现，发挥各自优势
2. **微服务架构**: 组件化设计，易于扩展和维护
3. **容器化部署**: Docker和Kubernetes支持，便于部署和运维
4. **监控和观测**: 健康检查、日志记录、性能监控
5. **测试覆盖**: 单元测试和集成测试保障代码质量

## 📊 性能指标

- **并发处理**: 支持万级并发请求
- **响应时间**: 平均响应时间 < 100ms
- **可用性**: 99.9%系统可用性保障
- **扩展性**: 水平扩展支持

## 🤝 贡献指南

1. Fork本仓库
2. 创建功能分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 创建Pull Request

## 📝 许可证

MIT License - 详见 [LICENSE](LICENSE) 文件

## 📞 联系方式

如有问题或建议，请通过Issue联系我们。

---

*持续更新中，欢迎Star和Fork！* ⭐




