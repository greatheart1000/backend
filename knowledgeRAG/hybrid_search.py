from typing import List, Dict, Any, Optional, Union, Tuple
from structured_search import StructuredSearch
from unstructured_search import UnstructuredSearch
from utils import redis_cache, timeit
from config import config
import numpy as np
import os

class HybridSearchSystem:
    """混合检索系统：整合结构化和非结构化数据检索"""
    def __init__(self):
        self.structured_search = StructuredSearch()
        self.unstructured_search = UnstructuredSearch()
        self.knowledge_graph = None  # 预留知识图谱接口
        
    def setup(self):
        """设置检索系统"""
        # 设置结构化数据索引
        self.structured_search.setup_index()
        
        # 设置非结构化数据索引
        self.unstructured_search.setup_index()
        
        # 确保缓存目录存在
        os.makedirs(config.CACHE_DIR, exist_ok=True)
        
    def index_structured_data(self, data: List[Dict]):
        """索引结构化数据"""
        self.structured_search.index_data(data)
        
    def index_unstructured_data(self, data: List[Dict]):
        """索引非结构化数据"""
        self.unstructured_search.index_data(data)
        
    @timeit
    def search(self, 
               query: str, 
               search_type: str = "all",  # all, structured, unstructured
               structured_params: Optional[Dict] = None,
               unstructured_params: Optional[Dict] = None,
               fusion_method: str = "reciprocal_rank",  # reciprocal_rank, weighted_score
               structured_weight: float = 0.5,
               unstructured_weight: float = 0.5,
               size: int = 10,
               use_cache: bool = True,
               user_context: Optional[Dict] = None) -> List[Dict]:
        """混合搜索入口"""
        # 生成缓存键
        cache_key = f"hybrid_search:{query}:{search_type}:{json.dumps(structured_params)}:{json.dumps(unstructured_params)}:{fusion_method}:{structured_weight}:{unstructured_weight}:{size}"
        if user_context:
            cache_key += f":{json.dumps(user_context)}"
        
        # 检查缓存
        if use_cache and redis_cache.exists(cache_key):
            return redis_cache.get(cache_key)
        
        results = []
        
        # 根据搜索类型执行不同的检索
        if search_type == "structured" or search_type == "all":
            # 结构化数据检索
            structured_results = self._search_structured(query, structured_params, size, use_cache, user_context)
            for result in structured_results:
                result["type"] = "structured"
            
            # 如果只搜索结构化数据，直接返回
            if search_type == "structured":
                results = structured_results[:size]
                if use_cache:
                    redis_cache.set(cache_key, results, expire=3600)
                return results
            
            results.extend(structured_results)
            
        if search_type == "unstructured" or search_type == "all":
            # 非结构化数据检索
            unstructured_results = self._search_unstructured(query, unstructured_params, size, use_cache)
            for result in unstructured_results:
                result["type"] = "unstructured"
            
            # 如果只搜索非结构化数据，直接返回
            if search_type == "unstructured":
                results = unstructured_results[:size]
                if use_cache:
                    redis_cache.set(cache_key, results, expire=3600)
                return results
            
            results.extend(unstructured_results)
            
        # 结果融合
        if results and search_type == "all":
            results = self._fuse_results(results, fusion_method, structured_weight, unstructured_weight, size)
        
        # 缓存结果
        if use_cache:
            redis_cache.set(cache_key, results, expire=3600)
        
        return results
        
    def _search_structured(self, 
                          query: str, 
                          params: Optional[Dict] = None,
                          size: int = 10,
                          use_cache: bool = True,
                          user_context: Optional[Dict] = None) -> List[Dict]:
        """执行结构化数据检索"""
        if params is None:
            params = {}
            
        filters = params.get("filters", None)
        sort_by = params.get("sort_by", None)
        
        return self.structured_search.search(
            query=query,
            filters=filters,
            sort_by=sort_by,
            size=size * 2,  # 获取更多结果用于融合
            use_cache=use_cache,
            user_context=user_context
        )
        
    def _search_unstructured(self, 
                            query: str, 
                            params: Optional[Dict] = None,
                            size: int = 10,
                            use_cache: bool = True) -> List[Dict]:
        """执行非结构化数据检索"""
        if params is None:
            params = {}
            
        use_bm25 = params.get("use_bm25", True)
        use_vector = params.get("use_vector", True)
        bm25_weight = params.get("bm25_weight", config.BM25_WEIGHT)
        vector_weight = params.get("vector_weight", config.VECTOR_WEIGHT)
        use_pseudo_feedback = params.get("use_pseudo_feedback", False)
        use_passage_search = params.get("use_passage_search", False)
        use_rerank = params.get("use_rerank", True)
        
        return self.unstructured_search.search(
            query=query,
            use_bm25=use_bm25,
            use_vector=use_vector,
            bm25_weight=bm25_weight,
            vector_weight=vector_weight,
            size=size * 2,  # 获取更多结果用于融合
            use_cache=use_cache,
            use_pseudo_feedback=use_pseudo_feedback,
            use_passage_search=use_passage_search,
            use_rerank=use_rerank
        )
        
    def _fuse_results(self, 
                     results: List[Dict], 
                     fusion_method: str, 
                     structured_weight: float, 
                     unstructured_weight: float, 
                     size: int) -> List[Dict]:
        """结果融合"""
        if fusion_method == "reciprocal_rank":
            #  reciprocal rank fusion
            return self._reciprocal_rank_fusion(results, size)
        elif fusion_method == "weighted_score":
            # 加权分数融合
            return self._weighted_score_fusion(results, structured_weight, unstructured_weight, size)
        else:
            # 默认使用加权分数融合
            return self._weighted_score_fusion(results, structured_weight, unstructured_weight, size)
            
    def _reciprocal_rank_fusion(self, results: List[Dict], size: int) -> List[Dict]:
        """Reciprocal Rank Fusion (RRF)结果融合算法"""
        # 为每种类型的结果单独排序
        structured_results = [r for r in results if r["type"] == "structured"]
        unstructured_results = [r for r in results if r["type"] == "unstructured"]
        
        # 对每种类型的结果按分数排序
        structured_results.sort(key=lambda x: x.get("_score", 0), reverse=True)
        unstructured_results.sort(key=lambda x: x.get("_score", 0), reverse=True)
        
        # 计算每个文档的RRF分数
        rrf_scores = {}
        k = 60  # RRF参数
        
        # 结构化结果的RRF分数
        for i, result in enumerate(structured_results):
            doc_id = result.get("id", str(i))
            rrf_score = 1.0 / (k + i + 1)
            if doc_id in rrf_scores:
                rrf_scores[doc_id]["score"] += rrf_score
                rrf_scores[doc_id]["doc"].setdefault("structured_rank", i+1)
            else:
                result_copy = result.copy()
                result_copy["structured_rank"] = i+1
                rrf_scores[doc_id] = {"score": rrf_score, "doc": result_copy}
        
        # 非结构化结果的RRF分数
        for i, result in enumerate(unstructured_results):
            doc_id = result.get("id", str(i))
            rrf_score = 1.0 / (k + i + 1)
            if doc_id in rrf_scores:
                rrf_scores[doc_id]["score"] += rrf_score
                rrf_scores[doc_id]["doc"].setdefault("unstructured_rank", i+1)
            else:
                result_copy = result.copy()
                result_copy["unstructured_rank"] = i+1
                rrf_scores[doc_id] = {"score": rrf_score, "doc": result_copy}
        
        # 按RRF分数排序并返回结果
        fused_results = sorted(rrf_scores.values(), key=lambda x: x["score"], reverse=True)
        return [item["doc"] for item in fused_results[:size]]
        
    def _weighted_score_fusion(self, 
                              results: List[Dict], 
                              structured_weight: float, 
                              unstructured_weight: float, 
                              size: int) -> List[Dict]:
        """加权分数融合"""
        # 标准化分数
        structured_scores = [r.get("_score", 0) for r in results if r["type"] == "structured"]
        unstructured_scores = [r.get("_score", 0) for r in results if r["type"] == "unstructured"]
        
        # 计算最大分数用于标准化
        max_structured_score = max(structured_scores) if structured_scores else 1
        max_unstructured_score = max(unstructured_scores) if unstructured_scores else 1
        
        # 对每个结果计算加权分数
        scored_results = []
        for result in results:
            result_copy = result.copy()
            raw_score = result_copy.get("_score", 0)
            
            # 标准化分数
            if result_copy["type"] == "structured":
                normalized_score = raw_score / max_structured_score if max_structured_score > 0 else 0
                weighted_score = normalized_score * structured_weight
            else:
                normalized_score = raw_score / max_unstructured_score if max_unstructured_score > 0 else 0
                weighted_score = normalized_score * unstructured_weight
            
            result_copy["normalized_score"] = normalized_score
            result_copy["weighted_score"] = weighted_score
            scored_results.append((weighted_score, result_copy))
        
        # 按加权分数排序并返回结果
        scored_results.sort(key=lambda x: x[0], reverse=True)
        return [item[1] for item in scored_results[:size]]
        
    def advanced_search(self, 
                       query: str, 
                       structured_filters: Optional[Dict] = None,
                       unstructured_options: Optional[Dict] = None,
                       knowledge_graph_boost: bool = False,
                       size: int = 10) -> List[Dict]:
        """高级搜索：结合多种检索技术"""
        # 首先执行混合搜索
        results = self.search(
            query=query,
            search_type="all",
            structured_params={"filters": structured_filters},
            unstructured_params=unstructured_options,
            size=size * 2  # 获取更多结果用于知识图谱增强
        )
        
        # 如果启用知识图谱增强
        if knowledge_graph_boost and self.knowledge_graph:
            results = self._enhance_with_knowledge_graph(results, query)
        
        # 截断结果
        return results[:size]
        
    def _enhance_with_knowledge_graph(self, results: List[Dict], query: str) -> List[Dict]:
        """使用知识图谱增强检索结果"""
        # 实际应用中，这里会调用知识图谱服务
        # 此处仅作为示例框架
        enhanced_results = results.copy()
        
        # 模拟知识图谱增强：为包含特定实体的文档增加分数
        for result in enhanced_results:
            content = " ".join([str(v) for v in result.values() if isinstance(v, str)])
            # 简单模拟：如果文档包含查询中的关键词，则增加分数
            if query.lower() in content.lower():
                if "weighted_score" in result:
                    result["weighted_score"] *= 1.1
                elif "_score" in result:
                    result["_score"] *= 1.1
        
        # 重新排序
        if all("weighted_score" in r for r in enhanced_results):
            enhanced_results.sort(key=lambda x: x["weighted_score"], reverse=True)
        else:
            enhanced_results.sort(key=lambda x: x.get("_score", 0), reverse=True)
        
        return enhanced_results
        
    def batch_search(self, 
                    queries: List[Dict], 
                    size: int = 10) -> List[Dict]:
        """批量搜索接口"""
        results = []
        
        for query_info in queries:
            query = query_info["query"]
            search_type = query_info.get("search_type", "all")
            
            query_results = self.search(
                query=query,
                search_type=search_type,
                size=size
            )
            
            results.append({
                "query": query,
                "results": query_results
            })
        
        return results

# 导入必要的模块
try:
    import json
except ImportError:
    import json