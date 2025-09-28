#!/bin/bash

echo "🧪 负载均衡算法测试脚本"
echo "================================"

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 测试函数
test_algorithm() {
    local algorithm=$1
    local port=$2
    local test_name=$3
    
    echo -e "\n${BLUE}🔄 测试 $test_name${NC}"
    echo "启动命令: python app/main.py --algorithm $algorithm --port $port"
    echo "等待服务启动..."
    
    # 等待服务启动
    sleep 3
    
    # 检查服务是否可用
    if curl -s http://localhost:$port/lb/health > /dev/null; then
        echo -e "${GREEN}✅ 服务启动成功${NC}"
        
        echo -e "\n${YELLOW}📊 发送测试请求:${NC}"
        for i in {1..6}; do
            echo -n "Request $i: "
            response=$(curl -s http://localhost:$port/ 2>/dev/null)
            if [[ $? -eq 0 ]]; then
                echo $response | jq -r '.server_info.id' 2>/dev/null || echo "解析失败"
            else
                echo -e "${RED}请求失败${NC}"
            fi
        done
        
        echo -e "\n${YELLOW}📈 后端统计信息:${NC}"
        curl -s http://localhost:$port/lb/backends | jq -r '.[] | "\(.id): \(.total_requests) requests"' 2>/dev/null
        
    else
        echo -e "${RED}❌ 服务启动失败，请检查端口 $port${NC}"
    fi
}

# 测试不同IP哈希的函数
test_ip_hash() {
    local port=$1
    
    echo -e "\n${BLUE}🔗 测试IP哈希 - 不同IP分布${NC}"
    
    echo "模拟不同客户端IP:"
    for ip in "192.168.1.100" "192.168.1.101" "192.168.1.102" "10.0.0.1" "172.16.0.1"; do
        echo -n "IP $ip: "
        response=$(curl -s -H "X-Forwarded-For: $ip" http://localhost:$port/ 2>/dev/null)
        if [[ $? -eq 0 ]]; then
            echo $response | jq -r '.server_info.id' 2>/dev/null || echo "解析失败"
        else
            echo -e "${RED}请求失败${NC}"
        fi
    done
}

# 主测试流程
main() {
    echo "请确保后端服务已启动 (端口 8001, 8002, 8003)"
    echo "如果没有启动，请运行: ./scripts/start_backends.sh --ports \"8001 8002 8003\""
    echo ""
    read -p "后端服务已启动吗? (y/n): " -n 1 -r
    echo
    
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "请先启动后端服务，然后重新运行此脚本"
        exit 1
    fi
    
    echo -e "\n${GREEN}开始测试各种负载均衡算法...${NC}"
    
    # 注意：这个脚本只是展示测试方法，实际需要在不同终端窗口手动启动各个算法
    echo -e "\n${YELLOW}⚠️  请在不同的终端窗口中手动启动以下服务:${NC}"
    echo "终端1: python app/main.py --algorithm round_robin --port 8090"
    echo "终端2: python app/main.py --algorithm weighted_round_robin --port 8091" 
    echo "终端3: python app/main.py --algorithm ip_hash --port 8092"
    echo "终端4: python app/main.py --algorithm least_connections --port 8093"
    echo ""
    echo "然后使用以下命令进行测试:"
    
    # 轮询测试
    echo -e "\n${BLUE}🔄 轮询算法测试:${NC}"
    echo 'for i in {1..6}; do curl -s http://localhost:8090/ | jq -r ".server_info.id"; done'
    
    # 加权轮询测试  
    echo -e "\n${BLUE}⚖️ 加权轮询测试:${NC}"
    echo 'for i in {1..12}; do curl -s http://localhost:8091/ | jq -r ".server_info.id"; done | sort | uniq -c'
    
    # IP哈希测试
    echo -e "\n${BLUE}🔗 IP哈希测试:${NC}"
    echo '# 同一IP会话保持'
    echo 'for i in {1..5}; do curl -s http://localhost:8092/ | jq -r ".server_info.id"; done'
    echo '# 不同IP分布'
    echo 'curl -s -H "X-Forwarded-For: 192.168.1.100" http://localhost:8092/ | jq -r ".server_info.id"'
    echo 'curl -s -H "X-Forwarded-For: 192.168.1.101" http://localhost:8092/ | jq -r ".server_info.id"'
    
    # 最少连接测试
    echo -e "\n${BLUE}📊 最少连接测试:${NC}"
    echo 'for i in {1..6}; do curl -s http://localhost:8093/ | jq -r ".server_info.id"; done'
    
    # 统计信息
    echo -e "\n${BLUE}📈 统计信息查看:${NC}"
    echo 'curl -s http://localhost:8090/lb/stats | jq'
    echo 'curl -s http://localhost:8091/lb/backends | jq'
    
}

# 检查依赖
if ! command -v jq &> /dev/null; then
    echo -e "${RED}❌ 需要安装jq工具: sudo apt-get install jq${NC}"
    exit 1
fi

if ! command -v curl &> /dev/null; then
    echo -e "${RED}❌ 需要安装curl工具${NC}"
    exit 1
fi

main