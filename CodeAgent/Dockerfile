FROM python:3.10-slim

# 设置工作目录
WORKDIR /app

# 安装系统依赖（编译一些Python包需要）
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# 复制依赖文件
COPY requirements.txt .

# 安装Python依赖
RUN pip install --no-cache-dir -r requirements.txt

# 复制应用代码
COPY app.py .
COPY config.py .

# 暴露端口
EXPOSE 8000

# 设置环境变量（可选，有默认值）
ENV HOST=0.0.0.0
ENV PORT=8000
ENV LOG_LEVEL=INFO

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8000/health')" || exit 1

# 启动应用
CMD ["python", "app.py"]
