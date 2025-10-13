from typing import List, Dict, Tuple, Any
from elasticsearch import Elasticsearch
import numpy as np
import logging
from cache.cache_manager import cache_manager
from config.settings import settings

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DynamicRetriever:
    def __init__(self):
        """初始化动态检索器"""
        # 初始化Elasticsearch客户端
        self.es_client = Elasticsearch(
            [{"host": settings.ELASTICSEARCH_HOST, "port": settings.ELASTICSEARCH_PORT}],
            # 注意：在生产环境中需要配置认证信息
        )
        
        # 索引名称
        self.index_name = "rag_documents"
    
    def hybrid_search(self, query: str, query_vector: np.ndarray, 
                     bm25_weight: float, vector_weight: float) -> List[Dict[str, Any]]:
        """
        执行混合检索（BM25 + 向量检索）
        
        Args:
            query: 查询文本
            query_vector: 查询向量
            bm25_weight: BM25权重
            vector_weight: 向量权重
            
        Returns:
            List[Dict]: 检索结果列表
        """
        # 构建缓存键
        cache_key = f"hybrid_search:{hash(query)}:{bm25_weight}:{vector_weight}"
        
        # 尝试从缓存获取结果
        cached_results = cache_manager.get(cache_key)
        if cached_results is not None:
            logger.info(f"从缓存获取混合检索结果，数量: {len(cached_results)}")
            return cached_results
        
        # 构建混合检索查询
        script_query = {
            "script_score": {
                "query": {
                    "bool": {
                        "should": [
                            {
                                "match": {
                                    "content": {
                                        "query": query,
                                        "boost": 1.0
                                    }
                                }
                            },
                            {
                                "match": {
                                    "title": {
                                        "query": query,
                                        "boost": 0.5
                                    }
                                }
                            }
                        ]
                    }
                },
                "script": {
                    "source": f"""
                        double bm25_score = _score;
                        double vector_score = cosineSimilarity(params.query_vector, 'vector');
                        double combined_score = ({bm25_weight} * bm25_score) + ({vector_weight} * (1 + vector_score));
                        return combined_score;
                    """,
                    "params": {
                        "query_vector": query_vector.tolist()
                    }
                }
            }
        }
        
        # 执行检索
        try:
            response = self.es_client.search(
                index=self.index_name,
                body={
                    "size": settings.TOP_M_CANDIDATES,
                    "query": script_query,
                    "_source": {"excludes": ["vector"]}  # 不返回向量字段
                }
            )
            
            # 解析结果
            results = []
            for hit in response['hits']['hits']:
                results.append({
                    "id": hit["_id"],
                    "score": hit["_score"],
                    "source": hit["_source"]
                })
            
            # 缓存结果
            cache_manager.set(cache_key, results, settings.CACHE_EXPIRE_TIME)
            
            return results
        except Exception as e:
            logger.error(f"混合检索失败: {e}")
            return []
    
    def get_document_by_id(self, doc_id: str) -> Dict[str, Any]:
        """
        根据文档ID获取文档内容
        
        Args:
            doc_id: 文档ID
            
        Returns:
            Dict: 文档内容
        """
        try:
            response = self.es_client.get(
                index=self.index_name,
                id=doc_id
            )
            return response["_source"]
        except Exception as e:
            logger.error(f"获取文档失败: {e}")
            return {}
    
    def search_by_document_id(self, doc_id: str) -> List[Dict[str, Any]]:
        """
        根据文档ID搜索相关块
        
        Args:
            doc_id: 文档ID
            
        Returns:
            List[Dict]: 相关块列表
        """
        try:
            response = self.es_client.search(
                index=self.index_name,
                body={
                    "query": {
                        "term": {
                            "doc_id.keyword": doc_id
                        }
                    },
                    "sort": [
                        {
                            "chunk_level.keyword": {
                                "order": "asc"
                            }
                        },
                        {
                            "chunk_index": {
                                "order": "asc"
                            }
                        }
                    ]
                }
            )
            
            results = []
            for hit in response['hits']['hits']:
                results.append({
                    "id": hit["_id"],
                    "score": hit["_score"],
                    "source": hit["_source"]
                })
            
            return results
        except Exception as e:
            logger.error(f"按文档ID搜索失败: {e}")
            return []
    
    def get_document_context(self, doc_id: str, chunk_index: int, 
                           context_window: int = 2) -> List[Dict[str, Any]]:
        """
        获取文档上下文（相邻块）
        
        Args:
            doc_id: 文档ID
            chunk_index: 当前块索引
            context_window: 上下文窗口大小
            
        Returns:
            List[Dict]: 上下文块列表
        """
        try:
            # 搜索相邻的块
            start_index = max(0, chunk_index - context_window)
            end_index = chunk_index + context_window
            
            response = self.es_client.search(
                index=self.index_name,
                body={
                    "query": {
                        "bool": {
                            "must": [
                                {
                                    "term": {
                                        "doc_id.keyword": doc_id
                                    }
                                },
                                {
                                    "range": {
                                        "chunk_index": {
                                            "gte": start_index,
                                            "lte": end_index
                                        }
                                    }
                                }
                            ]
                        }
                    },
                    "sort": [
                        {
                            "chunk_index": {
                                "order": "asc"
                            }
                        }
                    ]
                }
            )
            
            results = []
            for hit in response['hits']['hits']:
                results.append({
                    "id": hit["_id"],
                    "score": hit["_score"],
                    "source": hit["_source"]
                })
            
            return results
        except Exception as e:
            logger.error(f"获取文档上下文失败: {e}")
            return []

    def index_document(self, doc_id: str, document: Dict[str, Any]) -> bool:
        """
        索引文档到Elasticsearch
        
        Args:
            doc_id: 文档ID
            document: 文档内容
            
        Returns:
            bool: 是否索引成功
        """
        try:
            self.es_client.index(
                index=self.index_name,
                id=doc_id,
                body=document
            )
            logger.info(f"文档 {doc_id} 索引成功")
            return True
        except Exception as e:
            logger.error(f"索引文档失败: {e}")
            return False
    
    def bulk_index_documents(self, documents: List[Tuple[str, Dict[str, Any]]]) -> bool:
        """
        批量索引文档到Elasticsearch
        
        Args:
            documents: 文档列表，格式为[(doc_id, document_content), ...]
            
        Returns:
            bool: 是否索引成功
        """
        try:
            actions = []
            for doc_id, document in documents:
                action = {
                    "_index": self.index_name,
                    "_id": doc_id,
                    "_source": document
                }
                actions.append(action)
            
            from elasticsearch.helpers import bulk
            bulk(self.es_client, actions)
            logger.info(f"批量索引 {len(documents)} 个文档成功")
            return True
        except Exception as e:
            logger.error(f"批量索引文档失败: {e}")
            return False

# 全局动态检索器实例
dynamic_retriever = DynamicRetriever()