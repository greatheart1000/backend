# Token Bucket 限流器

## 项目简介

令牌桶是一种常见的限流算法，用于控制请求或数据包的速率。它通过一个"桶"来存储令牌，每个令牌代表处理一个单位的数据或请求的权利。系统以固定的速率向桶中添加令牌，而当请求到来时需要消耗相应数量的令牌。

本项目提供了两种令牌桶的实现方式：**内存版本** 和 **Redis版本**，适用于不同的部署场景。

## 两种实现方法

### 1. In-Memory 实现（内存版本）

**文件位置**: `limiter/in_memory.py`

**核心特点**:
- 基于Python内存的单机限流方案
- 使用线程锁保证线程安全
- 全局缓存桶实例，避免重复创建

**主要组件**:
```python
class TokenBucket:
    def __init__(self, capacity: int, refill_rate: float)
    def allow(self, tokens: int = 1) -> bool
    def _refill(self)  # 根据时间差补充令牌

def get_bucket(key: str, capacity: int = 10, refill_rate: float = 1.0) -> TokenBucket
```

**工作原理**:
1. 每次请求时先调用 `_refill()` 根据时间差补充令牌
2. 检查当前令牌数是否足够
3. 足够则扣除令牌并允许请求，否则拒绝

**优势**:
- ✅ 性能极高，纯内存操作
- ✅ 无外部依赖
- ✅ 线程安全
- ✅ 实现简单

**劣势**:
- ❌ 仅支持单机部署
- ❌ 进程重启后状态丢失
- ❌ 无法在分布式环境中共享限流状态

### 2. Redis Bucket 实现（Redis版本）

**文件位置**: `limiter/redis_bucket.py`

**核心特点**:
- 基于Redis的分布式限流方案
- 使用Lua脚本保证原子性操作
- 支持多服务实例共享限流状态

**主要组件**:
```python
def allow_user(user_id: str, capacity: int = 10, refill_rate: float = 1.0, requested: int = 1) -> bool
```

**核心Lua脚本**:
- 原子性地完成：获取状态 → 计算令牌 → 判断并扣除 → 更新状态
- 自动设置过期时间，避免垃圾数据累积

**工作原理**:
1. 构造Redis键名：`tb:{user_id}`
2. 调用Lua脚本执行原子操作
3. 脚本内部完成令牌计算和状态更新
4. 设置过期时间避免垃圾数据

**优势**:
- ✅ 支持分布式部署
- ✅ 数据持久化
- ✅ 高可用性
- ✅ 原子性操作保证数据一致性
- ✅ 自动清理过期数据

**劣势**:
- ❌ 依赖Redis服务
- ❌ 网络延迟影响性能
- ❌ 增加了系统复杂度

## 使用方式

### 环境配置

通过环境变量 `USE_REDIS` 控制使用哪种实现：

```bash
# 使用内存版本（默认）
export USE_REDIS=false

# 使用Redis版本
export USE_REDIS=true
```

### 启动应用

```bash
# 启动FastAPI应用
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### 测试接口

```bash
# 基本测试
curl http://localhost:8000/ping
curl http://localhost:8000/hello

# 带用户ID的测试
curl -H "x-user-id: user123" http://localhost:8000/hello

# 压力测试（快速发送多个请求测试限流）
for i in {1..15}; do curl http://localhost:8000/hello; echo; done
```

## 参数配置

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `capacity` | 桶容量（最大令牌数） | 10 |
| `refill_rate` | 每秒补充的令牌数 | 2.0 |
| `requested` | 每次请求消耗的令牌数 | 1 |

## 选择建议

### 使用内存版本的场景：
- 单机部署的应用
- 对性能要求极高
- 简单的限流需求
- 不需要数据持久化

### 使用Redis版本的场景：
- 微服务或分布式架构
- 多实例部署需要共享限流状态
- 需要数据持久化
- 对一致性要求较高

## 错误处理

- **内存版本**: 线程安全，异常时可能影响单个实例
- **Redis版本**: 实现了 fail-open 策略，Redis连接失败时允许请求通过（可根据业务需求改为 fail-close）

## 测试

```bash
# 运行所有测试
pytest tests/

# 运行特定测试
pytest tests/test_in_memory.py
pytest tests/test_redis_bucket.py

# 运行集成测试（需要Redis）
pytest tests/test_redis_bucket.py::test_redis_integration
```

## Docker 部署

```bash
# 构建镜像
docker-compose build

# 启动服务（包含Redis）
docker-compose up -d
```

## WSL 2 网络配置

在 WSL 2 中，要从 Windows 主机访问服务，可以使用以下命令找到宿主机IP：

```bash
ip route show | grep -i default | awk '{ print $3 }'

# 示例访问
curl http://172.27.152.1:8000/hello





