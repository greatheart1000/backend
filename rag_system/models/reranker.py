from typing import List, Dict, Any, Tuple
from sentence_transformers import CrossEncoder
import numpy as np
import logging
from cache.cache_manager import cache_manager
from config.settings import settings

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class Reranker:
    def __init__(self):
        """初始化精排器"""
        # 初始化交叉编码器模型
        self.cross_encoder = CrossEncoder(settings.RERANKER_MODEL)
    
    def reciprocal_rank_fusion(self, 
                              bm25_results: List[Dict[str, Any]], 
                              vector_results: List[Dict[str, Any]],
                              k: int = 60) -> List[Tuple[str, float]]:
        """
        执行倒数排名融合(RRF)
        
        Args:
            bm25_results: BM25检索结果
            vector_results: 向量检索结果
            k: 融合参数
            
        Returns:
            List[Tuple]: (文档ID, 融合得分) 列表，按得分降序排列
        """
        # 创建文档得分字典
        fused_scores = {}
        
        # 处理BM25结果
        for rank, result in enumerate(bm25_results):
            doc_id = result["id"]
            if doc_id not in fused_scores:
                fused_scores[doc_id] = 0
            fused_scores[doc_id] += 1 / (rank + k)
        
        # 处理向量检索结果
        for rank, result in enumerate(vector_results):
            doc_id = result["id"]
            if doc_id not in fused_scores:
                fused_scores[doc_id] = 0
            fused_scores[doc_id] += 1 / (rank + k)
        
        # 按得分排序
        sorted_scores = sorted(fused_scores.items(), key=lambda x: x[1], reverse=True)
        
        return sorted_scores
    
    def rerank(self, query: str, documents: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        使用交叉编码器对文档进行精排
        
        Args:
            query: 查询文本
            documents: 待精排的文档列表
            
        Returns:
            List[Dict]: 精排后的文档列表，按相关性得分降序排列
        """
        # 构建缓存键
        doc_ids = [doc["id"] for doc in documents]
        cache_key = f"rerank:{hash(query)}:{hash(str(sorted(doc_ids)))}"
        
        # 尝试从缓存获取结果
        cached_results = cache_manager.get(cache_key)
        if cached_results is not None:
            logger.info(f"从缓存获取精排结果，数量: {len(cached_results)}")
            return cached_results
        
        # 准备交叉编码器输入
        sentence_pairs = []
        for doc in documents:
            # 使用文档内容进行精排
            content = doc.get("source", {}).get("content", "")
            sentence_pairs.append([query, content])
        
        # 执行精排
        scores = self.cross_encoder.predict(sentence_pairs)
        
        # 将得分添加到文档中
        reranked_docs = []
        for i, doc in enumerate(documents):
            doc_copy = doc.copy()
            doc_copy["rerank_score"] = float(scores[i])
            reranked_docs.append(doc_copy)
        
        # 按精排得分排序
        reranked_docs.sort(key=lambda x: x["rerank_score"], reverse=True)
        
        # 只返回前K个结果
        top_k_docs = reranked_docs[:settings.TOP_K_RESULTS]
        
        # 缓存结果
        cache_manager.set(cache_key, top_k_docs, settings.CACHE_EXPIRE_TIME)
        
        logger.info(f"精排完成，返回 {len(top_k_docs)} 个文档")
        return top_k_docs

# 全局精排器实例
reranker = Reranker()