#!/bin/bash

# RAG系统启动脚本

echo "RAG知识库系统启动脚本"
echo "===================="

# 检查是否安装了依赖
if [ ! -f "requirements.txt" ]; then
    echo "错误: 找不到 requirements.txt 文件"
    exit 1
fi

# 安装依赖
echo "正在安装依赖..."
pip install -r requirements.txt

if [ $? -ne 0 ]; then
    echo "错误: 依赖安装失败"
    exit 1
fi

echo "依赖安装完成"

# 检查参数
if [ "$#" -eq 0 ]; then
    echo "用法:"
    echo "  启动命令行应用: ./start.sh --query \"你的问题\""
    echo "  启动API服务: ./start.sh --api"
    echo "  初始化系统: ./start.sh --init"
    echo "  环境检查: ./start.sh --check"
    exit 1
fi

# 解析参数
case "$1" in
    --query)
        if [ -z "$2" ]; then
            echo "错误: --query 参数需要指定查询内容"
            exit 1
        fi
        echo "正在处理查询: $2"
        python app.py --query "$2"
        ;;
    --api)
        echo "正在启动API服务..."
        python api.py
        ;;
    --init)
        echo "正在初始化系统..."
        python init.py
        ;;
    --check)
        echo "正在检查环境..."
        python check_env.py
        ;;
    *)
        echo "未知参数: $1"
        echo "用法:"
        echo "  启动命令行应用: ./start.sh --query \"你的问题\""
        echo "  启动API服务: ./start.sh --api"
        echo "  初始化系统: ./start.sh --init"
        echo "  环境检查: ./start.sh --check"
        exit 1
        ;;
esac