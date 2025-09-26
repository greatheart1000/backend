#!/bin/bash

# 启动 Etcd 服务器的脚本

echo "正在启动 Etcd 服务器..."

# 检查 etcd 是否已安装
if ! command -v etcd &> /dev/null; then
    echo "错误: 未找到 etcd 命令"
    echo "请先安装 etcd:"
    echo "  Ubuntu/Debian: sudo apt-get install etcd"
    echo "  CentOS/RHEL: sudo yum install etcd"
    echo "  macOS: brew install etcd"
    echo "  或从官网下载: https://etcd.io/docs/v3.5/install/"
    exit 1
fi

# 设置数据目录
DATA_DIR="./etcd_data"
mkdir -p $DATA_DIR

# 启动 etcd（开发模式）
echo "启动 etcd (开发模式)..."
echo "数据目录: $DATA_DIR"
echo "客户端端口: 2379"
echo "对等端口: 2380"
echo "Web UI 将在以下地址可用: http://localhost:2379/v2/keys"

etcd \
  --name etcd-dev \
  --data-dir $DATA_DIR \
  --listen-client-urls http://0.0.0.0:2379 \
  --advertise-client-urls http://localhost:2379 \
  --listen-peer-urls http://0.0.0.0:2380 \
  --initial-advertise-peer-urls http://localhost:2380 \
  --initial-cluster etcd-dev=http://localhost:2380 \
  --initial-cluster-token etcd-cluster-dev \
  --initial-cluster-state new \
  --enable-v2