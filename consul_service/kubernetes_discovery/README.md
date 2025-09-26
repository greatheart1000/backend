# Kubernetes (Etcd) 服务发现实现

这个目录包含基于 Etcd 的微服务发现实现，适用于 Kubernetes 环境。

## 目录结构

```
kubernetes_discovery/
├── etcd_service.py            # Etcd 服务发现核心库
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
│   ├── start_etcd.sh         # 启动 Etcd
│   ├── start_etcd.bat        # 启动 Etcd (Windows)
│   └── run_etcd_services.sh  # 启动所有服务
└── docs/                     # 文档目录
```

## 快速开始

### 1. 安装依赖

```bash
cd kubernetes_discovery
pip install -r requirements.txt
```

### 2. 启动 Etcd

**Linux/macOS:**
```bash
./scripts/start_etcd.sh
```

**Windows:**
```cmd
scripts\start_etcd.bat
```

### 3. 启动微服务

```bash
./scripts/run_etcd_services.sh
```

### 4. 运行客户端示例

```bash
cd client
python main.py
```

## 服务地址

- **Etcd API**: http://localhost:2379
- **用户服务**: http://localhost:5001
- **订单服务**: http://localhost:5002

## 核心特性

- ✅ 强一致性保证 (Raft 协议)
- ✅ 租约机制自动故障检测
- ✅ 实时监听服务变化 (Watch)
- ✅ Kubernetes 原生支持
- ✅ 高性能低延迟
- ✅ 分布式事务支持

## 技术栈

- **服务发现**: Etcd
- **Web 框架**: Flask  
- **认证**: JWT
- **密码加密**: bcrypt
- **HTTP 客户端**: requests
- **Etcd 客户端**: etcd3

## Etcd vs Consul

| 特性 | Etcd | Consul |
|------|------|--------|
| **一致性** | 强一致性 (Raft) | 强一致性 (Raft) |
| **性能** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ |
| **K8s集成** | ✅ 原生 | 🔶 第三方 |
| **故障检测** | 租约TTL | 多种方式 |
| **实时监听** | ✅ Watch | ✅ Watch |
| **学习成本** | 中等 | 低 |

## 监控命令

```bash
# 查看集群状态
etcdctl endpoint status --write-out=table

# 查看服务注册信息
etcdctl get --prefix "/services/"

# 查看健康状态
curl http://localhost:2379/health
```