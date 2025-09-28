import os
from datetime import timedelta

class Config:
    """基础配置类"""
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'your-secret-key-here'
    
    # 负载均衡器配置
    LB_ALGORITHMS = [
        'round_robin',
        'weighted_round_robin', 
        'ip_hash',
        'least_connections',
        'consistent_hash',
        'fastest_response'
    ]
    
    # 默认后端服务器
    DEFAULT_BACKENDS = [
        {'id': 'backend-1', 'host': '127.0.0.1', 'port': 8081, 'weight': 1},
        {'id': 'backend-2', 'host': '127.0.0.1', 'port': 8082, 'weight': 2},
        {'id': 'backend-3', 'host': '127.0.0.1', 'port': 8083, 'weight': 1},
    ]
    
    # 健康检查配置
    HEALTH_CHECK_INTERVAL = 10  # 秒
    HEALTH_CHECK_TIMEOUT = 5    # 秒
    HEALTH_CHECK_PATH = '/health'
    
    # 会话配置
    SESSION_TIMEOUT = timedelta(hours=1)
    SESSION_COOKIE_NAME = 'LB_SESSION'
    
    # 熔断器配置
    CIRCUIT_BREAKER_FAILURE_THRESHOLD = 5
    CIRCUIT_BREAKER_TIMEOUT = 60  # 秒
    
    # 限流配置
    RATE_LIMIT_CAPACITY = 100
    RATE_LIMIT_REFILL_RATE = 10  # 每秒
    
    # Redis配置（可选）
    REDIS_URL = os.environ.get('REDIS_URL') or 'redis://localhost:6379/0'
    
    # 日志配置
    LOG_LEVEL = os.environ.get('LOG_LEVEL') or 'INFO'

class DevelopmentConfig(Config):
    """开发环境配置"""
    DEBUG = True
    
class ProductionConfig(Config):
    """生产环境配置"""
    DEBUG = False
    
class TestingConfig(Config):
    """测试环境配置"""
    TESTING = True
    WTF_CSRF_ENABLED = False

# 配置映射
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}