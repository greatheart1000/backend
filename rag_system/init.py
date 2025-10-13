"""
RAG系统初始化脚本
用于创建索引、导入数据等初始化操作
"""

from elasticsearch import Elasticsearch
from config.settings import settings
import json

def create_elasticsearch_index():
    """创建Elasticsearch索引"""
    es_client = Elasticsearch(
        [{"host": settings.ELASTICSEARCH_HOST, "port": settings.ELASTICSEARCH_PORT}]
    )
    
    # 定义索引映射，支持文档块结构
    index_mapping = {
        "mappings": {
            "properties": {
                "content": {
                    "type": "text",
                    "analyzer": "ik_max_word",  # 支持中文分词
                    "search_analyzer": "ik_smart"
                },
                "title": {
                    "type": "text",
                    "analyzer": "ik_max_word",
                    "search_analyzer": "ik_smart"
                },
                "doc_id": {
                    "type": "keyword"
                },
                "chunk_id": {
                    "type": "keyword"
                },
                "chunk_level": {
                    "type": "keyword"
                },
                "chunk_index": {
                    "type": "integer"
                },
                "length": {
                    "type": "integer"
                },
                "vector": {
                    "type": "dense_vector",
                    "dims": 384,  # 根据使用的嵌入模型调整维度
                    "index": True  # 启用向量索引
                },
                "metadata": {
                    "type": "object",
                    "enabled": True
                }
            }
        },
        "settings": {
            "analysis": {
                "analyzer": {
                    "ik_max_word": {
                        "type": "custom",
                        "tokenizer": "ik_max_word"
                    },
                    "ik_smart": {
                        "type": "custom",
                        "tokenizer": "ik_smart"
                    }
                }
            }
        }
    }
    
    # 创建索引
    try:
        if not es_client.indices.exists(index="rag_documents"):
            es_client.indices.create(
                index="rag_documents",
                body=index_mapping
            )
            print(f"索引 rag_documents 创建成功")
        else:
            print(f"索引 rag_documents 已存在")
    except Exception as e:
        print(f"创建索引失败: {e}")

def import_sample_data():
    """导入示例数据"""
    # 这里可以添加导入示例数据的逻辑
    # 例如从文件读取数据并索引到Elasticsearch
    print("示例数据导入完成")

if __name__ == "__main__":
    print("初始化RAG系统...")
    create_elasticsearch_index()
    import_sample_data()
    print("初始化完成")