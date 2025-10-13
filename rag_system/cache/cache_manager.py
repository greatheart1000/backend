import redis
from redis.cluster import RedisCluster
import json
import pickle
import logging
from typing import Any, Optional, Union, List, Tuple
from config.settings import settings
import numpy as np

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class CacheManager:
    def __init__(self):
        """初始化Redis连接"""
        self.redis_client = None
        try:
            # 尝试连接Redis Cluster
            if hasattr(settings, 'REDIS_CLUSTER_NODES') and settings.REDIS_CLUSTER_NODES:
                startup_nodes = []
                for node in settings.REDIS_CLUSTER_NODES.split(','):
                    host, port = node.split(':')
                    startup_nodes.append({"host": host, "port": int(port)})
                
                self.redis_client = RedisCluster(
                    startup_nodes=startup_nodes,
                    decode_responses=False,
                    skip_full_coverage_check=True
                )
                logger.info("Redis Cluster连接成功")
            else:
                # 使用单节点Redis
                self.redis_client = redis.Redis(
                    host=settings.REDIS_HOST,
                    port=settings.REDIS_PORT,
                    db=settings.REDIS_DB,
                    password=settings.REDIS_PASSWORD,
                    decode_responses=False
                )
                logger.info("Redis单节点连接成功")
        except Exception as e:
            logger.error(f"Redis连接失败: {e}")
            raise
    
    def set(self, key: str, value: Any, expire: Optional[int] = None) -> bool:
        """
        设置缓存值
        
        Args:
            key: 缓存键
            value: 缓存值
            expire: 过期时间（秒）
            
        Returns:
            bool: 是否设置成功
        """
        try:
            serialized_value = pickle.dumps(value)
            result = self.redis_client.set(key, serialized_value, ex=expire or settings.CACHE_EXPIRE_TIME)
            return result
        except Exception as e:
            logger.error(f"设置缓存失败: {e}")
            return False
    
    def get(self, key: str) -> Optional[Any]:
        """
        获取缓存值
        
        Args:
            key: 缓存键
            
        Returns:
            缓存值，如果不存在则返回None
        """
        try:
            value = self.redis_client.get(key)
            if value is None:
                return None
            return pickle.loads(value)
        except Exception as e:
            logger.error(f"获取缓存失败: {e}")
            return None
    
    def delete(self, key: str) -> bool:
        """
        删除缓存值
        
        Args:
            key: 缓存键
            
        Returns:
            bool: 是否删除成功
        """
        try:
            result = self.redis_client.delete(key)
            return result > 0
        except Exception as e:
            logger.error(f"删除缓存失败: {e}")
            return False
    
    def exists(self, key: str) -> bool:
        """
        检查缓存键是否存在
        
        Args:
            key: 缓存键
            
        Returns:
            bool: 是否存在
        """
        try:
            return self.redis_client.exists(key) > 0
        except Exception as e:
            logger.error(f"检查缓存键失败: {e}")
            return False
    
    def semantic_search(self, query_vector: np.ndarray, threshold: float = 0.95) -> Optional[Tuple[str, Any]]:
        """
        基于语义相似度搜索缓存的答案
        
        Args:
            query_vector: 查询向量
            threshold: 相似度阈值
            
        Returns:
            Tuple[缓存键, 缓存值] 或 None
        """
        try:
            # 获取所有答案缓存键
            pattern = "final_answer:*"
            keys = []
            for key in self.redis_client.scan_iter(match=pattern):
                keys.append(key.decode('utf-8') if isinstance(key, bytes) else key)
            
            # 计算相似度
            for key in keys:
                # 获取对应的查询向量缓存键
                # 从final_answer:hash:session中提取hash部分
                parts = key.split(":")
                if len(parts) >= 2:
                    query_hash = parts[1]
                    vector_key = f"query_vector:{query_hash}"
                    
                    # 获取缓存的查询向量
                    cached_vector_data = self.redis_client.get(vector_key)
                    if cached_vector_data:
                        try:
                            cached_vector = pickle.loads(cached_vector_data)
                            # 计算余弦相似度
                            similarity = self._cosine_similarity(query_vector, cached_vector)
                            
                            # 如果相似度超过阈值，返回缓存的答案
                            if similarity >= threshold:
                                cached_answer = self.get(key)
                                if cached_answer:
                                    return (key, cached_answer)
                        except Exception as e:
                            logger.warning(f"处理缓存向量时出错: {e}")
                            continue
            
            return None
        except Exception as e:
            logger.error(f"语义搜索失败: {e}")
            return None
    
    def _cosine_similarity(self, vec1: np.ndarray, vec2: np.ndarray) -> float:
        """
        计算两个向量的余弦相似度
        
        Args:
            vec1: 向量1
            vec2: 向量2
            
        Returns:
            float: 余弦相似度
        """
        dot_product = np.dot(vec1, vec2)
        norm_vec1 = np.linalg.norm(vec1)
        norm_vec2 = np.linalg.norm(vec2)
        
        if norm_vec1 == 0 or norm_vec2 == 0:
            return 0.0
            
        return dot_product / (norm_vec1 * norm_vec2)
    
    def get_keys_by_pattern(self, pattern: str) -> List[str]:
        """
        根据模式获取所有匹配的键
        
        Args:
            pattern: 键模式
            
        Returns:
            List[str]: 匹配的键列表
        """
        try:
            keys = []
            for key in self.redis_client.scan_iter(match=pattern):
                keys.append(key.decode('utf-8') if isinstance(key, bytes) else key)
            return keys
        except Exception as e:
            logger.error(f"获取键列表失败: {e}")
            return []

# 全局缓存管理器实例
cache_manager = CacheManager()