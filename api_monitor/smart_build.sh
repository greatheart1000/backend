#!/bin/bash
# 智能Docker构建脚本

echo "🔧 智能Docker构建脚本"
echo "===================="

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

# 1. 网络连接测试
echo -e "${BLUE}🌐 测试网络连接...${NC}"
if timeout 10 curl -s https://registry-1.docker.io/v2/ > /dev/null; then
    echo -e "${GREEN}✅ Docker Hub连接正常${NC}"
    NETWORK_OK=true
else
    echo -e "${YELLOW}⚠️  Docker Hub连接有问题${NC}"
    NETWORK_OK=false
fi

# 2. 检查基础镜像是否存在
echo -e "${BLUE}🔍 检查基础镜像...${NC}"
if docker images | grep -q "python.*3.9"; then
    echo -e "${GREEN}✅ Python镜像已存在${NC}"
    IMAGE_EXISTS=true
else
    echo -e "${YELLOW}⚠️  需要拉取Python镜像${NC}"
    IMAGE_EXISTS=false
fi

# 3. 智能构建策略
if [ "$NETWORK_OK" = false ] && [ "$IMAGE_EXISTS" = false ]; then
    echo -e "${YELLOW}🔧 网络问题且无本地镜像，执行强力网络修复...${NC}"
    
    # 执行强力网络修复
    if [ -f "force_fix_network.sh" ]; then
        chmod +x force_fix_network.sh
        ./force_fix_network.sh
    else
        echo -e "${YELLOW}尝试基础网络修复...${NC}"
        if [ -f "fix_docker_network.sh" ]; then
            chmod +x fix_docker_network.sh
            ./fix_docker_network.sh
        fi
    fi
    
    # 重新测试网络
    if timeout 10 curl -s https://registry-1.docker.io/v2/ > /dev/null; then
        echo -e "${GREEN}✅ 网络修复成功${NC}"
        NETWORK_OK=true
    else
        echo -e "${RED}❌ 网络修复失败，尝试离线构建...${NC}"
        
        # 尝试离线构建
        if [ -f "offline_build.sh" ]; then
            echo -e "${BLUE}使用离线构建方案...${NC}"
            chmod +x offline_build.sh
            ./offline_build.sh
            exit $?
        else
            echo -e "${RED}❌ 离线构建脚本不存在${NC}"
            exit 1
        fi
    fi
elif [ "$NETWORK_OK" = false ]; then
    echo -e "${YELLOW}💻 网络问题但有本地镜像，尝试本地构建...${NC}"
    
    # 优先尝试使用本地镜像构建
    if [ -f "offline_build.sh" ]; then
        chmod +x offline_build.sh
        ./offline_build.sh
        exit $?
    fi
fi

# 4. 尝试构建
echo -e "${BLUE}🚀 开始构建服务...${NC}"

# 首先尝试正常构建
echo "尝试标准构建..."
if timeout 600 $DOCKER_COMPOSE_CMD build; then
    echo -e "${GREEN}✅ 标准构建成功${NC}"
else
    echo -e "${YELLOW}⚠️  标准构建失败，尝试Alpine版本...${NC}"
    
    # 备份原Dockerfile
    cp Dockerfile Dockerfile.backup
    
    # 使用Alpine版本
    if [ -f "Dockerfile.alpine" ]; then
        cp Dockerfile.alpine Dockerfile
        echo -e "${BLUE}使用Alpine版本重新构建...${NC}"
        
        if timeout 600 $DOCKER_COMPOSE_CMD build; then
            echo -e "${GREEN}✅ Alpine版本构建成功${NC}"
        else
            echo -e "${RED}❌ Alpine版本构建也失败${NC}"
            
            # 恢复原Dockerfile
            cp Dockerfile.backup Dockerfile
            exit 1
        fi
    else
        echo -e "${RED}❌ Alpine版本Dockerfile不存在${NC}"
        exit 1
    fi
fi

# 5. 启动服务
echo -e "${BLUE}🚀 启动服务...${NC}"
if $DOCKER_COMPOSE_CMD up -d; then
    echo -e "${GREEN}✅ 服务启动成功${NC}"
    
    # 等待服务就绪
    echo -e "${BLUE}⏳ 等待服务就绪...${NC}"
    sleep 10
    
    # 检查服务状态
    echo -e "${BLUE}📊 检查服务状态...${NC}"
    $DOCKER_COMPOSE_CMD ps
    
    # 测试Flask应用
    echo -e "${BLUE}🧪 测试Flask应用...${NC}"
    for i in {1..10}; do
        if curl -s http://localhost:5000/health > /dev/null; then
            echo -e "${GREEN}✅ Flask应用响应正常${NC}"
            break
        fi
        
        if [ $i -eq 10 ]; then
            echo -e "${YELLOW}⚠️  Flask应用未响应，请检查日志${NC}"
            echo "查看日志命令: $DOCKER_COMPOSE_CMD logs app"
        else
            echo "等待Flask启动... ($i/10)"
            sleep 3
        fi
    done
    
else
    echo -e "${RED}❌ 服务启动失败${NC}"
    exit 1
fi

echo ""
echo -e "${GREEN}🎉 构建和启动完成！${NC}"
echo "===================="
echo ""
echo -e "${BLUE}访问地址：${NC}"
echo "   Flask应用:    http://localhost:5000"
echo "   Grafana:      http://localhost:3000"
echo "   Prometheus:   http://localhost:9090"
echo "   Alertmanager: http://localhost:9093"
echo ""
echo -e "${BLUE}管理命令：${NC}"
echo "   查看状态: $DOCKER_COMPOSE_CMD ps"
echo "   查看日志: $DOCKER_COMPOSE_CMD logs -f"
echo "   停止服务: $DOCKER_COMPOSE_CMD down"
echo ""
echo -e "${BLUE}测试命令：${NC}"
echo "   python3 test_wsl_api.py"