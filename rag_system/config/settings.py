import os
from typing import Optional

class Settings:
    # Redis配置
    REDIS_HOST: str = os.getenv("REDIS_HOST", "localhost")
    REDIS_PORT: int = int(os.getenv("REDIS_PORT", 6379))
    REDIS_DB: int = int(os.getenv("REDIS_DB", 0))
    REDIS_PASSWORD: Optional[str] = os.getenv("REDIS_PASSWORD", None)
    REDIS_CLUSTER_NODES: Optional[str] = os.getenv("REDIS_CLUSTER_NODES", None)  # 格式: "host1:port1,host2:port2"
    
    # Elasticsearch配置
    ELASTICSEARCH_HOST: str = os.getenv("ELASTICSEARCH_HOST", "localhost")
    ELASTICSEARCH_PORT: int = int(os.getenv("ELASTICSEARCH_PORT", 9200))
    
    # 模型配置
    EMBEDDING_MODEL: str = os.getenv("EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2")
    RERANKER_MODEL: str = os.getenv("RERANKER_MODEL", "BAAI/bge-reranker-base")
    INTENT_MODEL: str = os.getenv("INTENT_MODEL", "facebook/bart-large-mnli")
    
    # API配置
    QWEN_API_KEY: str = os.getenv("QWEN_API_KEY", "")
    QWEN_API_BASE: str = os.getenv("QWEN_API_BASE", "https://dashscope.aliyuncs.com/api/v1")
    
    # 缓存过期时间（秒）
    CACHE_EXPIRE_TIME: int = int(os.getenv("CACHE_EXPIRE_TIME", 3600))  # 1小时
    
    # 检索参数
    TOP_M_CANDIDATES: int = int(os.getenv("TOP_M_CANDIDATES", 100))
    TOP_K_RESULTS: int = int(os.getenv("TOP_K_RESULTS", 10))
    
    # 会话管理
    SESSION_WINDOW_SIZE: int = int(os.getenv("SESSION_WINDOW_SIZE", 5))  # 会话历史窗口大小

settings = Settings()