#!/bin/bash

# Flask 服务启动脚本

echo "=== Flask Consul 服务发现演示 ==="

# 检查 Python 和 pip
if ! command -v python3 &> /dev/null; then
    echo "错误: Python3 未安装"
    exit 1
fi

# 安装依赖
echo "安装 Python 依赖..."
pip3 install -r requirements.txt

# 检查 Consul 是否运行
echo "检查 Consul 是否运行..."
if ! curl -f http://localhost:8500/v1/status/leader &> /dev/null; then
    echo "警告: Consul 似乎没有运行在 localhost:8500"
    echo "请先运行 ./scripts/start_consul.sh 启动 Consul"
    echo "继续启动服务..."
fi

# 函数：启动服务
start_service() {
    local service_name=$1
    local service_path=$2
    local port=$3
    
    echo "启动 $service_name (端口 $port)..."
    cd $service_path
    python3 main.py &
    local pid=$!
    echo "$service_name PID: $pid"
    cd - > /dev/null
    
    # 等待服务启动
    sleep 2
    
    # 检查服务是否启动成功
    if curl -f http://localhost:$port/health &> /dev/null; then
        echo "✓ $service_name 启动成功"
    else
        echo "✗ $service_name 启动失败"
    fi
    
    return $pid
}

# 启动用户服务
start_service "用户服务" "services/user_service" 5001
USER_PID=$?

# 启动订单服务
start_service "订单服务" "services/order_service" 5002
ORDER_PID=$?

echo ""
echo "=== 服务已启动 ==="
echo "用户服务: http://localhost:5001"
echo "订单服务: http://localhost:5002"
echo "Consul UI: http://localhost:8500"
echo ""
echo "运行客户端示例:"
echo "cd client && python3 main.py"
echo ""
echo "按 Ctrl+C 停止所有服务"

# 清理函数
cleanup() {
    echo ""
    echo "正在停止服务..."
    kill $USER_PID $ORDER_PID 2>/dev/null
    echo "所有服务已停止"
    exit 0
}

# 捕获中断信号
trap cleanup SIGINT SIGTERM

# 等待
wait