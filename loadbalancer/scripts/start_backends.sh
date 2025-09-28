#!/bin/bash

# 启动后端服务器的脚本

# 设置脚本目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

# 默认端口列表
DEFAULT_PORTS="8001 8002 8003"
PORTS="$DEFAULT_PORTS"

# 解析命令行参数
while [[ $# -gt 0 ]]; do
    case $1 in
        --ports)
            PORTS="$2"
            shift 2
            ;;
        -h|--help)
            echo "Usage: $0 [OPTIONS]"
            echo "Options:"
            echo "  --ports \"PORT1 PORT2 ...\"  Ports for backend servers (default: \"8001 8002 8003\")"
            echo "  -h, --help                   Show this help message"
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done

echo "========================================"
echo "Backend Servers Manager"
echo "========================================"
echo "Ports: $PORTS"
echo "Project Directory: $PROJECT_DIR"
echo "========================================"

# 切换到项目目录
cd "$PROJECT_DIR"

# 检查Python环境
if ! command -v python3 &> /dev/null; then
    echo "Error: python3 is not installed"
    exit 1
fi

echo "Starting backend servers..."

# 启动后端服务器管理器
python3 examples/start_backends.py --ports $PORTS