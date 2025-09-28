#!/bin/bash
# WSL环境下的系统设置脚本

echo "🐧 WSL环境下的登录监控系统部署脚本"
echo "================================================"

# 检查WSL版本
echo "📋 检查WSL环境信息："
echo "WSL版本: $(cat /proc/version)"
echo "发行版: $(lsb_release -d)"

# 更新系统包
echo ""
echo "📦 更新系统包..."
sudo apt update

# 安装必要工具
echo ""
echo "🔧 安装必要工具..."
sudo apt install -y curl wget git python3 python3-pip

# 检查Docker是否安装
echo ""
echo "🐳 检查Docker安装状态..."
if command -v docker &> /dev/null; then
    echo "✅ Docker已安装: $(docker --version)"
else
    echo "❌ Docker未安装，开始安装..."
    
    # 安装Docker
    curl -fsSL https://get.docker.com -o get-docker.sh
    sudo sh get-docker.sh
    
    # 将当前用户添加到docker组
    sudo usermod -aG docker $USER
    
    echo "⚠️  请注意：需要重新登录或运行 'newgrp docker' 以使Docker组权限生效"
fi

# 检查Docker Compose
echo ""
echo "🔗 检查Docker Compose..."
if command -v docker-compose &> /dev/null; then
    echo "✅ Docker Compose已安装: $(docker-compose --version)"
elif docker compose version &> /dev/null; then
    echo "✅ Docker Compose Plugin已安装: $(docker compose version)"
    echo "ℹ️  将使用 'docker compose' 替代 'docker-compose'"
    # 创建docker-compose的别名
    sudo ln -sf /usr/bin/docker /usr/local/bin/docker-compose
    echo '#!/bin/bash' | sudo tee /usr/local/bin/docker-compose > /dev/null
    echo 'docker compose "$@"' | sudo tee -a /usr/local/bin/docker-compose > /dev/null
    sudo chmod +x /usr/local/bin/docker-compose
else
    echo "❌ Docker Compose未安装，开始安装..."
    
    # 方法1: 尝试安装Docker Compose Plugin
    echo "  尝试安装Docker Compose Plugin..."
    sudo apt update
    sudo apt install -y docker-compose-plugin
    
    if docker compose version &> /dev/null; then
        echo "✅ Docker Compose Plugin安装成功"
        # 创建兼容性别名
        echo '#!/bin/bash' | sudo tee /usr/local/bin/docker-compose > /dev/null
        echo 'docker compose "$@"' | sudo tee -a /usr/local/bin/docker-compose > /dev/null
        sudo chmod +x /usr/local/bin/docker-compose
    else
        # 方法2: 手动安装docker-compose
        echo "  安装独立版Docker Compose..."
        COMPOSE_VERSION=$(curl -s https://api.github.com/repos/docker/compose/releases/latest | grep tag_name | cut -d '"' -f 4)
        sudo curl -L "https://github.com/docker/compose/releases/download/${COMPOSE_VERSION}/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
        sudo chmod +x /usr/local/bin/docker-compose
        
        if command -v docker-compose &> /dev/null; then
            echo "✅ Docker Compose安装完成: $(docker-compose --version)"
        else
            echo "❌ Docker Compose安装失败，请手动安装"
        fi
    fi
fi

# 启动Docker服务
echo ""
echo "🚀 启动Docker服务..."
sudo service docker start

# 检查Python环境
echo ""
echo "🐍 检查Python环境..."
python3 --version
pip3 --version

# 安装Python依赖
echo ""
echo "📚 安装Python依赖..."
if [ -f "requirements.txt" ]; then
    echo "  检查Python包管理方式..."
    
    # 检查是否有pipx
    if command -v pipx &> /dev/null; then
        echo "  使用pipx安装依赖..."
        pipx install flask prometheus-client
    # 检查是否可以使用apt安装
    elif [ -f "/etc/debian_version" ]; then
        echo "  使用apt安装Python包..."
        sudo apt update
        sudo apt install -y python3-flask python3-prometheus-client python3-requests
    # 使用虚拟环境
    else
        echo "  创建虚拟环境..."
        if ! python3 -m venv venv 2>/dev/null; then
            echo "  安装python3-venv..."
            sudo apt update
            sudo apt install -y python3-venv python3-full
        fi
        
        python3 -m venv venv
        source venv/bin/activate
        pip install -r requirements.txt
        echo "  虚拟环境创建完成: $(pwd)/venv"
    fi
    echo "✅ Python依赖安装完成"
else
    echo "⚠️  requirements.txt文件不存在，跳过Python依赖安装"
fi

# 检查端口占用
echo ""
echo "🔍 检查端口占用情况..."
ports=(5000 3000 9090 9093)
for port in "${ports[@]}"; do
    if netstat -tuln 2>/dev/null | grep ":$port " > /dev/null; then
        echo "⚠️  端口 $port 已被占用"
    else
        echo "✅ 端口 $port 可用"
    fi
done

# 设置WSL网络
echo ""
echo "🌐 WSL网络配置提示："
echo "- WSL2 IP地址: $(hostname -I | awk '{print $1}')"
echo "- 从Windows访问WSL服务，请使用: localhost:<端口号>"
echo "- 如需从外部访问，可能需要配置Windows防火墙"

echo ""
echo "✅ WSL环境设置完成！"
echo ""
echo "🚀 接下来可以运行："
echo "   ./start_wsl_system.sh    # 启动完整系统"
echo "   python3 app.py          # 仅启动Flask应用"
echo ""
echo "🔧 如果遇到docker-compose问题，请尝试："
echo "   docker compose --version  # 检查Docker Compose Plugin"
echo "   sudo apt install docker-compose-plugin  # 安装插件版本"
echo ""
echo "📱 访问地址（从Windows浏览器）："
echo "   Flask应用:    http://localhost:5000"
echo "   Grafana:      http://localhost:3000"
echo "   Prometheus:   http://localhost:9090"
echo "   Alertmanager: http://localhost:9093"