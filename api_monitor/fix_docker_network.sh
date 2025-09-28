#!/bin/bash
# Docker网络连接修复脚本

echo "🌐 Docker网络连接修复脚本"
echo "=========================="

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# 1. 检查网络连接
echo -e "${BLUE}🔍 检查网络连接...${NC}"
if ping -c 3 registry-1.docker.io > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Docker Hub连接正常${NC}"
else
    echo -e "${YELLOW}⚠️  Docker Hub连接有问题，尝试修复...${NC}"
    
    # 检查DNS设置
    echo -e "${BLUE}检查DNS配置...${NC}"
    cat /etc/resolv.conf
    
    # 添加公共DNS
    echo -e "${BLUE}配置DNS服务器...${NC}"
    sudo bash -c 'echo "nameserver 8.8.8.8" >> /etc/resolv.conf'
    sudo bash -c 'echo "nameserver 1.1.1.1" >> /etc/resolv.conf'
fi

# 2. 配置Docker镜像源
echo -e "${BLUE}🐳 配置Docker镜像源...${NC}"

# 创建Docker配置目录
sudo mkdir -p /etc/docker

# 配置国内镜像源
cat << 'EOF' | sudo tee /etc/docker/daemon.json > /dev/null
{
  "registry-mirrors": [
    "https://docker.mirrors.ustc.edu.cn",
    "https://hub-mirror.c.163.com",
    "https://mirror.baidubce.com"
  ],
  "dns": ["8.8.8.8", "1.1.1.1"],
  "max-concurrent-downloads": 3,
  "max-concurrent-uploads": 3
}
EOF

echo -e "${GREEN}✅ Docker镜像源配置完成${NC}"

# 3. 重启Docker服务
echo -e "${BLUE}🔄 重启Docker服务...${NC}"
sudo service docker restart
sleep 5

# 验证Docker状态
if docker info > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Docker服务重启成功${NC}"
else
    echo -e "${RED}❌ Docker服务重启失败${NC}"
    exit 1
fi

# 4. 预拉取基础镜像
echo -e "${BLUE}📥 预拉取基础镜像...${NC}"

# 尝试拉取Python镜像
echo "拉取python:3.9-slim镜像..."
if timeout 300 docker pull python:3.9-slim; then
    echo -e "${GREEN}✅ Python镜像拉取成功${NC}"
else
    echo -e "${YELLOW}⚠️  Python镜像拉取失败，尝试其他版本...${NC}"
    
    # 尝试更小的版本
    if timeout 300 docker pull python:3.9-alpine; then
        echo -e "${GREEN}✅ Python Alpine镜像拉取成功${NC}"
        echo -e "${YELLOW}建议修改Dockerfile使用alpine版本${NC}"
    else
        echo -e "${RED}❌ 镜像拉取仍然失败${NC}"
    fi
fi

# 5. 检查其他必要镜像
echo -e "${BLUE}📦 检查其他服务镜像...${NC}"

images=(
    "prom/prometheus:latest"
    "prom/alertmanager:latest" 
    "grafana/grafana:latest"
)

for image in "${images[@]}"; do
    echo "检查镜像: $image"
    if docker images | grep -q $(echo $image | cut -d':' -f1); then
        echo -e "${GREEN}✅ $image 已存在${NC}"
    else
        echo "拉取镜像: $image"
        if timeout 180 docker pull $image; then
            echo -e "${GREEN}✅ $image 拉取成功${NC}"
        else
            echo -e "${YELLOW}⚠️  $image 拉取失败，构建时会重试${NC}"
        fi
    fi
done

# 6. 网络诊断信息
echo ""
echo -e "${BLUE}🔍 网络诊断信息：${NC}"
echo "DNS配置:"
cat /etc/resolv.conf | grep nameserver

echo ""
echo "Docker配置:"
sudo cat /etc/docker/daemon.json

echo ""
echo "Docker信息:"
docker version --format 'Client: {{.Client.Version}}, Server: {{.Server.Version}}'

echo ""
echo -e "${GREEN}🎉 网络修复完成！${NC}"
echo "=========================="
echo ""
echo -e "${BLUE}建议的后续步骤：${NC}"
echo "1. 运行: docker pull python:3.9-slim  # 验证镜像拉取"
echo "2. 运行: ./start_wsl_system.sh        # 重新启动系统"
echo "3. 如果仍有问题，尝试: docker system prune  # 清理Docker缓存"