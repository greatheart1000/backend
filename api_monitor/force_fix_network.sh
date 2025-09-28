#!/bin/bash
# 强力网络修复脚本 - 专门解决Docker Hub连接问题

echo "🔧 强力网络修复脚本"
echo "=================="

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# 1. 重置网络配置
echo -e "${BLUE}🌐 重置网络配置...${NC}"

# 重置DNS配置
sudo bash -c 'echo "# WSL DNS Configuration" > /etc/resolv.conf'
sudo bash -c 'echo "nameserver 8.8.8.8" >> /etc/resolv.conf'
sudo bash -c 'echo "nameserver 1.1.1.1" >> /etc/resolv.conf'
sudo bash -c 'echo "nameserver 223.5.5.5" >> /etc/resolv.conf'

echo "DNS配置已更新："
cat /etc/resolv.conf

# 2. 配置Docker镜像源
echo -e "${BLUE}🐳 配置Docker镜像源...${NC}"

# 创建Docker配置目录
sudo mkdir -p /etc/docker

# 更强力的镜像源配置
cat << 'EOF' | sudo tee /etc/docker/daemon.json > /dev/null
{
  "registry-mirrors": [
    "https://docker.mirrors.ustc.edu.cn",
    "https://hub-mirror.c.163.com",
    "https://mirror.baidubce.com",
    "https://dockerhub.azk8s.cn",
    "https://reg-mirror.qiniu.com"
  ],
  "dns": ["8.8.8.8", "1.1.1.1", "223.5.5.5"],
  "max-concurrent-downloads": 3,
  "max-concurrent-uploads": 3,
  "max-download-attempts": 5,
  "insecure-registries": [],
  "live-restore": true
}
EOF

echo -e "${GREEN}✅ Docker配置已更新${NC}"

# 3. 重启网络服务
echo -e "${BLUE}🔄 重启网络和Docker服务...${NC}"

# 重启Docker服务
sudo service docker stop
sleep 2
sudo service docker start
sleep 5

# 验证Docker状态
if docker info > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Docker服务重启成功${NC}"
else
    echo -e "${RED}❌ Docker服务重启失败${NC}"
    
    # 尝试修复Docker
    echo -e "${YELLOW}尝试修复Docker...${NC}"
    sudo dockerd-rootless-setuptool.sh uninstall 2>/dev/null || true
    sudo service docker restart
    sleep 5
    
    if docker info > /dev/null 2>&1; then
        echo -e "${GREEN}✅ Docker修复成功${NC}"
    else
        echo -e "${RED}❌ Docker修复失败，请手动检查${NC}"
        exit 1
    fi
fi

# 4. 测试网络连接
echo -e "${BLUE}🧪 测试网络连接...${NC}"

# 测试DNS解析
echo "测试DNS解析..."
if nslookup registry-1.docker.io > /dev/null 2>&1; then
    echo -e "${GREEN}✅ DNS解析正常${NC}"
else
    echo -e "${YELLOW}⚠️  DNS解析有问题${NC}"
    
    # 刷新DNS缓存
    sudo systemctl restart systemd-resolved 2>/dev/null || true
fi

# 测试网络连通性
echo "测试网络连通性..."
MIRRORS=(
    "docker.mirrors.ustc.edu.cn"
    "hub-mirror.c.163.com" 
    "mirror.baidubce.com"
    "registry-1.docker.io"
)

WORKING_MIRROR=""
for mirror in "${MIRRORS[@]}"; do
    echo "测试镜像源: $mirror"
    if timeout 10 curl -s "https://$mirror/v2/" > /dev/null 2>&1; then
        echo -e "${GREEN}✅ $mirror 连接正常${NC}"
        WORKING_MIRROR="$mirror"
        break
    else
        echo -e "${YELLOW}⚠️  $mirror 连接失败${NC}"
    fi
done

if [ -z "$WORKING_MIRROR" ]; then
    echo -e "${RED}❌ 所有镜像源都无法连接${NC}"
    echo -e "${YELLOW}可能的原因：${NC}"
    echo "1. 企业网络限制"
    echo "2. 防火墙阻拦"
    echo "3. WSL网络配置问题"
    echo "4. Windows防火墙设置"
    
    echo -e "${BLUE}建议解决方案：${NC}"
    echo "1. 检查Windows防火墙设置"
    echo "2. 尝试使用代理服务器"
    echo "3. 联系网络管理员"
    echo "4. 使用离线镜像"
    exit 1
else
    echo -e "${GREEN}✅ 找到可用镜像源: $WORKING_MIRROR${NC}"
fi

# 5. 预拉取关键镜像
echo -e "${BLUE}📥 预拉取关键镜像...${NC}"

# 使用最小的镜像开始测试
IMAGES=(
    "alpine:latest"
    "python:3.9-alpine"
    "python:3.9-slim"
    "prom/prometheus:latest"
    "grafana/grafana:latest"
    "prom/alertmanager:latest"
)

PULLED_IMAGES=()
for image in "${IMAGES[@]}"; do
    echo "拉取镜像: $image"
    if timeout 300 docker pull $image; then
        echo -e "${GREEN}✅ $image 拉取成功${NC}"
        PULLED_IMAGES+=("$image")
    else
        echo -e "${YELLOW}⚠️  $image 拉取失败${NC}"
        
        # 如果是Python镜像失败，尝试其他版本
        if [[ $image == *"python"* ]]; then
            echo "尝试拉取更小的Python镜像..."
            if timeout 300 docker pull python:3.11-alpine; then
                echo -e "${GREEN}✅ python:3.11-alpine 拉取成功${NC}"
                PULLED_IMAGES+=("python:3.11-alpine")
            fi
        fi
    fi
done

# 6. 显示结果
echo ""
echo -e "${GREEN}🎉 网络修复完成！${NC}"
echo "=================="
echo ""
echo -e "${BLUE}拉取成功的镜像：${NC}"
for image in "${PULLED_IMAGES[@]}"; do
    echo "  ✅ $image"
done

echo ""
echo -e "${BLUE}Docker配置信息：${NC}"
echo "镜像源配置: /etc/docker/daemon.json"
echo "DNS配置: /etc/resolv.conf"

echo ""
echo -e "${BLUE}测试命令：${NC}"
echo "docker pull alpine:latest          # 测试基础拉取"
echo "docker images                      # 查看已有镜像"
echo "docker info                        # 查看Docker信息"

echo ""
echo -e "${BLUE}如果问题依然存在：${NC}"
echo "1. 重启WSL: wsl --shutdown (在Windows PowerShell中)"
echo "2. 重启Docker: sudo service docker restart"
echo "3. 清理Docker: docker system prune -a"
echo "4. 使用本地构建: ./smart_build.sh"

echo ""
echo -e "${GREEN}✨ 现在可以尝试构建项目了！${NC}"