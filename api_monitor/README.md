# WSL登录监控系统

基于 Flask + Prometheus + Grafana + Alertmanager 的增强版登录监控告警系统，专为WSL环境优化。

## 🚀 快速开始

### 在WSL中运行

```bash
# 1. 进入WSL环境
wsl

# 2. 导航到项目目录
cd /mnt/e/project/LLM-finetune-ResNet/login_monitor

# 3. 环境初始化（首次运行）
chmod +x *.sh
./wsl_setup.sh

# 4. 启动系统
./start_wsl_system.sh

# 5. 测试系统
python3 test_wsl_api.py
```

## 📱 访问地址

从Windows浏览器访问：

- **Flask应用**: http://localhost:5000
- **Grafana**: http://localhost:3000 (admin/admin123)
- **Prometheus**: http://localhost:9090
- **Alertmanager**: http://localhost:9093

## 🔧 管理命令

```bash
# 查看容器状态
docker-compose ps

# 查看日志
docker-compose logs -f

# 重启服务
docker-compose restart

# 停止服务
docker-compose down
```

## 📊 功能特性

- **15个API接口**：完整的用户管理、文件操作、统计分析
- **30+监控指标**：API级别和业务级别的全方位监控
- **2个Grafana仪表盘**：实时数据可视化
- **智能告警**：多级告警规则和通知机制

## 📋 文件说明

- `wsl_setup.sh` - WSL环境初始化脚本
- `start_wsl_system.sh` - 系统启动脚本
- `test_wsl_api.py` - WSL专用测试脚本
- `app.py` - Flask主应用
- `docker-compose.yml` - 容器编排配置
- `prometheus.yml` - Prometheus配置
- `alertmanager.yml` - 告警管理配置
- `rules.yml` - 告警规则
- `grafana/` - Grafana配置和仪表盘

详细部署指南请查看：[WSL_DEPLOYMENT_GUIDE.md](WSL_DEPLOYMENT_GUIDE.md)