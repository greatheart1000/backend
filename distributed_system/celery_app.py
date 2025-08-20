# celery_app.py
from celery import Celery
import os

# 设置环境变量，指定消息代理和结果后端
os.environ.setdefault('CELERY_BROKER_URL', 'amqp://guest:guest@localhost:5672//')
os.environ.setdefault('CELERY_RESULT_BACKEND', 'redis://localhost:6379/0')

# 创建Celery实例
app = Celery('distributed_system',
             broker=os.environ.get('CELERY_BROKER_URL'),
             backend=os.environ.get('CELERY_RESULT_BACKEND'),
             include=['tasks'])  # 包含任务模块

# 配置Celery
app.conf.update(
    # 任务序列化格式
    task_serializer='json',
    # 结果序列化格式
    result_serializer='json',
    # 接受的内容类型
    accept_content=['json'],
    # 时区设置
    timezone='Asia/Shanghai',
    # 启用UTC
    enable_utc=True,
    # 任务结果过期时间
    result_expires=3600,  # 1小时
    # 任务执行超时时间
    task_time_limit=30,  # 30秒
    # 任务软超时时间
    task_soft_time_limit=20,  # 20秒
    # 工作进程预取任务数
    worker_prefetch_multiplier=4,
    # 任务默认队列
    task_default_queue='default',
    # 任务默认交换机
    task_default_exchange='default',
    # 任务默认路由键
    task_default_routing_key='default',
    # 任务默认优先级
    task_default_priority=5,
    # 任务默认重试延迟
    task_default_retry_delay=3,  # 3秒
    # 任务最大重试次数
    task_max_retries=3,
)

# 如果直接运行此脚本，启动Celery Worker
if __name__ == '__main__':
    app.start()