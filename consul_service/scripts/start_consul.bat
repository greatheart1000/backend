@echo off
REM Consul 启动脚本 (Windows)

echo 正在启动 Consul...

REM 检查 Consul 是否已安装
consul version >nul 2>&1
if errorlevel 1 (
    echo 错误: Consul 未安装
    echo 请访问 https://www.consul.io/downloads 下载安装 Consul
    pause
    exit /b 1
)

REM 创建数据目录
if not exist "consul_data" mkdir consul_data

REM 启动 Consul 开发模式
consul agent -dev ^
    -data-dir=./consul_data ^
    -node=consul-dev ^
    -bind=127.0.0.1 ^
    -client=0.0.0.0 ^
    -ui-config-enabled ^
    -log-level=INFO

echo Consul 已启动
echo Web UI: http://localhost:8500
pause