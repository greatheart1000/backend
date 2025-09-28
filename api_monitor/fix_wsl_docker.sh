#!/bin/bash
# WSL环境Docker Compose修复脚本

echo "🔧 WSL环境Docker Compose修复脚本"
echo "=================================="

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}🔍 检查Docker Compose状态...${NC}"

# 检查docker-compose命令
if command -v docker-compose &> /dev/null; then
    echo -e "${GREEN}✅ docker-compose命令可用: $(docker-compose --version)${NC}"
elif docker compose version &> /dev/null 2>&1; then
    echo -e "${YELLOW}⚠️  只有Docker Compose Plugin可用${NC}"
    echo -e "${BLUE}正在创建docker-compose兼容性链接...${NC}"
    
    # 创建docker-compose脚本包装器
    cat << 'EOF' | sudo tee /usr/local/bin/docker-compose > /dev/null
#!/bin/bash
docker compose "$@"
EOF
    
    sudo chmod +x /usr/local/bin/docker-compose
    
    if command -v docker-compose &> /dev/null; then
        echo -e "${GREEN}✅ docker-compose兼容性链接创建成功${NC}"
    else
        echo -e "${RED}❌ 创建兼容性链接失败${NC}"
    fi
    
else
    echo -e "${RED}❌ Docker Compose不可用，正在安装...${NC}"
    
    # 更新包列表
    sudo apt update
    
    # 尝试安装Docker Compose Plugin
    echo -e "${BLUE}安装Docker Compose Plugin...${NC}"
    sudo apt install -y docker-compose-plugin
    
    # 再次检查
    if docker compose version &> /dev/null 2>&1; then
        echo -e "${GREEN}✅ Docker Compose Plugin安装成功${NC}"
        
        # 创建兼容性链接
        cat << 'EOF' | sudo tee /usr/local/bin/docker-compose > /dev/null
#!/bin/bash
docker compose "$@"
EOF
        sudo chmod +x /usr/local/bin/docker-compose
        
    else
        echo -e "${YELLOW}Plugin安装失败，尝试安装独立版本...${NC}"
        
        # 获取最新版本
        COMPOSE_VERSION=$(curl -s https://api.github.com/repos/docker/compose/releases/latest | grep tag_name | cut -d '"' -f 4)
        echo "最新版本: $COMPOSE_VERSION"
        
        # 下载并安装
        sudo curl -L "https://github.com/docker/compose/releases/download/${COMPOSE_VERSION}/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
        sudo chmod +x /usr/local/bin/docker-compose
    fi
fi

echo ""
echo -e "${BLUE}🧪 测试Docker Compose...${NC}"

# 测试docker-compose命令
if command -v docker-compose &> /dev/null; then
    echo -e "${GREEN}✅ docker-compose命令测试通过: $(docker-compose --version)${NC}"
else
    echo -e "${RED}❌ docker-compose命令不可用${NC}"
    exit 1
fi

# 测试docker compose命令
if docker compose version &> /dev/null 2>&1; then
    echo -e "${GREEN}✅ docker compose命令测试通过: $(docker compose version)${NC}"
else
    echo -e "${YELLOW}⚠️  docker compose命令不可用（非必需）${NC}"
fi

echo ""
echo -e "${BLUE}🐍 处理Python环境问题...${NC}"

# 检查Python包管理方式
if [ -f "/etc/debian_version" ]; then
    echo "检测到Debian/Ubuntu系统，使用apt安装Python包..."
    sudo apt update
    sudo apt install -y python3-flask python3-prometheus-client python3-requests python3-urllib3
    
    echo -e "${GREEN}✅ Python依赖通过apt安装完成${NC}"
else
    echo "创建Python虚拟环境..."
    
    # 安装必要的包
    sudo apt update
    sudo apt install -y python3-venv python3-full
    
    # 创建虚拟环境
    if [ ! -d "venv" ]; then
        python3 -m venv venv
        echo -e "${GREEN}✅ 虚拟环境创建完成${NC}"
    fi
    
    # 激活虚拟环境并安装依赖
    source venv/bin/activate
    pip install flask prometheus-client requests
    echo -e "${GREEN}✅ Python依赖安装完成${NC}"
fi

echo ""
echo -e "${GREEN}🎉 修复完成！${NC}"
echo "=================================="
echo ""
echo -e "${BLUE}现在可以运行：${NC}"
echo "   ./start_wsl_system.sh"
echo ""
echo -e "${BLUE}如果还有问题，请检查：${NC}"
echo "   docker --version"
echo "   docker-compose --version"
echo "   docker compose version"
echo "   sudo service docker status"