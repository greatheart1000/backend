@echo off
REM 启动 Etcd 服务器的脚本 (Windows)

echo 正在启动 Etcd 服务器...

REM 检查 etcd 是否存在
where etcd >nul 2>nul
if %errorlevel% neq 0 (
    echo 错误: 未找到 etcd 命令
    echo 请先安装 etcd:
    echo   1. 从官网下载: https://etcd.io/docs/v3.5/install/
    echo   2. 解压到系统 PATH 中
    echo   3. 或使用 Chocolatey: choco install etcd
    pause
    exit /b 1
)

REM 设置数据目录
set DATA_DIR=.\etcd_data
if not exist %DATA_DIR% mkdir %DATA_DIR%

echo 启动 etcd (开发模式)...
echo 数据目录: %DATA_DIR%
echo 客户端端口: 2379
echo 对等端口: 2380
echo Web API 将在以下地址可用: http://localhost:2379/v2/keys

etcd ^
  --name etcd-dev ^
  --data-dir %DATA_DIR% ^
  --listen-client-urls http://0.0.0.0:2379 ^
  --advertise-client-urls http://localhost:2379 ^
  --listen-peer-urls http://0.0.0.0:2380 ^
  --initial-advertise-peer-urls http://localhost:2380 ^
  --initial-cluster etcd-dev=http://localhost:2380 ^
  --initial-cluster-token etcd-cluster-dev ^
  --initial-cluster-state new ^
  --enable-v2

pause