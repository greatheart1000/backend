@echo off
REM Windows批处理文件，用于在WSL环境中运行Python依赖修复脚本

echo 正在检查WSL是否已安装...

REM 检查wsl命令是否存在
wsl --version >nul 2>&1
if %errorlevel% neq 0 (
    echo 错误: 未找到WSL(Windows Subsystem for Linux)。
    echo 请先安装WSL，然后再运行此脚本。
    echo 安装方法: 以管理员身份运行PowerShell，执行 'wsl --install'
    pause
    exit /b 1
)

 echo WSL已安装，正在启动...

REM 运行WSL并执行修复脚本
wsl -d Ubuntu -e bash -c "cd /mnt/e/project/web3_learn/knowledgeRAG && chmod +x fix_python_deps.sh && sudo ./fix_python_deps.sh"

REM 检查命令执行结果
if %errorlevel% equ 0 (
    echo Python依赖修复脚本执行完成。
) else (
    echo 错误: Python依赖修复脚本执行失败。
)

pause