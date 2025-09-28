# Flask 负载均衡器

一个基于Flask框架实现的完整负载均衡系统，支持多种负载均衡算法、服务发现、健康检查、会话保持、熔断器和限流器等企业级功能。

## 功能特性

### 🎯 负载均衡算法
- **轮询 (Round Robin)** - 请求依次分发到各个后端
- **加权轮询 (Weighted Round Robin)** - 根据权重分发请求
- **IP哈希 (IP Hash)** - 基于客户端IP的一致性哈希
- **最少连接 (Least Connections)** - 选择当前连接数最少的后端
- **一致性哈希 (Consistent Hash)** - 适用于缓存场景的一致性哈希
- **最快响应 (Fastest Response)** - 基于响应时间的智能选择

### 🏗️ 架构支持
- **四层负载均衡** - TCP/UDP代理转发
- **七层负载均衡** - HTTP反向代理
- **客户端负载均衡** - SDK形式的客户端负载均衡库

### 🔍 服务发现与健康检查
- 动态服务注册和发现
- HTTP/TCP健康检查
- 自动故障转移
- 服务状态监控

### 🛡️ 高可用功能
- **会话保持** - 基于Cookie/Header的会话亲和性
- **熔断器** - 防止系统雪崩的熔断机制
- **限流器** - 令牌桶、滑动窗口、漏桶等多种限流算法
- **故障隔离** - 自动隔离不健康的后端服务

### 📊 监控与管理
- 实时统计信息
- 性能指标监控
- RESTful管理API
- 健康检查端点

## 项目结构

```
flask_loadbalancer/
├── algorithms/          # 负载均衡算法
│   ├── base.py         # 基础类和接口
│   ├── round_robin.py  # 轮询算法
│   ├── weighted_round_robin.py  # 加权轮询
│   ├── ip_hash.py      # IP哈希
│   ├── least_connections.py    # 最少连接
│   ├── consistent_hash.py      # 一致性哈希
│   └── fastest_response.py     # 最快响应
├── balancer/           # 负载均衡器实现
│   ├── http_proxy.py   # HTTP反向代理
│   └── tcp_proxy.py    # TCP代理
├── discovery/          # 服务发现
│   ├── registry.py     # 服务注册表
│   ├── health.py       # 健康检查
│   └── watcher.py      # 服务监控
├── middleware/         # 中间件
│   ├── session.py      # 会话管理
│   ├── circuit_breaker.py  # 熔断器
│   └── rate_limiter.py     # 限流器
├── app/               # 主应用
│   └── main.py        # Flask应用入口
├── examples/          # 示例代码
│   ├── backend_server.py   # 示例后端服务器
│   └── start_backends.py   # 后端服务器管理器
├── scripts/           # 启动脚本
│   ├── start_loadbalancer.sh  # 启动负载均衡器
│   └── start_backends.sh      # 启动后端服务器
├── tests/             # 测试代码
│   └── test_loadbalancer.py   # 负载均衡器测试
├── config/            # 配置文件
├── requirements.txt   # Python依赖
└── README.md         # 项目说明
```

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 启动后端服务器

```bash
# 使用脚本启动多个后端服务器
chmod +x scripts/start_backends.sh
./scripts/start_backends.sh --ports "8001 8002 8003"

# 或者手动启动单个服务器
python examples/backend_server.py --port 8001 --id backend1
```

### 3. 启动负载均衡器

```bash
# 使用脚本启动
chmod +x scripts/start_loadbalancer.sh
./scripts/start_loadbalancer.sh --host 0.0.0.0 --port 8080 --algorithm round_robin

# 或者直接运行Python程序
python app/main.py --host 0.0.0.0 --port 8080 --algorithm round_robin
```

### 4. 测试负载均衡器

```bash
# 基本测试
curl http://localhost:8080/

# 运行完整测试套件
python tests/test_loadbalancer.py --url http://localhost:8080 --requests 100
```

## 配置选项

### 负载均衡算法

支持以下算法：
- `round_robin` - 轮询算法（默认）
- `weighted_round_robin` - 加权轮询
- `ip_hash` - IP哈希
- `least_connections` - 最少连接

### 启动参数

**负载均衡器参数：**
```bash
python app/main.py [OPTIONS]
  --host HOST           # 绑定主机 (默认: 0.0.0.0)
  --port PORT           # 绑定端口 (默认: 8080)
  --algorithm ALGO      # 负载均衡算法 (默认: round_robin)
  --debug               # 启用调试模式
```

**后端服务器参数：**
```bash
python examples/backend_server.py [OPTIONS]
  --port PORT           # 服务端口 (必需)
  --id ID               # 服务器ID
  --host HOST           # 绑定主机 (默认: 127.0.0.1)
```

## API 端点

### 负载均衡器管理

| 端点 | 方法 | 描述 |
|------|------|------|
| `/lb/health` | GET | 健康检查 |
| `/lb/stats` | GET | 统计信息 |
| `/lb/backends` | GET | 后端服务器列表 |
| `/lb/config` | GET | 配置信息 |
| `/lb/backends/add` | POST | 添加后端服务器 |
| `/lb/backends/{id}/remove` | DELETE | 移除后端服务器 |
| `/lb/backends/{id}/enable` | POST | 启用后端服务器 |
| `/lb/backends/{id}/disable` | POST | 禁用后端服务器 |

### 示例API调用

```bash
# 获取统计信息
curl http://localhost:8080/lb/stats

# 添加后端服务器
curl -X POST http://localhost:8080/lb/backends/add \
  -H "Content-Type: application/json" \
  -d '{"host": "localhost", "port": 8004, "weight": 1}'

# 禁用后端服务器
curl -X POST http://localhost:8080/lb/backends/backend1/disable
```

## 高级功能

### 1. 会话保持

支持基于Cookie和Header的会话保持：

```python
# 路由配置中启用会话保持
route = RouteConfig(
    service_name='web-service',
    enable_session_affinity=True
)
```

### 2. 熔断器

自动检测故障并进行熔断保护：

```python
# 熔断器配置
circuit_breaker = CircuitBreaker(
    failure_threshold=5,    # 失败阈值
    success_threshold=3,    # 成功阈值
    timeout=60             # 超时时间（秒）
)
```

### 3. 限流器

支持多种限流算法：

```python
# 令牌桶限流器
token_bucket = TokenBucketRateLimiter(capacity=100, refill_rate=10.0)

# 滑动窗口限流器
sliding_window = SlidingWindowRateLimiter(max_requests=50, window_size=60)

# 漏桶限流器
leaky_bucket = LeakyBucketRateLimiter(capacity=100, leak_rate=5.0)
```

### 4. 服务发现

动态注册和发现服务：

```python
# 注册服务
registry.register_service(
    service_name='web-service',
    service_id='backend1',
    address='localhost',
    port=8001,
    health_check_url='http://localhost:8001/health'
)
```

## 性能测试

使用内置的测试工具进行性能测试：

```bash
# 运行性能测试
python tests/test_loadbalancer.py \
  --url http://localhost:8080 \
  --requests 1000 \
  --concurrency 50 \
  --output results.json
```

## 监控指标

系统提供以下监控指标：

- **请求统计**: 总请求数、成功/失败请求数、成功率
- **响应时间**: 平均响应时间、分位数统计
- **后端状态**: 后端服务器健康状态、连接数
- **熔断器状态**: 熔断器状态、失败率
- **限流统计**: 限流次数、通过率

## 故障排除

### 常见问题

1. **连接被拒绝**
   - 检查后端服务器是否启动
   - 确认端口配置正确

2. **请求分布不均**
   - 检查负载均衡算法配置
   - 确认权重设置

3. **会话保持不工作**
   - 检查Cookie设置
   - 确认路由配置

### 日志配置

调整日志级别获取更多信息：

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## 贡献指南

1. Fork 项目
2. 创建特性分支 (`git checkout -b feature/amazing-feature`)
3. 提交更改 (`git commit -m 'Add amazing feature'`)
4. 推送到分支 (`git push origin feature/amazing-feature`)
5. 创建 Pull Request

## 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。

## 支持

如有问题或建议，请提交 Issue 或联系维护者。

---

**注意**: 这是一个教学/演示项目，在生产环境使用前请进行充分的测试和优化。