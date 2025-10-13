from typing import Dict, Any, Tuple, List
import numpy as np
import logging
from models.intent_classifier import intent_classifier
from models.context_manager import context_manager
from models.dynamic_retriever import dynamic_retriever
from models.reranker import reranker
from models.answer_generator import answer_generator
from cache.cache_manager import cache_manager
from config.settings import settings

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class RAGPipeline:
    def __init__(self):
        """初始化RAG管道"""
        pass
    
    def process_query(self, query: str, session_id: str = "default") -> Dict[str, Any]:
        """
        处理用户查询的完整流程
        
        Args:
            query: 用户查询
            session_id: 会话ID
            
        Returns:
            Dict: 处理结果
        """
        try:
            logger.info(f"开始处理查询: {query}")
            
            # 阶段1：意图与权重分析
            logger.info("阶段1：意图与权重分析")
            intent, weights = intent_classifier.classify_intent(query)
            logger.info(f"识别意图: {intent}, 权重: {weights}")
            
            # 阶段2：向量化与会话管理
            logger.info("阶段2：向量化与会话管理")
            query_vector = context_manager.get_query_vector(query)
            session_history = context_manager.get_session_history(session_id)
            logger.info(f"获取查询向量和会话历史完成")
            
            # 构建缓存键检查最终答案缓存
            answer_cache_key = f"final_answer:{hash(query)}:{session_id}"
            cached_answer = cache_manager.get(answer_cache_key)
            if cached_answer:
                logger.info("从缓存中获取最终答案")
                return {
                    "query": query,
                    "answer": cached_answer,
                    "intent": intent,
                    "from_cache": True,
                    "cache_type": "exact_match"
                }
            
            # 如果精确匹配未命中，尝试语义相似度匹配
            logger.info("尝试语义相似度匹配")
            semantic_match = cache_manager.semantic_search(query_vector, threshold=0.95)
            if semantic_match:
                cache_key, cached_answer = semantic_match
                logger.info(f"通过语义相似度匹配找到答案: {cache_key}")
                return {
                    "query": query,
                    "answer": cached_answer,
                    "intent": intent,
                    "from_cache": True,
                    "cache_type": "semantic_similarity"
                }
            
            # 阶段3：混合检索（粗排）
            logger.info("阶段3：混合检索（粗排）")
            candidates = dynamic_retriever.hybrid_search(
                query, query_vector, 
                weights["bm25"], weights["vector"]
            )
            logger.info(f"检索到 {len(candidates)} 个候选文档")
            
            # 阶段4：精排与融合
            logger.info("阶段4：精排与融合")
            # 只对前TOP_K_RESULTS个文档进行精排
            top_candidates = candidates[:settings.TOP_M_CANDIDATES]
            reranked_docs = reranker.rerank(query, top_candidates)
            logger.info(f"精排完成，得到 {len(reranked_docs)} 个文档")
            
            # 阶段5：答案生成
            logger.info("阶段5：答案生成")
            answer = answer_generator.generate_answer(
                query, reranked_docs, query_vector, session_history
            )
            logger.info("答案生成完成")
            
            # 阶段6：结果返回与缓存
            logger.info("阶段6：结果返回与缓存")
            # 缓存最终答案
            cache_manager.set(answer_cache_key, answer, settings.CACHE_EXPIRE_TIME)
            
            # 更新会话历史
            context_manager.update_session_history(session_id, query, answer)
            
            return {
                "query": query,
                "answer": answer,
                "intent": intent,
                "from_cache": False,
                "candidates_count": len(candidates),
                "final_docs_count": len(reranked_docs)
            }
            
        except Exception as e:
            logger.error(f"处理查询时发生错误: {e}")
            return {
                "query": query,
                "answer": "抱歉，处理您的查询时发生了错误。",
                "error": str(e)
            }

# 全局RAG管道实例
rag_pipeline = RAGPipeline()