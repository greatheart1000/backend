#!/bin/bash
# WSL环境下的系统启动脚本

echo "🐧 WSL环境 - 登录监控系统启动脚本"
echo "================================================"

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 检测Docker Compose命令
detect_docker_compose() {
    if command -v docker-compose &> /dev/null; then
        DOCKER_COMPOSE_CMD="docker-compose"
    elif docker compose version &> /dev/null; then
        DOCKER_COMPOSE_CMD="docker compose"
    else
        echo -e "${RED}❌ Docker Compose未安装或不可用${NC}"
        echo -e "${YELLOW}请先运行: ./wsl_setup.sh${NC}"
        exit 1
    fi
    echo -e "${GREEN}✅ 使用Docker Compose命令: $DOCKER_COMPOSE_CMD${NC}"
}

# 检查Docker服务状态
check_docker() {
    echo -e "${BLUE}🐳 检查Docker服务状态...${NC}"
    
    if ! command -v docker &> /dev/null; then
        echo -e "${RED}❌ Docker未安装，请先运行 ./wsl_setup.sh${NC}"
        exit 1
    fi
    
    # 检测Docker Compose
    detect_docker_compose
    
    # 检查Docker守护进程是否运行
    if ! docker info &> /dev/null; then
        echo -e "${YELLOW}⚠️  Docker守护进程未运行，正在启动...${NC}"
        sudo service docker start
        sleep 3
        
        if ! docker info &> /dev/null; then
            echo -e "${RED}❌ Docker启动失败${NC}"
            exit 1
        fi
    fi
    
    echo -e "${GREEN}✅ Docker服务正常${NC}"
}

# 检查端口占用
check_ports() {
    echo -e "${BLUE}🔍 检查端口占用...${NC}"
    
    ports=(5000 3000 9090 9093)
    occupied_ports=()
    
    for port in "${ports[@]}"; do
        if netstat -tuln 2>/dev/null | grep ":$port " > /dev/null; then
            occupied_ports+=($port)
        fi
    done
    
    if [ ${#occupied_ports[@]} -gt 0 ]; then
        echo -e "${YELLOW}⚠️  以下端口已被占用: ${occupied_ports[*]}${NC}"
        echo -e "${YELLOW}   如果是之前的容器，将自动停止并重启${NC}"
        $DOCKER_COMPOSE_CMD down 2>/dev/null
    else
        echo -e "${GREEN}✅ 所有端口可用${NC}"
    fi
}

# 检查配置文件
check_config() {
    echo -e "${BLUE}📋 检查配置文件...${NC}"
    
    required_files=(
        "docker-compose.yml"
        "Dockerfile"
        "app.py"
        "prometheus.yml"
        "alertmanager.yml"
        "rules.yml"
    )
    
    missing_files=()
    for file in "${required_files[@]}"; do
        if [ ! -f "$file" ]; then
            missing_files+=($file)
        fi
    done
    
    if [ ${#missing_files[@]} -gt 0 ]; then
        echo -e "${RED}❌ 缺少配置文件: ${missing_files[*]}${NC}"
        exit 1
    fi
    
    echo -e "${GREEN}✅ 配置文件完整${NC}"
}

# 构建并启动服务
start_services() {
    echo -e "${BLUE}🚀 构建并启动服务...${NC}"
    
    # 检查是否有智能构建脚本
    if [ -f "smart_build.sh" ]; then
        echo -e "${YELLOW}   使用智能构建脚本...${NC}"
        chmod +x smart_build.sh
        if ./smart_build.sh; then
            echo -e "${GREEN}✅ 智能构建成功${NC}"
            return 0
        else
            echo -e "${YELLOW}⚠️  智能构建失败，尝试传统方式...${NC}"
        fi
    fi
    
    # 传统构建方式
    echo -e "${YELLOW}   构建Flask应用镜像...${NC}"
    $DOCKER_COMPOSE_CMD build
    
    if [ $? -ne 0 ]; then
        echo -e "${RED}❌ 镜像构建失败${NC}"
        echo -e "${YELLOW}建议尝试：${NC}"
        echo "   1. ./fix_docker_network.sh  # 修复网络问题"
        echo "   2. docker system prune      # 清理Docker缓存"
        echo "   3. ./smart_build.sh         # 使用智能构建"
        exit 1
    fi
    
    # 启动所有服务
    echo -e "${YELLOW}   启动所有服务...${NC}"
    $DOCKER_COMPOSE_CMD up -d
    
    if [ $? -ne 0 ]; then
        echo -e "${RED}❌ 服务启动失败${NC}"
        exit 1
    fi
    
    echo -e "${GREEN}✅ 服务启动成功${NC}"
}

# 等待服务就绪
wait_for_services() {
    echo -e "${BLUE}⏳ 等待服务就绪...${NC}"
    
    services=(
        "localhost:5000|Flask应用"
        "localhost:9090|Prometheus"
        "localhost:3000|Grafana"
        "localhost:9093|Alertmanager"
    )
    
    for service in "${services[@]}"; do
        IFS='|' read -r url name <<< "$service"
        echo -e "${YELLOW}   等待 ${name} 启动...${NC}"
        
        max_attempts=30
        attempt=0
        
        while [ $attempt -lt $max_attempts ]; do
            if curl -s "$url" > /dev/null 2>&1; then
                echo -e "${GREEN}   ✅ ${name} 已就绪${NC}"
                break
            fi
            
            sleep 2
            ((attempt++))
            
            if [ $attempt -eq $max_attempts ]; then
                echo -e "${YELLOW}   ⚠️  ${name} 启动时间较长，请稍后手动检查${NC}"
            fi
        done
    done
}

# 显示访问信息
show_access_info() {
    echo ""
    echo -e "${GREEN}🎉 系统启动完成！${NC}"
    echo "================================================"
    echo ""
    echo -e "${BLUE}📱 访问地址（在Windows浏览器中）：${NC}"
    echo "   🌐 Flask应用:    http://localhost:5000"
    echo "   📊 Grafana:      http://localhost:3000"
    echo "      用户名: admin"
    echo "      密码:   admin123"
    echo "   📈 Prometheus:   http://localhost:9090"
    echo "   🚨 Alertmanager: http://localhost:9093"
    echo ""
    echo -e "${BLUE}🔧 管理命令：${NC}"
    echo "   查看日志:     $DOCKER_COMPOSE_CMD logs -f"
    echo "   停止服务:     $DOCKER_COMPOSE_CMD down"
    echo "   重启服务:     $DOCKER_COMPOSE_CMD restart"
    echo "   查看状态:     $DOCKER_COMPOSE_CMD ps"
    echo ""
    echo -e "${BLUE}🧪 测试命令：${NC}"
    echo "   python3 test_wsl_api.py        # WSL专用API测试"
    echo "   curl http://localhost:5000/health  # 快速健康检查"
    echo ""
    echo -e "${BLUE}🌐 WSL网络信息：${NC}"
    echo "   WSL内部IP: $(hostname -I | awk '{print $1}')"
    echo "   Windows可以通过 localhost 访问WSL服务"
    echo ""
    echo -e "${BLUE}📋 Grafana仪表盘：${NC}"
    echo "   1. 登录Grafana后，查看以下仪表盘："
    echo "      - 登录监控系统 - 直方图分析"
    echo "      - 增强版API监控系统 - 完整指标分析"
    echo "   2. 在仪表盘中可以看到所有API接口的监控数据"
}

# 主函数
main() {
    echo -e "${GREEN}开始WSL环境部署...${NC}"
    echo ""
    
    check_docker
    check_config
    check_ports
    start_services
    wait_for_services
    show_access_info
    
    echo ""
    echo -e "${GREEN}✨ 部署完成！享受监控之旅吧！${NC}"
}

# 异常处理
trap 'echo -e "\n${RED}❌ 部署过程中断${NC}"; $DOCKER_COMPOSE_CMD down 2>/dev/null; exit 1' INT TERM

# 执行主函数
main