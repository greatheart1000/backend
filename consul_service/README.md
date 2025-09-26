# gRPC 服务发现与消息队列示例

本项目演示了使用 Consul 进行服务发现和 NSQ 作为消息队列的完整示例。

## 项目结构

```
.
├── go.mod                    # Go 模块文件
├── order_service/           # Order 服务（注册到 Consul）
│   └── main.go
├── user_client/             # User 客户端（从 Consul 发现服务）
│   └── main.go
├── nsq/                     # NSQ 消息队列示例
│   ├── producer/            # 消息生产者
│   │   └── main.go
│   └── consumer/            # 消息消费者
│       └── main.go
├── examples/                # 简化示例（不依赖外部服务）
│   ├── simple_service_discovery.go
│   └── message_queue/
│       └── main.go
├── scripts/                 # 启动脚本
│   ├── start_consul.sh
│   ├── start_nsq.sh
│   ├── run_services.sh
│   ├── start_consul.bat
│   └── start_nsq.bat
└── README.md               # 项目说明
```

## 依赖安装

### 1. 安装 Consul

```bash
# Windows (使用 Chocolatey)
choco install consul

# 或者下载二进制文件
# https://www.consul.io/downloads
```

### 2. 安装 NSQ

```bash
# Windows (使用 Chocolatey)
choco install nsq

# 或者下载二进制文件
# https://nsq.io/deployment/installing.html
```

### 3. 安装 Go 依赖

```bash
go mod tidy
```

## 运行步骤

### 1. 启动 Consul

```bash
# 开发模式启动 Consul
consul agent -dev

# 或者使用脚本
./scripts/start_consul.sh
```

Consul UI 访问地址：http://localhost:8500

### 2. 启动 NSQ

```bash
# 启动 nsqlookupd
nsqlookupd

# 新开终端，启动 nsqd
nsqd --lookupd-tcp-address=127.0.0.1:4161

# 或者使用脚本
./scripts/start_nsq.sh
```

NSQ 管理界面：http://localhost:4171

### 3. 运行服务发现示例

```bash
# 终端 1：启动 Order 服务
cd order_service
go run main.go

# 终端 2：运行 User 客户端
cd user_client
go run main.go
```

### 4. 运行 NSQ 消息队列示例

```bash
# 终端 1：启动消费者
cd nsq/consumer
go run main.go

# 终端 2：运行生产者
cd nsq/producer
go run main.go
```

### 5. 运行简化示例（无需外部依赖）

如果不想安装 Consul 和 NSQ，可以运行简化示例：

```bash
# 服务发现简化示例
cd examples
go run simple_service_discovery.go

# 消息队列简化示例
cd examples/message_queue
go run main.go
```

## 功能说明

### 服务发现（Consul）

1. **Order 服务**：
   - 启动 HTTP 服务在端口 8081
   - 提供 `/health`、`/create`、`/list` 接口
   - 自动注册到 Consul
   - 支持优雅关闭和注销

2. **User 客户端**：
   - 从 Consul 查询可用的 Order 服务实例
   - 随机选择实例进行负载均衡
   - 调用 Order 服务的接口

### 消息队列（NSQ）

1. **生产者**：
   - 模拟用户上传图片
   - 发布图片处理消息到 `image_process` topic
   - 消息包含 URL、时间戳、用户ID

2. **消费者**：
   - 订阅 `image_process` topic
   - 处理图片消息（模拟生成缩略图）
   - 支持优雅关闭

## 关键特性

- **服务发现**：自动注册、健康检查、服务发现
- **负载均衡**：随机选择服务实例
- **消息队列**：异步处理、解耦服务
- **优雅关闭**：正确处理信号和资源清理
- **错误处理**：完善的错误处理和日志记录

## 生产环境考虑

1. **安全性**：TLS 加密、ACL 访问控制
2. **监控**：Prometheus 指标、健康检查
3. **高可用**：多实例部署、集群模式
4. **可观测性**：分布式链路追踪、日志聚合
5. **配置管理**：环境变量、配置文件

## 故障排除

1. **Consul 连接失败**：检查 Consul 是否启动，默认地址 127.0.0.1:8500
2. **NSQ 连接失败**：检查 nsqlookupd 和 nsqd 是否启动
3. **端口冲突**：修改代码中的端口配置
4. **依赖问题**：运行 `go mod tidy` 更新依赖
5. **简化示例**：如果不想安装外部依赖，可以直接运行 `examples/` 目录下的简化示例

## 快速开始

### 方法一：完整示例（需要安装 Consul 和 NSQ）

1. 安装依赖：`go mod tidy`
2. 启动 Consul：`consul agent -dev`
3. 启动 NSQ：`nsqlookupd` 和 `nsqd --lookupd-tcp-address=127.0.0.1:4161`
4. 运行服务：参考上面的运行步骤

### 方法二：简化示例（无需外部依赖）

```bash
# 运行服务发现示例
go run examples/simple_service_discovery.go

# 运行消息队列示例
go run examples/message_queue/main.go
``` 