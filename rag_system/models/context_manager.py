from typing import List, Dict, Optional, Tuple
from sentence_transformers import SentenceTransformer
import numpy as np
import logging
from cache.cache_manager import cache_manager
from config.settings import settings

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ContextManager:
    def __init__(self):
        """初始化上下文管理器"""
        # 初始化嵌入模型
        self.embedding_model = SentenceTransformer(settings.EMBEDDING_MODEL)
        
        # 会话历史窗口大小
        self.window_size = settings.SESSION_WINDOW_SIZE
    
    def get_query_vector(self, query: str) -> np.ndarray:
        """
        将查询转换为向量表示
        
        Args:
            query: 用户查询
            
        Returns:
            np.ndarray: 查询向量
        """
        # 构建缓存键
        cache_key = f"query_vector:{hash(query)}"
        
        # 尝试从缓存获取结果
        cached_vector = cache_manager.get(cache_key)
        if cached_vector is not None:
            logger.info("从缓存获取查询向量")
            return cached_vector
        
        try:
            # 生成查询向量
            query_vector = self.embedding_model.encode(query)
            
            # 缓存结果
            cache_manager.set(cache_key, query_vector, settings.CACHE_EXPIRE_TIME)
            
            logger.info("查询向量生成完成")
            return query_vector
        except Exception as e:
            logger.error(f"查询向量生成失败: {e}")
            # 返回零向量作为备用
            return np.zeros(384)
    
    def get_session_history(self, session_id: str) -> List[Dict[str, str]]:
        """
        获取会话历史记录
        
        Args:
            session_id: 会话ID
            
        Returns:
            List[Dict]: 会话历史记录列表
        """
        # 构建缓存键
        cache_key = f"session_history:{session_id}"
        
        # 尝试从缓存获取结果
        history = cache_manager.get(cache_key)
        if history is not None:
            logger.info(f"从缓存获取会话历史，记录数: {len(history)}")
            return history
        
        # 如果缓存中没有，返回空列表
        return []
    
    def update_session_history(self, session_id: str, query: str, response: str) -> bool:
        """
        更新会话历史记录
        
        Args:
            session_id: 会话ID
            query: 用户查询
            response: 系统回复
            
        Returns:
            bool: 是否更新成功
        """
        # 获取当前会话历史
        history = self.get_session_history(session_id)
        
        # 添加新的交互记录
        history.append({
            "query": query,
            "response": response
        })
        
        # 保持窗口大小，移除最旧的记录
        if len(history) > self.window_size:
            history = history[-self.window_size:]
        
        # 构建缓存键
        cache_key = f"session_history:{session_id}"
        
        # 缓存更新后的会话历史
        return cache_manager.set(cache_key, history, settings.CACHE_EXPIRE_TIME)
    
    def get_contextual_query(self, query: str, session_id: str) -> str:
        """
        构建包含上下文的查询
        
        Args:
            query: 当前查询
            session_id: 会话ID
            
        Returns:
            str: 包含上下文的查询
        """
        # 获取会话历史
        history = self.get_session_history(session_id)
        
        # 如果没有历史记录，直接返回原查询
        if not history:
            return query
        
        # 构建上下文增强的查询
        context_parts = []
        for interaction in history[-3:]:  # 只使用最近3轮对话
            context_parts.append(f"Q: {interaction['query']}")
            context_parts.append(f"A: {interaction['response']}")
        
        context_parts.append(f"Current Q: {query}")
        
        # 组合上下文查询
        contextual_query = " ".join(context_parts)
        
        return contextual_query

# 全局上下文管理器实例
context_manager = ContextManager()