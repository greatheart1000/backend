import os

class Config:
    # Elasticsearch 配置
    ES_HOST = os.environ.get('ES_HOST', 'localhost')
    ES_PORT = int(os.environ.get('ES_PORT', 9200))
    ES_USER = os.environ.get('ES_USER', 'elastic')
    ES_PASSWORD = os.environ.get('ES_PASSWORD', 'changeme')
    ES_SCHEME = os.environ.get('ES_SCHEME', 'http')
    
    # Redis 配置
    REDIS_HOST = os.environ.get('REDIS_HOST', 'localhost')
    REDIS_PORT = int(os.environ.get('REDIS_PORT', 6379))
    REDIS_DB = int(os.environ.get('REDIS_DB', 0))
    
    # 索引名称
    STRUCTURED_INDEX = os.environ.get('STRUCTURED_INDEX', 'structured_data')
    UNSTRUCTURED_INDEX = os.environ.get('UNSTRUCTURED_INDEX', 'unstructured_data')
    
    # 向量模型配置
    VECTOR_MODEL = os.environ.get('VECTOR_MODEL', 'all-MiniLM-L6-v2')
    VECTOR_DIM = int(os.environ.get('VECTOR_DIM', 384))
    
    # 检索参数
    TOP_K = int(os.environ.get('TOP_K', 10))
    BM25_WEIGHT = float(os.environ.get('BM25_WEIGHT', 0.5))
    VECTOR_WEIGHT = float(os.environ.get('VECTOR_WEIGHT', 0.5))
    
    # 路径配置
    DATA_DIR = os.environ.get('DATA_DIR', './data')
    CACHE_DIR = os.environ.get('CACHE_DIR', './cache')

# 实例化配置对象
config = Config()