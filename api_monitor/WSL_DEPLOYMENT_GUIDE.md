# WSL环境下的登录监控系统部署指南

## 🐧 WSL环境特别说明

本项目已针对WSL（Windows Subsystem for Linux）环境进行了专门优化，提供了完整的部署脚本和测试工具。

## 🚀 快速开始

### 1. 环境准备

```bash
# 1. 首次设置（安装必要工具）
chmod +x wsl_setup.sh
./wsl_setup.sh

# 2. 启动系统
chmod +x start_wsl_system.sh
./start_wsl_system.sh

# 3. 测试系统
python3 test_wsl_api.py
```

### 2. 分步骤部署

#### 步骤1: 环境检查和安装
```bash
# 运行环境设置脚本
./wsl_setup.sh
```

此脚本会：
- ✅ 检查WSL版本和发行版信息
- ✅ 更新系统包管理器
- ✅ 安装Docker和Docker Compose
- ✅ 安装Python3和pip
- ✅ 检查端口占用情况
- ✅ 配置Docker用户权限

#### 步骤2: 启动监控系统
```bash
# 启动完整的监控栈
./start_wsl_system.sh
```

此脚本会：
- 🐳 检查并启动Docker服务
- 📋 验证配置文件完整性
- 🔍 检查端口占用并清理冲突
- 🚀 构建并启动所有容器
- ⏳ 等待服务就绪
- 📱 显示访问地址和管理命令

#### 步骤3: 验证和测试
```bash
# 运行WSL专用测试脚本
python3 test_wsl_api.py
```

此脚本会：
- 🐧 检查WSL环境配置
- 🌐 验证网络连接性
- 🐳 检查Docker容器状态
- 🔌 测试API连接性
- 🧪 运行全面功能测试
- 📊 生成测试报告

## 📱 访问地址（从Windows）

在Windows浏览器中访问以下地址：

- **Flask应用**: http://localhost:5000
- **Grafana**: http://localhost:3000
  - 用户名: admin
  - 密码: admin123
- **Prometheus**: http://localhost:9090
- **Alertmanager**: http://localhost:9093

## 🔧 WSL特殊配置

### 网络配置
WSL2使用虚拟化网络，但服务可以通过localhost从Windows访问：

```bash
# 查看WSL内部IP
hostname -I

# 查看网络路由
ip route show default

# 检查端口监听
netstat -tuln | grep LISTEN
```

### Docker配置
```bash
# 启动Docker服务
sudo service docker start

# 检查Docker状态
docker info

# 查看容器状态
docker-compose ps

# 查看日志
docker-compose logs -f
```

### 防火墙设置
如果无法从Windows访问WSL服务，可能需要配置Windows防火墙：

1. 打开Windows防火墙设置
2. 允许应用通过防火墙
3. 添加端口规则（5000, 3000, 9090, 9093）

## 🛠️ 常用管理命令

### 服务管理
```bash
# 查看所有容器状态
docker-compose ps

# 查看实时日志
docker-compose logs -f

# 查看特定服务日志
docker-compose logs -f app        # Flask应用
docker-compose logs -f grafana    # Grafana
docker-compose logs -f prometheus # Prometheus

# 重启服务
docker-compose restart

# 停止服务
docker-compose down

# 重新构建并启动
docker-compose up -d --build
```

### 系统监控
```bash
# 查看系统资源使用
docker stats

# 查看磁盘使用
docker system df

# 清理未使用的镜像和容器
docker system prune
```

### 网络诊断
```bash
# 检查端口占用
netstat -tuln | grep :5000

# 测试服务连通性
curl http://localhost:5000/health

# 检查DNS解析
nslookup localhost
```

## 🚨 故障排除

### 常见问题及解决方案

#### 1. Docker服务启动失败
```bash
# 重启Docker服务
sudo service docker restart

# 检查Docker状态
sudo service docker status

# 查看Docker日志
journalctl -u docker.service
```

#### 2. 端口被占用
```bash
# 查看端口占用
netstat -tuln | grep :5000

# 杀死占用进程
sudo lsof -ti:5000 | xargs sudo kill -9

# 或停止所有Docker容器
docker-compose down
```

#### 3. 网络连接问题
```bash
# 重启WSL网络
wsl --shutdown
# 然后重新启动WSL

# 检查WSL版本
wsl -l -v

# 重置网络配置
sudo service networking restart
```

#### 4. 权限问题
```bash
# 将用户添加到docker组
sudo usermod -aG docker $USER

# 重新登录或运行
newgrp docker

# 检查权限
groups $USER
```

#### 5. 内存不足
```bash
# 查看内存使用
free -h

# 查看Docker内存使用
docker stats

# 清理Docker资源
docker system prune -a
```

### 日志分析
```bash
# 查看应用错误日志
docker-compose logs app | grep ERROR

# 查看Prometheus目标状态
curl http://localhost:9090/api/v1/targets

# 查看Grafana数据源状态
curl -u admin:admin123 http://localhost:3000/api/datasources
```

## 📊 性能优化

### WSL资源配置
创建 `%UserProfile%\.wslconfig` 文件：

```ini
[wsl2]
memory=4GB
processors=2
swap=2GB
```

### Docker资源限制
在 `docker-compose.yml` 中添加资源限制：

```yaml
services:
  app:
    deploy:
      resources:
        limits:
          memory: 512M
          cpus: '0.5'
```

## 🔒 安全考虑

### 生产环境建议
1. **修改默认密码**: 更改Grafana默认密码
2. **启用HTTPS**: 配置SSL证书
3. **网络隔离**: 使用Docker网络隔离
4. **访问控制**: 实施IP白名单
5. **数据持久化**: 替换内存存储为数据库

### 开发环境安全
```bash
# 仅绑定本地接口
export FLASK_HOST=127.0.0.1

# 禁用调试模式
export FLASK_DEBUG=false

# 设置强密码
export GRAFANA_ADMIN_PASSWORD=your_strong_password
```

## 📈 监控最佳实践

### Grafana仪表盘
1. 导入项目提供的仪表盘模板
2. 根据业务需求自定义面板
3. 设置告警阈值
4. 配置通知渠道

### Prometheus配置
1. 调整抓取间隔
2. 配置数据保留期
3. 添加自定义指标
4. 优化查询性能

### 告警规则
1. 配置多级告警
2. 设置合理阈值
3. 避免告警风暴
4. 定期回顾调整

## 🎯 扩展开发

### 添加新API接口
1. 在 `app.py` 中添加路由
2. 实现业务逻辑
3. 添加Prometheus指标
4. 更新测试脚本
5. 创建Grafana面板

### 集成其他服务
1. 数据库集成
2. 认证服务
3. 消息队列
4. 缓存系统
5. 日志聚合

## 📞 技术支持

如果遇到问题，请按以下顺序排查：

1. **检查环境**: 运行 `python3 test_wsl_api.py`
2. **查看日志**: `docker-compose logs -f`
3. **验证配置**: 检查YAML文件语法
4. **网络诊断**: 使用curl测试连接
5. **重启服务**: `docker-compose restart`

## 🎉 总结

通过WSL专用的部署脚本和测试工具，您可以：

- ✅ **一键部署**: 自动化安装和配置
- ✅ **环境检测**: 智能识别和解决问题
- ✅ **全面测试**: 验证所有功能正常
- ✅ **实时监控**: 15个API接口的完整监控
- ✅ **可视化分析**: Grafana仪表盘展示
- ✅ **故障排除**: 详细的问题解决指南

现在您可以在WSL环境中享受完整的登录监控系统了！🚀