# Consul 服务发现实现

这个目录包含基于 Consul 的微服务发现实现。

## 目录结构

```
consul_discovery/
├── consul_service.py          # Consul 服务发现核心库
├── config.py                  # 配置文件
├── requirements.txt           # Python 依赖
├── services/                  # 微服务目录
│   ├── user_service/         # 用户服务
│   │   └── main.py
│   └── order_service/        # 订单服务
│       └── main.py
├── client/                   # 客户端示例
│   └── main.py
├── scripts/                  # 启动脚本
│   ├── start_consul.sh       # 启动 Consul
│   ├── start_consul.bat      # 启动 Consul (Windows)
│   ├── run_services.sh       # 启动所有服务
│   └── run_services.bat      # 启动所有服务 (Windows)
└── docs/                     # 文档目录
```

## 快速开始

### 1. 安装依赖

```bash
cd consul_discovery
pip install -r requirements.txt
```

### 2. 启动 Consul

**Linux/macOS:**
```bash
./scripts/start_consul.sh
```

**Windows:**
```cmd
scripts\start_consul.bat
```

### 3. 启动微服务

**Linux/macOS:**
```bash
./scripts/run_services.sh
```

**Windows:**
```cmd
scripts\run_services.bat
```

### 4. 运行客户端示例

```bash
cd client
python main.py
```

## 服务地址

- **Consul UI**: http://localhost:8500
- **用户服务**: http://localhost:5001
- **订单服务**: http://localhost:5002

## 核心特性

- ✅ 自动服务注册/注销
- ✅ 健康检查机制  
- ✅ 服务发现和负载均衡
- ✅ 故障自动恢复
- ✅ 微服务间通信
- ✅ JWT 认证集成

## 技术栈

- **服务发现**: Consul
- **Web 框架**: Flask
- **认证**: JWT
- **密码加密**: bcrypt
- **HTTP 客户端**: requests