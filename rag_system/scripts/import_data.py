#!/usr/bin/env python3
"""
数据导入脚本
用于将文档数据导入到Elasticsearch中
"""

import sys
import os
import json
import argparse
from typing import List, Dict, Any

# 添加项目路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from models.dynamic_retriever import DynamicRetriever
from documents.doc_processor import doc_processor

def load_data_from_json(file_path: str) -> List[Dict[str, Any]]:
    """从JSON文件加载数据"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return data
    except Exception as e:
        print(f"加载数据失败: {e}")
        return []

def load_data_from_text(file_path: str) -> List[Dict[str, Any]]:
    """从文本文件加载数据（每行一个文档）"""
    try:
        documents = []
        with open(file_path, 'r', encoding='utf-8') as f:
            for i, line in enumerate(f):
                line = line.strip()
                if line:
                    documents.append({
                        "id": f"doc_{i}",
                        "title": f"Document_{i}",
                        "content": line,
                        "metadata": {}
                    })
        return documents
    except Exception as e:
        print(f"加载数据失败: {e}")
        return []

def prepare_documents_for_indexing(documents: List[Dict[str, Any]]) -> List[tuple]:
    """准备文档用于索引"""
    prepared_docs = []
    
    for doc in documents:
        # 获取文档内容
        doc_id = doc.get("id", f"doc_{len(prepared_docs)}")
        content = doc.get("content", "")
        title = doc.get("title", f"Document_{len(prepared_docs)}")
        metadata = doc.get("metadata", {})
        
        # 处理文档（切分+向量化）
        print(f"处理文档: {title}")
        processed_chunks = doc_processor.process_document(doc_id, title, content, metadata)
        
        # 准备每个块用于索引
        for chunk in processed_chunks:
            chunk_id = f"{doc_id}_{chunk['chunk_id']}_{chunk['chunk_index']}"
            index_doc = {
                "content": chunk["content"],
                "title": chunk["title"],
                "doc_id": chunk["doc_id"],
                "chunk_id": chunk["chunk_id"],
                "chunk_level": chunk["level"],
                "chunk_index": chunk["chunk_index"],
                "length": chunk["length"],
                "vector": chunk.get("vector", []),
                "metadata": chunk["metadata"]
            }
            prepared_docs.append((chunk_id, index_doc))
    
    return prepared_docs

def import_data(file_path: str, file_type: str = "json"):
    """导入数据到Elasticsearch"""
    print(f"正在从 {file_path} 导入数据...")
    
    # 加载数据
    if file_type == "json":
        raw_documents = load_data_from_json(file_path)
    elif file_type == "text":
        raw_documents = load_data_from_text(file_path)
    else:
        print(f"不支持的文件类型: {file_type}")
        return False
    
    if not raw_documents:
        print("没有数据需要导入")
        return False
    
    print(f"加载了 {len(raw_documents)} 个文档")
    
    # 准备文档用于索引
    documents = prepare_documents_for_indexing(raw_documents)
    
    # 初始化检索器
    retriever = DynamicRetriever()
    
    # 批量索引文档
    success = retriever.bulk_index_documents(documents)
    
    if success:
        print(f"成功导入 {len(documents)} 个文档块")
        return True
    else:
        print("导入数据失败")
        return False

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="RAG系统数据导入工具")
    parser.add_argument("file_path", help="数据文件路径")
    parser.add_argument("--type", choices=["json", "text"], default="json", help="文件类型")
    
    args = parser.parse_args()
    
    # 检查文件是否存在
    if not os.path.exists(args.file_path):
        print(f"文件不存在: {args.file_path}")
        return 1
    
    # 导入数据
    success = import_data(args.file_path, args.type)
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())