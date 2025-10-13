from services.rag_pipeline import rag_pipeline
import argparse

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="RAG知识库系统")
    parser.add_argument("--query", type=str, help="用户查询", required=True)
    parser.add_argument("--session_id", type=str, default="default", help="会话ID")
    
    args = parser.parse_args()
    
    # 处理查询
    result = rag_pipeline.process_query(args.query, args.session_id)
    
    # 输出结果
    print("\n=== RAG系统处理结果 ===")
    print(f"查询: {result['query']}")
    print(f"答案: {result['answer']}")
    
    if 'intent' in result:
        print(f"意图: {result['intent']}")
    
    if 'candidates_count' in result:
        print(f"候选文档数: {result['candidates_count']}")
        print(f"最终文档数: {result['final_docs_count']}")
    
    if result.get('from_cache'):
        print("结果来自缓存")

if __name__ == "__main__":
    main()