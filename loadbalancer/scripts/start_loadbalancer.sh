#!/bin/bash

# Flask负载均衡器启动脚本

# 设置脚本目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

# 默认配置
HOST="0.0.0.0"
PORT="8080"
ALGORITHM="round_robin"
DEBUG="false"

# 解析命令行参数
while [[ $# -gt 0 ]]; do
    case $1 in
        --host)
            HOST="$2"
            shift 2
            ;;
        --port)
            PORT="$2"
            shift 2
            ;;
        --algorithm)
            ALGORITHM="$2"
            shift 2
            ;;
        --debug)
            DEBUG="true"
            shift
            ;;
        -h|--help)
            echo "Usage: $0 [OPTIONS]"
            echo "Options:"
            echo "  --host HOST           Host to bind to (default: 0.0.0.0)"
            echo "  --port PORT           Port to bind to (default: 8080)"
            echo "  --algorithm ALGO      Load balancing algorithm (default: round_robin)"
            echo "                        Options: round_robin, weighted_round_robin, ip_hash, least_connections"
            echo "  --debug               Enable debug mode"
            echo "  -h, --help            Show this help message"
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done

echo "========================================"
echo "Flask Load Balancer"
echo "========================================"
echo "Host: $HOST"
echo "Port: $PORT"
echo "Algorithm: $ALGORITHM"
echo "Debug: $DEBUG"
echo "Project Directory: $PROJECT_DIR"
echo "========================================"

# 切换到项目目录
cd "$PROJECT_DIR"

# 检查Python环境
if ! command -v python3 &> /dev/null; then
    echo "Error: python3 is not installed"
    exit 1
fi

# 检查依赖
if [ ! -f "requirements.txt" ]; then
    echo "Error: requirements.txt not found"
    exit 1
fi

# 安装依赖（如果需要）
echo "Checking dependencies..."
python3 -m pip install -r requirements.txt > /dev/null 2>&1

# 构建Python参数
PYTHON_ARGS="--host $HOST --port $PORT --algorithm $ALGORITHM"
if [ "$DEBUG" = "true" ]; then
    PYTHON_ARGS="$PYTHON_ARGS --debug"
fi

echo "Starting Flask Load Balancer..."
echo "Command: python3 app/main.py $PYTHON_ARGS"
echo ""

# 启动负载均衡器
python3 app/main.py $PYTHON_ARGS