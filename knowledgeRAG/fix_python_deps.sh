#!/bin/bash
# 解决Ubuntu系统中Python依赖冲突问题的脚本
# 问题描述: python3-dbus 和 python3-gi 依赖 python3 (< 3.11)，但已安装 python3.12.3

# 确保以root权限运行
if [ "$EUID" -ne 0 ]
  then echo "请以root权限运行此脚本: sudo ./fix_python_deps.sh"
  exit
fi

# 更新系统包列表
echo "正在更新系统包列表..."
sudo apt update -y

# 安装Python 3.11
echo "正在安装Python 3.11..."
# 添加deadsnakes PPA源以获取Python 3.11
sudo add-apt-repository ppa:deadsnakes/ppa -y
sudo apt update -y
sudo apt install python3.11 python3.11-dev python3.11-distutils -y

# 安装update-alternatives工具(如果尚未安装)
sudo apt install alternatives -y

# 配置Python版本管理
echo "正在配置Python版本管理..."
sudo update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.12 1
sudo update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.11 2

echo "设置Python 3.11为默认版本..."
sudo update-alternatives --set python3 /usr/bin/python3.11

# 验证Python版本
echo "当前Python 3版本:"
python3 --version

# 安装pip for Python 3.11
echo "正在安装pip for Python 3.11..."
curl -sS https://bootstrap.pypa.io/get-pip.py | python3.11

# 尝试修复依赖关系
 echo "正在尝试修复依赖关系..."
sudo apt install -f -y

# 安装所需的包
 echo "正在安装python3-dbus和python3-gi..."
sudo apt install python3-dbus python3-gi -y

# 安装完成后检查
if [ $? -eq 0 ]; then
  echo "依赖包安装成功！"
  echo "解决Python依赖冲突问题完成。"
  echo "当前Python 3版本:"
  python3 --version
else
  echo "依赖包安装失败，请尝试其他解决方案。"
  exit 1
fi