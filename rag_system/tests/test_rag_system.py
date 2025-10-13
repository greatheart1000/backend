"""
RAG系统测试脚本
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from services.rag_pipeline import rag_pipeline

def test_rag_pipeline():
    """测试RAG管道"""
    # 测试查询
    test_queries = [
        "什么是人工智能？",
        "如何学习Python编程？",
        "太阳系有哪些行星？"
    ]
    
    print("开始测试RAG系统...")
    
    for i, query in enumerate(test_queries, 1):
        print(f"\n--- 测试查询 {i}: {query} ---")
        
        # 处理查询
        result = rag_pipeline.process_query(query, f"test_session_{i}")
        
        # 输出结果
        print(f"查询: {result.get('query', 'N/A')}")
        print(f"答案: {result.get('answer', 'N/A')}")
        print(f"意图: {result.get('intent', 'N/A')}")
        if 'error' in result:
            print(f"错误: {result['error']}")
    
    print("\n测试完成!")

if __name__ == "__main__":
    test_rag_pipeline()