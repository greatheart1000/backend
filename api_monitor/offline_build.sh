#!/bin/bash
# 离线构建方案 - 无需外网连接

echo "📦 离线构建方案"
echo "=============="

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# 检测Docker Compose命令
if command -v docker-compose &> /dev/null; then
    DOCKER_COMPOSE_CMD="docker-compose"
elif docker compose version &> /dev/null; then
    DOCKER_COMPOSE_CMD="docker compose"
else
    echo -e "${RED}❌ Docker Compose不可用${NC}"
    exit 1
fi

echo -e "${GREEN}✅ 使用Docker Compose命令: $DOCKER_COMPOSE_CMD${NC}"

# 1. 检查本地镜像
echo -e "${BLUE}🔍 检查本地可用镜像...${NC}"

LOCAL_IMAGES=$(docker images --format "table {{.Repository}}:{{.Tag}}" | grep -v REPOSITORY)
echo "本地镜像列表："
echo "$LOCAL_IMAGES"

# 寻找可用的Python镜像
PYTHON_IMAGE=""
if docker images | grep -q "python.*3.9"; then
    PYTHON_IMAGE=$(docker images --format "{{.Repository}}:{{.Tag}}" | grep "python.*3.9" | head -1)
elif docker images | grep -q "python.*3.1"; then
    PYTHON_IMAGE=$(docker images --format "{{.Repository}}:{{.Tag}}" | grep "python.*3.1" | head -1)
elif docker images | grep -q "python"; then
    PYTHON_IMAGE=$(docker images --format "{{.Repository}}:{{.Tag}}" | grep "python" | head -1)
fi

if [ -n "$PYTHON_IMAGE" ]; then
    echo -e "${GREEN}✅ 找到可用Python镜像: $PYTHON_IMAGE${NC}"
else
    echo -e "${YELLOW}⚠️  未找到Python镜像，将使用本地Python环境${NC}"
fi

# 2. 创建本地Python Dockerfile
echo -e "${BLUE}🐍 创建本地Python环境Dockerfile...${NC}"

cat << 'EOF' > Dockerfile.local
# 使用Ubuntu基础镜像（通常WSL已有）
FROM ubuntu:20.04

# 设置环境变量
ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# 安装Python和必要工具
RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    python3-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# 创建符号链接
RUN ln -s /usr/bin/python3 /usr/bin/python

# 复制本地安装的Python包（如果有的话）
COPY requirements.txt .

# 安装Python包（使用本地源）
RUN pip3 install --no-cache-dir flask || \
    apt-get update && apt-get install -y python3-flask && \
    pip3 install --no-cache-dir prometheus-client || \
    apt-get install -y python3-prometheus-client || \
    echo "Using system packages"

# 复制应用代码
COPY app.py .

# 创建非root用户
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# 暴露端口
EXPOSE 5000

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD python3 -c "import urllib.request; urllib.request.urlopen('http://localhost:5000/health')" || exit 1

# 启动应用
CMD ["python3", "app.py"]
EOF

echo -e "${GREEN}✅ 本地Dockerfile创建完成${NC}"

# 3. 修改docker-compose.yml使用本地镜像
echo -e "${BLUE}🔧 创建离线版docker-compose配置...${NC}"

# 备份原配置
cp docker-compose.yml docker-compose.yml.backup

# 创建离线版本
cat << 'EOF' > docker-compose.offline.yml
version: '3.8'

services:
  app:
    build:
      context: .
      dockerfile: Dockerfile.local
    ports:
      - "5000:5000"
    environment:
      - FLASK_ENV=production
      - PYTHONUNBUFFERED=1
    healthcheck:
      test: ["CMD", "python3", "-c", "import urllib.request; urllib.request.urlopen('http://localhost:5000/health')"]
      interval: 30s
      timeout: 10s
      retries: 3
    restart: unless-stopped

  prometheus:
    image: prom/prometheus:latest
    ports:
      - "9090:9090"
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml
      - ./rules.yml:/etc/prometheus/rules.yml
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.path=/prometheus'
      - '--web.console.libraries=/etc/prometheus/console_libraries'
      - '--web.console.templates=/etc/prometheus/consoles'
      - '--storage.tsdb.retention.time=200h'
      - '--web.enable-lifecycle'
      - '--web.enable-admin-api'
    restart: unless-stopped

  grafana:
    image: grafana/grafana:latest
    ports:
      - "3000:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin123
    volumes:
      - ./grafana/provisioning:/etc/grafana/provisioning
      - ./grafana/dashboards:/var/lib/grafana/dashboards
    restart: unless-stopped

  alertmanager:
    image: prom/alertmanager:latest
    ports:
      - "9093:9093"
    volumes:
      - ./alertmanager.yml:/etc/alertmanager/alertmanager.yml
    command:
      - '--config.file=/etc/alertmanager/alertmanager.yml'
      - '--storage.path=/alertmanager'
      - '--web.external-url=http://localhost:9093'
    restart: unless-stopped
EOF

echo -e "${GREEN}✅ 离线版配置创建完成${NC}"

# 4. 尝试构建
echo -e "${BLUE}🚀 开始离线构建...${NC}"

# 首先尝试仅构建Flask应用
echo "构建Flask应用..."
if docker build -f Dockerfile.local -t login-monitor-app .; then
    echo -e "${GREEN}✅ Flask应用构建成功${NC}"
else
    echo -e "${RED}❌ Flask应用构建失败${NC}"
    
    # 尝试使用现有Python镜像
    if [ -n "$PYTHON_IMAGE" ]; then
        echo -e "${YELLOW}尝试使用现有Python镜像: $PYTHON_IMAGE${NC}"
        
        # 修改Dockerfile使用本地镜像
        sed "s|FROM ubuntu:20.04|FROM $PYTHON_IMAGE|" Dockerfile.local > Dockerfile.existing
        
        if docker build -f Dockerfile.existing -t login-monitor-app .; then
            echo -e "${GREEN}✅ 使用现有镜像构建成功${NC}"
        else
            echo -e "${RED}❌ 构建仍然失败${NC}"
            exit 1
        fi
    else
        exit 1
    fi
fi

# 5. 启动服务
echo -e "${BLUE}🚀 启动服务...${NC}"

# 停止现有服务
$DOCKER_COMPOSE_CMD down 2>/dev/null || true

# 使用离线配置启动
if $DOCKER_COMPOSE_CMD -f docker-compose.offline.yml up -d; then
    echo -e "${GREEN}✅ 服务启动成功${NC}"
    
    # 等待服务就绪
    echo -e "${BLUE}⏳ 等待服务就绪...${NC}"
    sleep 15
    
    # 检查服务状态
    $DOCKER_COMPOSE_CMD -f docker-compose.offline.yml ps
    
    echo ""
    echo -e "${GREEN}🎉 离线部署完成！${NC}"
    echo "=============="
    echo ""
    echo -e "${BLUE}访问地址：${NC}"
    echo "   Flask应用:    http://localhost:5000"
    echo "   Prometheus:   http://localhost:9090"
    echo "   Grafana:      http://localhost:3000 (admin/admin123)"
    echo "   Alertmanager: http://localhost:9093"
    
else
    echo -e "${RED}❌ 服务启动失败${NC}"
    exit 1
fi

echo ""
echo -e "${BLUE}管理命令：${NC}"
echo "   查看状态: $DOCKER_COMPOSE_CMD -f docker-compose.offline.yml ps"
echo "   查看日志: $DOCKER_COMPOSE_CMD -f docker-compose.offline.yml logs -f"
echo "   停止服务: $DOCKER_COMPOSE_CMD -f docker-compose.offline.yml down"