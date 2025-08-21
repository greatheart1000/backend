from elasticsearch import Elasticsearch
from elasticsearch.helpers import bulk
from sentence_transformers import SentenceTransformer
import redis
import numpy as np
import json
import time
from typing import List, Dict, Any, Union
from config import config

class ESClient:
    """Elasticsearch客户端封装"""
    def __init__(self):
        self.client = Elasticsearch(
            hosts=[f"{config.ES_SCHEME}://{config.ES_HOST}:{config.ES_PORT}"],
            basic_auth=(config.ES_USER, config.ES_PASSWORD),
            verify_certs=False,
            ssl_show_warn=False
        )
        
    def check_connection(self):
        """检查ES连接是否正常"""
        return self.client.ping()
        
    def create_index(self, index_name: str, mapping: Dict):
        """创建索引"""
        if self.client.indices.exists(index=index_name):
            self.client.indices.delete(index=index_name)
        self.client.indices.create(index=index_name, body={"mappings": mapping})
        
    def bulk_index(self, index_name: str, documents: List[Dict]):
        """批量索引文档"""
        actions = [
            {
                "_index": index_name,
                "_id": doc.get("id", str(i)),
                "_source": doc
            } for i, doc in enumerate(documents)
        ]
        bulk(self.client, actions)
        
    def search(self, index_name: str, query: Dict, size: int = 10):
        """执行搜索"""
        return self.client.search(index=index_name, body=query, size=size)
        
    def hybrid_search(self, index_name: str, text_query: str, vector: List[float], 
                      bm25_weight: float = 0.5, vector_weight: float = 0.5, size: int = 10):
        """执行混合搜索（BM25+向量）"""
        query = {
            "query": {
                "script_score": {
                    "query": {
                        "match": {
                            "content": {
                                "query": text_query,
                                "boost": bm25_weight
                            }
                        }
                    },
                    "script": {
                        "source": "cosineSimilarity(params.query_vector, 'vector') * params.vector_weight + _score",
                        "params": {
                            "query_vector": vector,
                            "vector_weight": vector_weight
                        }
                    }
                }
            }
        }
        return self.client.search(index=index_name, body=query, size=size)

class VectorEncoder:
    """向量编码器"""
    def __init__(self):
        self.model = SentenceTransformer(config.VECTOR_MODEL)
        
    def encode(self, texts: Union[str, List[str]]) -> Union[List[float], List[List[float]]]:
        """将文本转换为向量"""
        if isinstance(texts, str):
            return self.model.encode(texts).tolist()
        return self.model.encode(texts).tolist()

class RedisCache:
    """Redis缓存客户端"""
    def __init__(self):
        self.client = redis.Redis(
            host=config.REDIS_HOST,
            port=config.REDIS_PORT,
            db=config.REDIS_DB,
            decode_responses=True
        )
        
    def set(self, key: str, value: Any, expire: int = 3600):
        """设置缓存"""
        if isinstance(value, (dict, list)):
            value = json.dumps(value)
        self.client.set(key, value, ex=expire)
        
    def get(self, key: str) -> Any:
        """获取缓存"""
        value = self.client.get(key)
        if value is not None:
            try:
                return json.loads(value)
            except (json.JSONDecodeError, TypeError):
                return value
        return None
        
    def exists(self, key: str) -> bool:
        """检查缓存是否存在"""
        return self.client.exists(key)

# 实例化工具类
es_client = ESClient()
vector_encoder = VectorEncoder()
redis_cache = RedisCache()

# 工具函数
def timeit(func):
    """装饰器：记录函数执行时间"""
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        print(f"{func.__name__} executed in {end_time - start_time:.4f} seconds")
        return result
    return wrapper


def preprocess_text(text: str) -> str:
    """文本预处理"""
    # 这里可以根据具体需求添加更多预处理步骤
    text = text.lower().strip()
    # 移除特殊字符
    import re
    text = re.sub(r'[^\w\s]', '', text)
    return text