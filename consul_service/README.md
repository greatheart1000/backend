# Flask Consul 服务发现演示

这是一个基于 Flask 和 Consul 的微服务架构演示项目，展示了服务注册、发现和调用的完整流程。

## 项目结构

```
consul_service/
├── requirements.txt          # Python 依赖
├── .env                     # 环境配置
├── config.py                # 配置文件
├── consul_service.py        # Consul 服务工具类
├── user_service/            # 用户服务
│   └── main.py             # 用户服务主程序
├── order_service/           # 订单服务
│   └── main.py             # 订单服务主程序
├── client_example/          # 客户端示例
│   └── main.py             # 服务发现调用示例
├── scripts/                 # 启动脚本
│   ├── start_consul.sh     # 启动 Consul (Linux/macOS)
│   ├── start_consul.bat    # 启动 Consul (Windows)
│   ├── run_services.sh     # 启动所有服务 (Linux/macOS)
│   └── run_services.bat    # 启动所有服务 (Windows)
└── README.md               # 项目说明
```

## 功能特性

### 🔐 用户服务 (user-service)
- **端口**: 5001
- **功能**:
  - 用户注册 (`POST /api/users/register`)
  - 用户登录 (`POST /api/users/login`)
  - 获取用户信息 (`GET /api/users/profile`)
  - 获取用户列表 (`GET /api/users`)
- **认证**: JWT Token
- **密码加密**: bcrypt

### 📦 订单服务 (order-service)
- **端口**: 5002
- **功能**:
  - 创建订单 (`POST /api/orders`)
  - 获取订单列表 (`GET /api/orders`)
  - 获取订单详情 (`GET /api/orders/<order_id>`)
  - 更新订单状态 (`PUT /api/orders/<order_id>/status`)
  - 获取订单统计 (`GET /api/orders/stats`)
- **认证**: 通过用户服务验证 JWT Token
- **服务依赖**: 依赖用户服务进行身份验证

### 🎯 Consul 服务发现
- **服务注册**: 自动注册到 Consul
- **健康检查**: 定期健康检查
- **服务发现**: 动态发现可用服务
- **负载均衡**: 简单轮询算法
- **故障恢复**: 自动注销不健康服务

## 快速开始

### 1. 安装依赖

确保你已安装以下软件：
- Python 3.7+
- Consul 1.15+

### 2. 安装 Consul

#### Linux/macOS:
```bash
# 下载并安装 Consul
wget https://releases.hashicorp.com/consul/1.15.2/consul_1.15.2_linux_amd64.zip
unzip consul_1.15.2_linux_amd64.zip
sudo mv consul /usr/local/bin/
```

#### Windows:
1. 访问 [Consul 下载页面](https://www.consul.io/downloads)
2. 下载适用于 Windows 的版本
3. 解压并将 `consul.exe` 添加到系统 PATH

### 3. 安装 Python 依赖

```bash
pip install -r requirements.txt
```

### 4. 启动服务

#### 方法一：使用启动脚本 (推荐)

**Linux/macOS:**
```bash
# 启动 Consul
./scripts/start_consul.sh

# 新开终端，启动所有 Flask 服务
./scripts/run_services.sh
```

**Windows:**
```cmd
REM 启动 Consul
scripts\start_consul.bat

REM 新开命令行，启动所有 Flask 服务
scripts\run_services.bat
```

#### 方法二：手动启动

```bash
# 1. 启动 Consul
consul agent -dev -ui

# 2. 启动用户服务
cd user_service
python main.py

# 3. 启动订单服务 (新终端)
cd order_service
python main.py
```

### 5. 运行客户端示例

```bash
cd client_example
python main.py
```

## API 使用示例

### 用户注册
```bash
curl -X POST http://localhost:5001/api/users/register \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "password": "testpass123",
    "email": "test@example.com"
  }'
```

### 用户登录
```bash
curl -X POST http://localhost:5001/api/users/login \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "password": "testpass123"
  }'
```

### 创建订单
```bash
# 先登录获取 token，然后：
curl -X POST http://localhost:5002/api/orders \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -d '{
    "product_name": "测试产品",
    "quantity": 2,
    "price": 99.99
  }'
```

### 获取订单列表
```bash
curl -X GET http://localhost:5002/api/orders \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

## 服务地址

启动后，各服务地址如下：

- **Consul UI**: http://localhost:8500
- **用户服务**: http://localhost:5001
- **订单服务**: http://localhost:5002

### 健康检查端点

- **用户服务健康检查**: http://localhost:5001/health
- **订单服务健康检查**: http://localhost:5002/health

## 架构说明

### 服务注册流程
1. 服务启动时自动注册到 Consul
2. 提供健康检查端点
3. Consul 定期检查服务健康状态
4. 服务退出时自动注销

### 服务发现流程
1. 客户端通过 Consul API 查询可用服务
2. 获取健康服务实例列表
3. 使用负载均衡算法选择服务实例
4. 发起 HTTP 请求到选中的服务

### 微服务通信
- 订单服务通过服务发现调用用户服务
- 使用 JWT Token 进行服务间认证
- 自动处理服务故障和重试

## 技术栈

- **Web 框架**: Flask
- **服务发现**: Consul
- **认证**: JWT (PyJWT)
- **密码加密**: bcrypt
- **HTTP 客户端**: requests
- **配置管理**: python-dotenv

## 配置说明

### 环境变量 (.env)
```
SECRET_KEY=your-secret-key-change-this-in-production
CONSUL_HOST=localhost
CONSUL_PORT=8500
JWT_SECRET_KEY=jwt-secret-key-change-this-in-production
```

### 生产环境建议
1. 更改默认密钥
2. 使用真实数据库替代内存存储
3. 添加日志聚合和监控
4. 配置 HTTPS
5. 设置适当的错误处理和重试机制

## 故障排除

### 常见问题

1. **Consul 连接失败**
   - 确保 Consul 已启动并运行在 localhost:8500
   - 检查防火墙设置

2. **服务注册失败**
   - 检查服务端口是否被占用
   - 确认网络配置正确

3. **服务发现失败**
   - 确保服务已成功注册到 Consul
   - 检查服务健康状态

4. **JWT Token 错误**
   - 确认 token 格式正确
   - 检查 token 是否过期

### 日志查看

所有服务都会输出详细的日志信息，包括：
- 服务注册状态
- API 调用记录
- 错误信息和堆栈跟踪

## 扩展功能

### 可扩展的特性
1. **添加更多微服务**
2. **实现熔断器模式**
3. **添加分布式链路追踪**
4. **集成消息队列**
5. **添加配置中心**
6. **实现服务网格**

### 生产环境增强
1. **数据库集成** (PostgreSQL/MySQL)
2. **缓存支持** (Redis)
3. **监控和告警** (Prometheus + Grafana)
4. **日志聚合** (ELK Stack)
5. **API 网关** (Kong/Zuul)

## 许可证

MIT License

## 贡献

欢迎提交 Issue 和 Pull Request！