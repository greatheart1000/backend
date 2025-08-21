from typing import List, Dict, Any, Optional, Union
from utils import es_client, redis_cache, timeit, preprocess_text
from config import config
import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
import joblib
import os

class StructuredSearch:
    """结构化数据检索模块"""
    def __init__(self):
        self.index_name = config.STRUCTURED_INDEX
        self.synonym_dict = self._load_synonyms()
        self.rank_model = self._load_rank_model()
        self.scaler = self._load_scaler()
        
    def _load_synonyms(self) -> Dict[str, List[str]]:
        """加载同义词词典"""
        # 实际应用中可以从文件或数据库加载
        return {
            "手机": ["移动电话", "智能手机", "手机设备"],
            "电脑": ["计算机", "台式机", "笔记本"],
            "平板": ["平板电脑", "平板设备"],
            # 可以根据业务需求添加更多同义词
        }
        
    def _load_rank_model(self) -> Optional[LogisticRegression]:
        """加载排序模型"""
        model_path = os.path.join(config.CACHE_DIR, "structured_rank_model.pkl")
        if os.path.exists(model_path):
            return joblib.load(model_path)
        return None
        
    def _load_scaler(self) -> Optional[StandardScaler]:
        """加载特征缩放器"""
        scaler_path = os.path.join(config.CACHE_DIR, "structured_scaler.pkl")
        if os.path.exists(scaler_path):
            return joblib.load(scaler_path)
        return None
        
    def setup_index(self):
        """设置结构化数据索引"""
        # 结构化数据的映射定义，包含各种字段类型和索引优化
        mapping = {
            "properties": {
                "id": {"type": "keyword"},
                "title": {
                    "type": "text",
                    "analyzer": "ik_max_word",  # 假设使用中文分词器
                    "fields": {
                        "keyword": {"type": "keyword"}
                    },
                    "boost": 2.0  # 标题字段权重更高
                },
                "category": {
                    "type": "keyword",
                    "fields": {
                        "text": {"type": "text", "analyzer": "ik_smart"}
                    }
                },
                "brand": {"type": "keyword", "boost": 1.5},
                "price": {
                    "type": "double",
                    "fields": {
                        "keyword": {"type": "keyword"}
                    }
                },
                "stock": {"type": "integer"},
                "sales": {"type": "integer"},
                "rating": {"type": "double"},
                "description": {
                    "type": "text",
                    "analyzer": "ik_max_word",
                    "boost": 1.2
                },
                "created_at": {"type": "date"},
                "updated_at": {"type": "date"}
            }
        }
        es_client.create_index(self.index_name, mapping)
        
    def index_data(self, data: List[Dict]):
        """索引结构化数据"""
        # 对数据进行预处理
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
        
    @timeit
    def search(self, 
               query: str, 
               filters: Optional[Dict] = None, 
               sort_by: Optional[List[Dict]] = None, 
               size: int = 10, 
               use_cache: bool = True, 
               user_context: Optional[Dict] = None) -> List[Dict]:
        """结构化数据搜索"""
        # 生成缓存键
        cache_key = f"structured_search:{query}:{json.dumps(filters)}:{json.dumps(sort_by)}:{size}"
        if user_context:
            cache_key += f":{json.dumps(user_context)}"
        
        # 检查缓存
        if use_cache and redis_cache.exists(cache_key):
            return redis_cache.get(cache_key)
        
        # 查询预处理
        processed_query = preprocess_text(query)
        expanded_query = self.expand_query_with_synonyms(processed_query)
        
        # 构建查询
        search_body = {"query": {"bool": {}}}
        
        # 添加文本查询
        if expanded_query:
            search_body["query"]["bool"]["must"] = [
                {
                    "multi_match": {
                        "query": expanded_query,
                        "fields": [
                            "title^3",  # 标题权重最高
                            "description^2",
                            "category^1.5",
                            "brand"
                        ],
                        "type": "best_fields"
                    }
                }
            ]
        
        # 添加过滤器
        if filters:
            search_body["query"]["bool"]["filter"] = []
            
            # 处理价格范围过滤
            if "price_range" in filters:
                price_filter = {
                    "range": {
                        "price": {
                            "gte": filters["price_range"].get("min", 0),
                            "lte": filters["price_range"].get("max", float("inf"))
                        }
                    }
                }
                search_body["query"]["bool"]["filter"].append(price_filter)
            
            # 处理分类过滤
            if "categories" in filters and filters["categories"]:
                category_filter = {"terms": {"category": filters["categories"]}}
                search_body["query"]["bool"]["filter"].append(category_filter)
            
            # 处理品牌过滤
            if "brands" in filters and filters["brands"]:
                brand_filter = {"terms": {"brand": filters["brands"]}}
                search_body["query"]["bool"]["filter"].append(brand_filter)
            
            # 处理库存过滤
            if "in_stock" in filters and filters["in_stock"]:
                stock_filter = {"range": {"stock": {"gt": 0}}}
                search_body["query"]["bool"]["filter"].append(stock_filter)
            
        # 添加排序
        if sort_by:
            search_body["sort"] = sort_by
        else:
            # 默认排序：相关度得分 + 销量降序
            search_body["sort"] = [
                {"_score": {"order": "desc"}},
                {"sales": {"order": "desc"}}
            ]
        
        # 执行搜索
        results = es_client.search(self.index_name, search_body, size=size)
        
        # 提取结果
        hits = []
        for hit in results["hits"]["hits"]:
            source = hit["_source"]
            source["_score"] = hit["_score"]
            hits.append(source)
        
        # 如果有排序模型，使用模型进行二次排序
        if self.rank_model and hits:
            hits = self._rerank_with_model(hits, query, user_context)
        
        # 缓存结果
        if use_cache:
            redis_cache.set(cache_key, hits, expire=3600)
        
        return hits
        
    def _rerank_with_model(self, hits: List[Dict], query: str, user_context: Optional[Dict] = None) -> List[Dict]:
        """使用机器学习模型进行二次排序"""
        if not self.rank_model or not hits:
            return hits
        
        # 提取特征
        features = []
        for hit in hits:
            # 基础特征
            feature = [
                hit.get("price", 0),
                hit.get("sales", 0),
                hit.get("rating", 0),
                hit.get("stock", 0),
                hit.get("_score", 0),
                # 可以根据业务需求添加更多特征
            ]
            features.append(feature)
        
        # 特征缩放
        if self.scaler:
            features = self.scaler.transform(features)
        
        # 预测相关性分数
        scores = self.rank_model.predict_proba(features)[:, 1]
        
        # 根据预测分数重新排序
        scored_hits = [(score, hit) for score, hit in zip(scores, hits)]
        scored_hits.sort(key=lambda x: x[0], reverse=True)
        
        return [hit for _, hit in scored_hits]
        
    def train_rank_model(self, training_data: List[Dict]):
        """训练排序模型"""
        # 准备训练数据
        X = []
        y = []
        
        for item in training_data:
            # 特征
            features = [
                item.get("price", 0),
                item.get("sales", 0),
                item.get("rating", 0),
                item.get("stock", 0),
                item.get("_score", 0),
                # 可以添加更多特征
            ]
            X.append(features)
            
            # 标签 (1表示相关，0表示不相关)
            y.append(item.get("label", 0))
        
        # 特征缩放
        self.scaler = StandardScaler()
        X_scaled = self.scaler.fit_transform(X)
        
        # 训练逻辑回归模型
        self.rank_model = LogisticRegression()
        self.rank_model.fit(X_scaled, y)
        
        # 保存模型
        os.makedirs(config.CACHE_DIR, exist_ok=True)
        joblib.dump(self.rank_model, os.path.join(config.CACHE_DIR, "structured_rank_model.pkl"))
        joblib.dump(self.scaler, os.path.join(config.CACHE_DIR, "structured_scaler.pkl"))
        
        return self.rank_model

# 导入JSON模块
try:
    import json
except ImportError:
    import json