# 微服务发现架构演示

这是一个完整的微服务架构演示项目，展示了两种主流的服务发现实现方案：

## 🏗️ 项目架构

### 1. Consul 服务发现 (`consul_discovery/`)
基于 HashiCorp Consul 的服务发现实现，适用于传统部署环境。

### 2. Kubernetes 服务发现 (`kubernetes_discovery/`)
基于 Etcd 的服务发现实现，适用于 Kubernetes 和云原生环境。

## 📁 目录结构

```
微服务发现项目/
├── consul_discovery/          # Consul 服务发现实现
│   ├── services/             # 微服务
│   ├── client/              # 客户端示例
│   ├── scripts/             # 启动脚本
│   └── README.md            # Consul 方案说明
├── kubernetes_discovery/     # Kubernetes(Etcd) 服务发现实现
│   ├── services/            # 微服务
│   ├── client/             # 客户端示例
│   ├── scripts/            # 启动脚本
│   ├── docs/               # 详细文档
│   └── README.md           # Kubernetes 方案说明
└── README.md               # 项目总览(本文件)
```

## 🚀 快速开始

### 选择服务发现方案

#### 1. Consul 服务发现
适用于传统部署环境，学习成本低，功能丰富。

```bash
cd consul_discovery
# 查看详细说明
cat README.md
```

#### 2. Kubernetes(Etcd) 服务发现
适用于 Kubernetes 和云原生环境，高性能，强一致性。

```bash
cd kubernetes_discovery
# 查看详细说明
cat README.md
```

## 📊 方案对比

| 特性 | **Consul** | **Kubernetes(Etcd)** |
|------|------------|----------------------|
| **一致性模型** | 强一致性 (CP) | 强一致性 (CP) |
| **性能** | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| **K8s集成** | 🔶 第三方 | ✅ 原生 |
| **故障检测** | 多种方式 | 租约TTL |
| **实时监听** | ✅ Watch | ✅ Watch |
| **学习成本** | 低 | 中等 |
| **适用场景** | 传统部署 | 云原生/K8s |

## 🛠️ 核心特性

### 通用特性
- ✅ 自动服务注册/注销
- ✅ 健康检查机制
- ✅ 服务发现和负载均衡
- ✅ 故障自动恢复
- ✅ 微服务间通信
- ✅ JWT 认证集成

## 🗺️ 架构说明

### Consul 架构
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   User Service  │    │  Order Service  │    │     Client      │
│   (Port 5001)   │    │   (Port 5002)   │    │   Application   │
└─────────┬───────┐    └─────────┬───────┐    └─────────┬───────┐
          │                      │                      │
          │ 注册服务              │ 注册服务              │ 发现服务
          └──────────┬───────────┴───────────────────┘
                     │
             ┌───────┴────────┐
             │     Consul     │
             │   (Port 8500)  │
             └────────────────┘
```

### Kubernetes(Etcd) 架构
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   User Service  │    │  Order Service  │    │     Client      │
│   (Port 5001)   │    │   (Port 5002)   │    │   Application   │
└─────────┬───────┐    └─────────┬───────┐    └─────────┬───────┐
          │                      │                      │
          │ 租约注册              │ 租约注册              │ 发现服务
          └──────────┬───────────┴───────────────────┘
                     │
             ┌───────┴────────┐
             │      Etcd      │
             │   (Port 2379)  │
             │                │
             │ 租约 + 监听机制 │
             └────────────────┘
```

## 💻 技术栈

### Consul 方案
- **服务发现**: Consul
- **Web 框架**: Flask
- **认证**: JWT (PyJWT)
- **密码加密**: bcrypt
- **HTTP 客户端**: requests
- **配置管理**: python-dotenv

### Kubernetes 方案
- **服务发现**: Etcd
- **Web 框架**: Flask
- **认证**: JWT (PyJWT)
- **密码加密**: bcrypt
- **HTTP 客户端**: requests
- **Etcd 客户端**: etcd3

## 🚀 项目亮点

1. **完整的微服务架构**: 包含用户服务、订单服务和客户端示例
2. **两种服务发现方案**: Consul 和 Kubernetes(Etcd) 对比实现
3. **生产级特性**: JWT 认证、密码加密、健康检查
4. **自动化脚本**: 一键启动所有服务
5. **详细文档**: 包含完整的使用说明和架构介绍

## 📋 学习路径

1. **初学者**: 先学习 `consul_discovery/` 中的 Consul 方案
2. **进阶者**: 学习 `kubernetes_discovery/` 中的 Etcd 方案
3. **面试准备**: 理解两种方案的优缺点和适用场景

## 📄 许可证

MIT License

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！格**

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