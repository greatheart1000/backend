#!/bin/bash

# 启动所有基于 Etcd 的微服务

echo "=== 启动基于 Etcd 的微服务 ==="

# 检查 etcd 是否运行
echo "检查 Etcd 连接..."
if ! curl -s http://localhost:2379/health > /dev/null 2>&1; then
    echo "错误: Etcd 服务未运行"
    echo "请先运行: ./scripts/start_etcd.sh"
    exit 1
fi

echo "✓ Etcd 连接正常"

# 安装依赖
echo "安装 Python 依赖..."
pip install etcd3 >/dev/null 2>&1

# 启动用户服务
echo "启动用户服务 (端口 5001)..."
cd user_service_etcd
python main.py &
USER_PID=$!
cd ..

# 等待用户服务启动
sleep 3

# 启动订单服务
echo "启动订单服务 (端口 5002)..."
cd order_service_etcd
python main.py &
ORDER_PID=$!
cd ..

echo ""
echo "=== 所有服务已启动 ==="
echo "用户服务: http://localhost:5001"
echo "订单服务: http://localhost:5002"
echo "Etcd API: http://localhost:2379"
echo ""
echo "运行客户端示例:"
echo "  cd client_etcd_example && python main.py"
echo ""
echo "按 Ctrl+C 停止所有服务..."

# 捕获 Ctrl+C 信号并清理
cleanup() {
    echo ""
    echo "正在停止服务..."
    kill $USER_PID $ORDER_PID 2>/dev/null
    echo "所有服务已停止"
    exit 0
}

trap cleanup SIGINT

# 等待子进程
wait