from typing import List, Dict, Any, Optional, Union, Tuple
from utils import es_client, vector_encoder, redis_cache, timeit, preprocess_text
from config import config
import numpy as np
import pandas as pd
from transformers import AutoTokenizer, AutoModelForSequenceClassification
import torch
import os
import re

class UnstructuredSearch:
    """非结构化数据检索模块"""
    def __init__(self):
        self.index_name = config.UNSTRUCTURED_INDEX
        self.vector_dim = config.VECTOR_DIM
        self.synonym_dict = self._load_synonyms()
        self.cross_encoder = self._load_cross_encoder()
        self.passage_size = 200  # 段落大小（字符数）
        
    def _load_synonyms(self) -> Dict[str, List[str]]:
        """加载同义词词典"""
        # 实际应用中可以从文件或数据库加载
        return {
            "人工智能": ["AI", "机器学习", "深度学习"],
            "大数据": ["数据分析", "数据挖掘", "数据处理"],
            "云计算": ["云服务", "云平台", "云存储"],
            # 可以根据业务需求添加更多同义词
        }
        
    def _load_cross_encoder(self) -> Optional[Any]:
        """加载Cross-Encoder模型"""
        try:
            from sentence_transformers import CrossEncoder
            # 使用轻量级的Cross-Encoder模型
            return CrossEncoder('cross-encoder/ms-marco-MiniLM-L-6-v2')
        except ImportError:
            print("Cross-Encoder not available, will skip reranking")
            return None
        
    def setup_index(self):
        """设置非结构化数据索引"""
        # 非结构化数据的映射定义，包含文本字段和向量字段
        mapping = {
            "properties": {
                "id": {"type": "keyword"},
                "title": {
                    "type": "text",
                    "analyzer": "ik_max_word",
                    "boost": 2.0
                },
                "content": {
                    "type": "text",
                    "analyzer": "ik_max_word"
                },
                "vector": {
                    "type": "dense_vector",
                    "dims": self.vector_dim,
                    "index": True,
                    "similarity": "cosine"
                },
                "passages": {
                    "type": "nested",
                    "properties": {
                        "text": {
                            "type": "text",
                            "analyzer": "ik_max_word"
                        },
                        "vector": {
                            "type": "dense_vector",
                            "dims": self.vector_dim,
                            "index": True,
                            "similarity": "cosine"
                        },
                        "position": {"type": "integer"}
                    }
                },
                "source": {"type": "keyword"},
                "created_at": {"type": "date"},
                "updated_at": {"type": "date"}
            }
        }
        es_client.create_index(self.index_name, mapping)
        
    def _split_into_passages(self, text: str) -> List[str]:
        """将长文本切分为段落"""
        # 按句号、问号、感叹号等标点符号分割
        sentences = re.split(r'[。！？.!?]', text)
        passages = []
        current_passage = ""
        
        for sentence in sentences:
            if not sentence.strip():
                continue
            
            # 如果当前段落加上新句子超过指定大小，则保存当前段落
            if len(current_passage) + len(sentence) > self.passage_size:
                if current_passage:
                    passages.append(current_passage)
                current_passage = sentence
            else:
                if current_passage:
                    current_passage += "。" + sentence
                else:
                    current_passage = sentence
        
        # 添加最后一个段落
        if current_passage:
            passages.append(current_passage)
        
        return passages
        
    def index_data(self, data: List[Dict]):
        """索引非结构化数据"""
        processed_data = []
        
        for item in data:
            processed_item = item.copy()
            
            # 添加默认字段
            if "id" not in processed_item:
                processed_item["id"] = str(hash(frozenset(processed_item.items())))
            if "created_at" not in processed_item:
                import datetime
                processed_item["created_at"] = datetime.datetime.now().isoformat()
            if "updated_at" not in processed_item:
                processed_item["updated_at"] = datetime.datetime.now().isoformat()
            
            # 生成文档向量
            content = processed_item.get("content", "")
            if content:
                processed_item["vector"] = vector_encoder.encode(content)
                
                # 生成段落级数据
                passages = self._split_into_passages(content)
                if passages:
                    passage_vectors = vector_encoder.encode(passages)
                    processed_item["passages"] = [
                        {
                            "text": passage,
                            "vector": vector,
                            "position": i
                        } for i, (passage, vector) in enumerate(zip(passages, passage_vectors))
                    ]
            
            processed_data.append(processed_item)
        
        es_client.bulk_index(self.index_name, processed_data)
        
    def expand_query_with_synonyms(self, query: str) -> str:
        """使用同义词扩展查询"""
        words = query.split()
        expanded_words = []
        for word in words:
            expanded_words.append(word)
            if word in self.synonym_dict:
                expanded_words.extend(self.synonym_dict[word])
        return " ".join(set(expanded_words))
        
    def _extract_key_terms_from_docs(self, docs: List[Dict], top_n: int = 5) -> List[str]:
        """从文档中提取关键术语用于伪反馈"""
        # 简单实现：统计词频
        from collections import Counter
        import jieba
        
        word_counter = Counter()
        for doc in docs:
            content = doc.get("_source", {}).get("content", "")
            if content:
                words = jieba.lcut_for_search(content)  # 使用搜索引擎模式分词
                # 过滤停用词和短词
                filtered_words = [word for word in words if len(word) > 1]
                word_counter.update(filtered_words)
        
        # 返回词频最高的top_n个词
        return [word for word, _ in word_counter.most_common(top_n)]
        
    def pseudo_relevance_feedback(self, query: str, initial_docs: List[Dict], top_n_terms: int = 3) -> str:
        """伪相关性反馈：使用初始检索结果扩展查询"""
        if not initial_docs:
            return query
        
        # 从初始文档中提取关键术语
        key_terms = self._extract_key_terms_from_docs(initial_docs, top_n=top_n_terms)
        
        # 扩展查询
        expanded_query = query + " " + " ".join(key_terms)
        return expanded_query
        
    @timeit
    def search(self, 
               query: str, 
               use_bm25: bool = True, 
               use_vector: bool = True, 
               bm25_weight: float = config.BM25_WEIGHT, 
               vector_weight: float = config.VECTOR_WEIGHT, 
               size: int = 10, 
               use_cache: bool = True, 
               use_pseudo_feedback: bool = False, 
               use_passage_search: bool = False, 
               use_rerank: bool = False) -> List[Dict]:
        """非结构化数据搜索"""
        # 生成缓存键
        cache_key = f"unstructured_search:{query}:{use_bm25}:{use_vector}:{bm25_weight}:{vector_weight}:{size}:{use_pseudo_feedback}:{use_passage_search}:{use_rerank}"
        
        # 检查缓存
        if use_cache and redis_cache.exists(cache_key):
            return redis_cache.get(cache_key)
        
        # 查询预处理
        processed_query = preprocess_text(query)
        expanded_query = self.expand_query_with_synonyms(processed_query)
        
        # 如果使用伪反馈，先执行一次初步搜索
        if use_pseudo_feedback:
            # 先执行一次简单搜索获取初始结果
            initial_query = {
                "query": {
                    "match": {
                        "content": expanded_query
                    }
                }
            }
            initial_results = es_client.search(self.index_name, initial_query, size=5)
            initial_docs = initial_results["hits"]["hits"]
            
            # 使用伪反馈扩展查询
            expanded_query = self.pseudo_relevance_feedback(expanded_query, initial_docs)
        
        # 生成查询向量
        query_vector = vector_encoder.encode(expanded_query)
        
        # 根据配置选择搜索方式
        if use_bm25 and use_vector:
            # 混合搜索
            results = es_client.hybrid_search(
                self.index_name, 
                expanded_query, 
                query_vector, 
                bm25_weight, 
                vector_weight, 
                size=size * 2  # 获取更多结果用于可能的重排序
            )
        elif use_bm25:
            # 仅使用BM25
            query_body = {
                "query": {
                    "match": {
                        "content": expanded_query
                    }
                }
            }
            results = es_client.search(self.index_name, query_body, size=size * 2)
        elif use_vector:
            # 仅使用向量检索
            query_body = {
                "query": {
                    "script_score": {
                        "query": {"match_all": {}},
                        "script": {
                            "source": "cosineSimilarity(params.query_vector, 'vector') + 1.0",
                            "params": {
                                "query_vector": query_vector
                            }
                        }
                    }
                }
            }
            results = es_client.search(self.index_name, query_body, size=size * 2)
        else:
            # 默认使用BM25
            query_body = {
                "query": {
                    "match": {
                        "content": expanded_query
                    }
                }
            }
            results = es_client.search(self.index_name, query_body, size=size * 2)
        
        # 提取结果
        hits = []
        for hit in results["hits"]["hits"]:
            source = hit["_source"]
            source["_score"] = hit["_score"]
            hits.append(source)
        
        # 如果启用重排序且有Cross-Encoder模型
        if use_rerank and self.cross_encoder and hits:
            hits = self._rerank_with_cross_encoder(hits, query, size)
        elif len(hits) > size:
            # 否则截断结果
            hits = hits[:size]
        
        # 缓存结果
        if use_cache:
            redis_cache.set(cache_key, hits, expire=3600)
        
        return hits
        
    def _rerank_with_cross_encoder(self, docs: List[Dict], query: str, size: int) -> List[Dict]:
        """使用Cross-Encoder进行重排序"""
        if not self.cross_encoder or not docs:
            return docs
        
        # 准备重排序的输入对
        input_pairs = []
        for doc in docs:
            # 使用文档标题+内容作为输入
            doc_text = doc.get("title", "") + " " + doc.get("content", "")
            # 截断过长的文本
            if len(doc_text) > 512:
                doc_text = doc_text[:512]
            input_pairs.append([query, doc_text])
        
        # 获取重排序分数
        with torch.no_grad():
            scores = self.cross_encoder.predict(input_pairs)
        
        # 根据分数重新排序文档
        scored_docs = [(scores[i], doc) for i, doc in enumerate(docs)]
        scored_docs.sort(key=lambda x: x[0], reverse=True)
        
        # 返回排序后的文档（截断到指定大小）
        return [doc for _, doc in scored_docs[:size]]
        
    def search_passages(self, query: str, size: int = 10) -> List[Dict]:
        """段落级搜索"""
        # 生成查询向量
        query_vector = vector_encoder.encode(query)
        
        # 构建嵌套查询，搜索段落
        query_body = {
            "query": {
                "nested": {
                    "path": "passages",
                    "query": {
                        "script_score": {
                            "query": {
                                "match": {
                                    "passages.text": query
                                }
                            },
                            "script": {
                                "source": "cosineSimilarity(params.query_vector, 'passages.vector') + 1.0",
                                "params": {
                                    "query_vector": query_vector
                                }
                            }
                        }
                    },
                    "inner_hits": {
                        "size": size,
                        "sort": [{"_score": {"order": "desc"}}]
                    }
                }
            }
        }
        
        results = es_client.search(self.index_name, query_body, size=size)
        
        # 提取段落结果
        passage_hits = []
        for doc in results["hits"]["hits"]:
            if "inner_hits" in doc and "passages" in doc["inner_hits"]:
                for passage in doc["inner_hits"]["passages"]["hits"]:
                    passage_info = passage["_source"].copy()
                    passage_info["doc_id"] = doc["_id"]
                    passage_info["doc_title"] = doc["_source"].get("title", "")
                    passage_info["_score"] = passage["_score"]
                    passage_hits.append(passage_info)
        
        # 按分数排序并截断
        passage_hits.sort(key=lambda x: x["_score"], reverse=True)
        return passage_hits[:size]

# 导入必要的模块
try:
    import json
except ImportError:
    import json