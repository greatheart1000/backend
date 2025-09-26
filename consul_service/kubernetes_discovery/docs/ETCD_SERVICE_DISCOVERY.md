# Etcd 服务发现实现指南

## 什么是 Etcd？

Etcd 是一个分布式可靠的键值存储，主要用于分布式系统的配置管理和服务发现。它是 Kubernetes 的核心组件，提供了强一致性保证。

## Etcd vs 其他服务发现方案

| 特性 | Etcd | Consul | Eureka | Zookeeper |
|------|------|--------|--------|-----------|
| **一致性** | 强一致性 (Raft) | 强一致性 (Raft) | AP模型 | 强一致性 (ZAB) |
| **性能** | 高性能 | 中等 | 高性能 | 中等 |
| **Kubernetes集成** | ✅ 原生 | 🔶 第三方 | 🔶 第三方 | 🔶 第三方 |
| **健康检查** | 租约TTL | 多种方式 | 心跳 | 会话 |
| **监听机制** | ✅ Watch | ✅ Watch | ❌ 无 | ✅ Watch |
| **多数据中心** | ✅ 支持 | ✅ 支持 | ❌ 无 | 🔶 复杂 |
| **学习成本** | 中等 | 低 | 低 | 高 |

## Etcd 服务发现核心概念

### 1. 键值存储结构
```
/services/
├── user-service/
│   ├── user-service-001
│   └── user-service-002
└── order-service/
    └── order-service-001
```

### 2. 租约机制 (Lease)
- **TTL (Time To Live)**: 服务注册时创建租约，设置过期时间
- **续约 (Renew)**: 服务定期刷新租约，保持活跃状态
- **自动清理**: 租约过期时，Etcd 自动删除相关键值

### 3. 监听机制 (Watch)
- **实时通知**: 监听键前缀变化，实时获取服务上下线事件
- **事件类型**: PUT（服务注册/更新）、DELETE（服务下线）

## 核心实现

### 1. 服务注册

```python
def register_service(self, service_name: str, service_id: str, address: str, 
                    port: int, metadata: Dict = None, tags: List[str] = None) -> bool:
    # 1. 创建租约 (TTL=30秒)
    lease = self.etcd.lease(self.lease_ttl)
    
    # 2. 构建服务信息
    service_info = {
        'service_id': service_id,
        'service_name': service_name,
        'address': address,
        'port': port,
        'tags': tags or [],
        'metadata': metadata or {},
        'registered_at': time.time()
    }
    
    # 3. 注册到 Etcd (绑定租约)
    service_key = f"/services/{service_name}/{service_id}"
    self.etcd.put(service_key, json.dumps(service_info), lease=lease)
    
    # 4. 启动续约线程
    self._start_lease_renewal(service_id, lease)
```

### 2. 服务发现

```python
def discover_service(self, service_name: str) -> List[Dict]:
    # 1. 查询服务前缀
    service_prefix = f"/services/{service_name}/"
    
    # 2. 获取所有实例
    services = []
    for value, metadata in self.etcd.get_prefix(service_prefix):
        service_info = json.loads(value.decode('utf-8'))
        
        # 3. 健康检查
        if self._is_service_healthy(service_info):
            services.append(service_info)
    
    return services
```

### 3. 租约续约

```python
def _start_lease_renewal(self, service_id: str, lease):
    def renewal_thread():
        while service_id in self.registered_services:
            # 每隔 TTL/3 时间续约一次
            time.sleep(self.lease_ttl // 3)
            
            if service_id in self.registered_services:
                lease.refresh()  # 续约
    
    # 后台线程执行
    thread = threading.Thread(target=renewal_thread, daemon=True)
    thread.start()
```

### 4. 服务监听

```python
def watch_service(self, service_name: str, callback):
    def watch_thread():
        service_prefix = f"/services/{service_name}/"
        events_iterator, cancel = self.etcd.watch_prefix(service_prefix)
        
        for event in events_iterator:
            if event.type == etcd3.events.PutEvent:
                # 服务注册/更新
                callback(event, service_name)
            elif event.type == etcd3.events.DeleteEvent:
                # 服务下线
                callback(event, service_name)
    
    thread = threading.Thread(target=watch_thread, daemon=True)
    thread.start()
```

## 项目架构

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│  User Service   │    │  Order Service  │    │     Client      │
│   (Port 5001)   │    │   (Port 5002)   │    │   Application   │
│                 │    │                 │    │                 │
│ ┌─────────────┐ │    │ ┌─────────────┐ │    │ ┌─────────────┐ │
│ │ Etcd Client │ │    │ │ Etcd Client │ │    │ │ Etcd Client │ │
│ └─────────────┘ │    │ └─────────────┘ │    │ └─────────────┘ │
└─────────┬───────┘    └─────────┬───────┘    └─────────┬───────┘
          │                      │                      │
          │ 注册/发现服务          │ 注册/发现服务          │ 发现服务
          └──────────┬───────────┴──────────────────────┘
                     │
             ┌───────▼────────┐
             │      Etcd      │
             │   (Port 2379)  │
             │                │
             │ 租约 + 监听机制 │
             └────────────────┘
```

## 关键优势

### 1. 强一致性
- 基于 Raft 协议，保证数据强一致性
- 避免脑裂问题，确保服务发现的准确性

### 2. 高性能
- 优化的存储引擎，读写性能优越
- 支持大量并发连接

### 3. Kubernetes 原生支持
- Kubernetes 官方服务发现机制
- 与容器编排平台无缝集成

### 4. 租约机制
- 自动故障检测，无需额外健康检查
- 服务异常时自动清理注册信息

### 5. 实时监听
- Watch 机制提供实时事件通知
- 服务拓扑变化立即响应

## 快速开始

### 1. 安装 Etcd

**Linux/macOS:**
```bash
# 下载安装
ETCD_VER=v3.5.9
curl -L https://github.com/etcd-io/etcd/releases/download/${ETCD_VER}/etcd-${ETCD_VER}-linux-amd64.tar.gz -o etcd.tar.gz
tar xzf etcd.tar.gz
sudo mv etcd-${ETCD_VER}-linux-amd64/etcd* /usr/local/bin/
```

**Ubuntu/Debian:**
```bash
sudo apt-get install etcd
```

**macOS:**
```bash
brew install etcd
```

### 2. 启动 Etcd

```bash
# 开发模式启动
./scripts/start_etcd.sh
```

### 3. 启动微服务

```bash
# 安装依赖
pip install -r requirements.txt

# 启动所有服务
./scripts/run_etcd_services.sh
```

### 4. 测试服务发现

```bash
# 运行客户端示例
cd client_etcd_example
python main.py
```

## 生产环境配置

### 1. Etcd 集群部署

```bash
# 节点1
etcd --name node1 \
  --initial-advertise-peer-urls http://10.0.1.10:2380 \
  --listen-peer-urls http://10.0.1.10:2380 \
  --advertise-client-urls http://10.0.1.10:2379 \
  --listen-client-urls http://10.0.1.10:2379 \
  --initial-cluster node1=http://10.0.1.10:2380,node2=http://10.0.1.11:2380,node3=http://10.0.1.12:2380

# 节点2、3 类似配置...
```

### 2. 安全配置

```python
# TLS 加密
etcd_service = EtcdService(
    host='etcd-cluster.example.com',
    port=2379,
    ca_cert='/path/to/ca.crt',
    cert_cert='/path/to/client.crt',
    cert_key='/path/to/client.key'
)
```

### 3. 性能调优

```python
# 连接池配置
etcd_service = EtcdService(
    host='localhost',
    port=2379,
    timeout=10,
    grpc_options=[
        ('grpc.keepalive_time_ms', 30000),
        ('grpc.keepalive_timeout_ms', 5000),
    ]
)
```

## 监控和运维

### 1. Etcd 监控指标

```bash
# 查看集群状态
etcdctl endpoint status --write-out=table

# 查看集群健康状态
etcdctl endpoint health

# 查看性能指标
curl http://localhost:2379/metrics
```

### 2. 常用运维命令

```bash
# 查看所有键
etcdctl get --prefix ""

# 查看服务注册信息
etcdctl get --prefix "/services/"

# 删除过期服务
etcdctl del --prefix "/services/offline-service/"

# 备份数据
etcdctl snapshot save backup.db
```

## 故障排除

### 1. 常见问题

**连接失败:**
```bash
# 检查 Etcd 状态
systemctl status etcd
curl http://localhost:2379/health
```

**租约过期:**
```python
# 调整租约TTL
self.lease_ttl = 60  # 增加到60秒
```

**性能问题:**
```python
# 启用连接池
import grpc
channel = grpc.insecure_channel('localhost:2379')
```

### 2. 日志分析

```bash
# Etcd 日志
journalctl -u etcd -f

# 应用日志
tail -f app.log | grep "etcd"
```

## 最佳实践

1. **合理设置租约TTL**: 通常 30-60 秒
2. **实现优雅关闭**: 服务停止时主动注销
3. **健康检查**: 结合应用层健康检查
4. **监控告警**: 监控 Etcd 集群状态
5. **数据备份**: 定期备份 Etcd 数据
6. **安全配置**: 生产环境启用 TLS

这套基于 Etcd 的服务发现方案提供了企业级的可靠性和性能，特别适合 Kubernetes 环境和对一致性要求较高的场景。