@echo off
REM Flask 服务启动脚本 (Windows)

echo === Flask Consul 服务发现演示 ===

REM 检查 Python
python --version >nul 2>&1
if errorlevel 1 (
    echo 错误: Python 未安装
    pause
    exit /b 1
)

REM 安装依赖
echo 安装 Python 依赖...
pip install -r requirements.txt

REM 检查 Consul 是否运行
echo 检查 Consul 是否运行...
curl -f http://localhost:8500/v1/status/leader >nul 2>&1
if errorlevel 1 (
    echo 警告: Consul 似乎没有运行在 localhost:8500
    echo 请先运行 scripts\start_consul.bat 启动 Consul
    echo 继续启动服务...
)

REM 启动用户服务
echo 启动用户服务 (端口 5001)...
cd user_service
start "用户服务" python main.py
cd ..

REM 等待服务启动
timeout /t 3 /nobreak >nul

REM 启动订单服务
echo 启动订单服务 (端口 5002)...
cd order_service
start "订单服务" python main.py
cd ..

REM 等待服务启动
timeout /t 3 /nobreak >nul

echo.
echo === 服务已启动 ===
echo 用户服务: http://localhost:5001
echo 订单服务: http://localhost:5002
echo Consul UI: http://localhost:8500
echo.
echo 运行客户端示例:
echo cd client_example ^&^& python main.py
echo.
echo 按任意键退出...
pause >nul