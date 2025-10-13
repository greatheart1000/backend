# 使用Python官方镜像作为基础镜像
FROM python:3.9-slim

# 设置工作目录
WORKDIR /app

# 复制依赖文件
COPY requirements.txt .

# 安装依赖
RUN pip install --no-cache-dir -r requirements.txt

# 复制项目代码
COPY . .

# 暴露端口（如果需要提供API服务）
EXPOSE 8000

# 设置环境变量
ENV REDIS_HOST=localhost
ENV REDIS_PORT=6379
ENV ELASTICSEARCH_HOST=localhost
ENV ELASTICSEARCH_PORT=9200

# 启动命令
CMD ["python", "app.py", "--query", "你好"]