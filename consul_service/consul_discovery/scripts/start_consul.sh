#!/bin/bash

# Consul 启动脚本 (Linux/macOS)

echo "正在启动 Consul..."

# 检查 Consul 是否已安装
if ! command -v consul &> /dev/null; then
    echo "错误: Consul 未安装"
    echo "请访问 https://www.consul.io/downloads 下载安装 Consul"
    exit 1
fi

# 创建数据目录
mkdir -p ./consul_data

# 启动 Consul 开发模式
consul agent -dev \
    -data-dir=./consul_data \
    -node=consul-dev \
    -bind=127.0.0.1 \
    -client=0.0.0.0 \
    -ui-config-enabled \
    -log-level=INFO

echo "Consul 已启动"
echo "Web UI: http://localhost:8500"