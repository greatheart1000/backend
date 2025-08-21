@echo off
REM 知识图谱检索增强系统 - 运行示例脚本

setlocal enabledelayedexpansion

REM 检查Python是否安装
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo 错误: 未找到Python。请先安装Python并配置环境变量。
    pause
    exit /b 1
)

REM 检查requirements.txt是否存在
if not exist requirements.txt (
    echo 错误: 未找到requirements.txt文件。
    pause
    exit /b 1
)

REM 安装依赖
echo 正在安装依赖包...
pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo 错误: 依赖安装失败。
    pause
    exit /b 1
)

echo 依赖安装成功。

REM 运行示例代码
echo 正在运行示例代码...
python example_usage.py

REM 检查运行结果
if %errorlevel% neq 0 (
    echo 错误: 示例代码运行失败。
    pause
    exit /b 1
)

echo 示例代码运行完成。
pause