# 多阶段构建，支持网络问题的备用方案
ARG PYTHON_IMAGE=python:3.9-slim
FROM ${PYTHON_IMAGE}

WORKDIR /app

# 配置pip镜像源以加速下载
RUN pip config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple/ && \
    pip config set global.trusted-host pypi.tuna.tsinghua.edu.cn

# 复制依赖文件
COPY requirements.txt .

# 安装依赖（使用缓存友好的方式）
RUN pip install --no-cache-dir -r requirements.txt || \
    pip install --no-cache-dir flask prometheus-client werkzeug

# 复制应用代码
COPY app.py .

# 创建非root用户
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# 暴露端口
EXPOSE 5000

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:5000/health')" || exit 1

# 启动应用
CMD ["python", "app.py"]