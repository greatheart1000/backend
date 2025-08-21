#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
知识图谱检索增强系统 - 使用示例

这个示例文件演示了如何同时使用结构化和非结构化数据进行检索，
以及如何应用各种优化技术来提高检索召回准确率。
"""

from structured_search import StructuredSearch
from unstructured_search import UnstructuredSearch
from hybrid_search import HybridSearchSystem
from utils import es_client, vector_encoder, redis_cache
import time
import json
from typing import List, Dict


def setup_environment():
    """设置环境，确保ES和Redis连接正常"""
    print("正在检查环境...")
    
    # 检查ES连接
    if not es_client.check_connection():
        print("错误: 无法连接到Elasticsearch服务。请确保服务已启动并且配置正确。")
        return False
    print("✓ Elasticsearch连接成功")
    
    # 检查Redis连接
    try:
        redis_cache.client.ping()
        print("✓ Redis连接成功")
    except Exception as e:
        print(f"错误: 无法连接到Redis服务: {str(e)}")
        return False
    
    print("环境检查完成")
    return True


def create_sample_data():
    """创建示例数据"""
    print("正在创建示例数据...")
    
    # 结构化数据示例 - 电子产品
    structured_data = [
        {
            "id": "prod_001",
            "title": "iPhone 14 Pro 256GB 暗紫色",
            "category": "手机",
            "brand": "Apple",
            "price": 8999.00,
            "stock": 156,
            "sales": 2856,
            "rating": 4.8,
            "description": "iPhone 14 Pro搭载A16仿生芯片，超视网膜XDR显示屏，全天候显示功能，4800万像素主摄，支持车祸检测。"
        },
        {
            "id": "prod_002",
            "title": "华为 Mate 60 Pro 512GB 黑色",
            "category": "手机",
            "brand": "华为",
            "price": 6999.00,
            "stock": 320,
            "sales": 4210,
            "rating": 4.7,
            "description": "华为Mate 60 Pro支持卫星通话，搭载麒麟9000S芯片，鸿蒙操作系统，5000万像素超光变摄像头。"
        },
        {
            "id": "prod_003",
            "title": "小米14 Pro 16GB+512GB 钛合金版",
            "category": "手机",
            "brand": "小米",
            "price": 5799.00,
            "stock": 210,
            "sales": 3124,
            "rating": 4.6,
            "description": "小米14 Pro搭载骁龙8 Gen 3处理器，徕卡光学镜头，索尼IMX989主摄，120W有线快充。"
        },
        {
            "id": "prod_004",
            "title": "MacBook Pro 14英寸 M3 Pro芯片",
            "category": "电脑",
            "brand": "Apple",
            "price": 15999.00,
            "stock": 78,
            "sales": 532,
            "rating": 4.9,
            "description": "MacBook Pro 14英寸配备M3 Pro芯片，16GB统一内存，512GB固态硬盘，Liquid视网膜XDR显示屏。"
        },
        {
            "id": "prod_005",
            "title": "华为 MateBook X Pro 13.9英寸",
            "category": "电脑",
            "brand": "华为",
            "price": 8999.00,
            "stock": 120,
            "sales": 856,
            "rating": 4.5,
            "description": "华为MateBook X Pro搭载第12代英特尔酷睿i7处理器，16GB内存，512GB固态硬盘，3.1K原色全面屏。"
        }
    ]
    
    # 非结构化数据示例 - 产品评测和技术文章
    unstructured_data = [
        {
            "id": "doc_001",
            "title": "iPhone 14 Pro深度评测：专业摄影新标杆",
            "content": "iPhone 14 Pro在摄影方面的提升是显著的。4800万像素主摄带来了更高的解析力和细节表现，全新的光像引擎让低光拍摄能力大幅提升。A16芯片的算力提升不仅体现在性能上，也为摄影系统提供了更强大的图像处理能力。不过，价格仍然是高端定位，适合专业用户和摄影爱好者。",
            "source": "科技评测网"
        },
        {
            "id": "doc_002",
            "title": "华为Mate 60 Pro体验：突破与创新",
            "content": "华为Mate 60 Pro的推出标志着华为在高端手机市场的强势回归。卫星通话功能在紧急情况下非常实用，麒麟芯片的性能表现也令人满意。鸿蒙系统的流畅度和生态整合度不断提升，但在第三方应用适配方面仍有进步空间。整体而言，这是一款具有里程碑意义的产品。",
            "source": "数码前沿"
        },
        {
            "id": "doc_003",
            "title": "2024年智能手机选购指南",
            "content": "在选择智能手机时，需要考虑多个因素。处理器性能决定了手机的流畅度和多任务处理能力，相机系统则影响拍照和视频质量，电池续航和充电速度关系到日常使用体验。此外，操作系统、存储空间、屏幕素质和品牌生态也是重要考量。不同预算和需求的用户应根据自身情况选择合适的产品。",
            "source": "消费电子周刊"
        },
        {
            "id": "doc_004",
            "title": "MacBook Pro M3系列对比：如何选择适合你的型号",
            "content": "苹果最新的MacBook Pro M3系列提供了M3、M3 Pro和M3 Max三种芯片选择。对于一般办公和轻度创作，基础版M3已经足够；专业创作者和工程师则应考虑M3 Pro或M3 Max，以获得更强的多核心性能和图形处理能力。内存配置建议至少16GB，存储容量根据个人需求选择。",
            "source": "苹果科技网"
        },
        {
            "id": "doc_005",
            "title": "人工智能在手机摄影中的应用",
            "content": "近年来，人工智能技术在手机摄影领域的应用越来越广泛。AI场景识别、智能HDR、人像模式优化、夜间模式增强等功能都离不开人工智能算法的支持。通过机器学习，手机能够自动识别拍摄场景并进行针对性优化，让普通用户也能拍出专业级别的照片。未来，随着AI技术的进一步发展，手机摄影能力还将迎来更大突破。",
            "source": "AI研究动态"
        }
    ]
    
    print(f"已创建{len(structured_data)}条结构化数据和{len(unstructured_data)}条非结构化数据")
    return structured_data, unstructured_data


def structured_search_demo(structured_data: List[Dict]):
    """结构化数据检索演示"""
    print("\n========== 结构化数据检索演示 ==========")
    
    # 初始化结构化搜索模块
    structured_search = StructuredSearch()
    
    # 设置索引
    print("设置结构化数据索引...")
    structured_search.setup_index()
    
    # 索引数据
    print("索引结构化数据...")
    structured_search.index_data(structured_data)
    
    # 等待索引完成
    time.sleep(1)
    
    # 执行基本搜索
    print("\n1. 基本搜索示例 - 搜索'手机':")
    results = structured_search.search(query="手机", size=10)
    for i, result in enumerate(results, 1):
        print(f"{i}. {result['title']} - {result['price']}元 - 销量: {result['sales']}")
    
    # 执行带过滤条件的搜索
    print("\n2. 带过滤条件的搜索 - 价格在5000-10000元之间且有库存的手机:")
    filters = {
        "price_range": {"min": 5000, "max": 10000},
        "in_stock": True,
        "categories": ["手机"]
    }
    results = structured_search.search(query="手机", filters=filters, size=10)
    for i, result in enumerate(results, 1):
        print(f"{i}. {result['title']} - {result['price']}元 - 库存: {result['stock']}")
    
    # 执行带排序的搜索
    print("\n3. 带排序的搜索 - 按销量降序排列:")
    sort_by = [{"sales": {"order": "desc"}}]
    results = structured_search.search(query="手机", sort_by=sort_by, size=10)
    for i, result in enumerate(results, 1):
        print(f"{i}. {result['title']} - {result['price']}元 - 销量: {result['sales']}")
    
    # 执行品牌过滤搜索
    print("\n4. 品牌过滤搜索 - Apple品牌产品:")
    brand_filters = {"brands": ["Apple"]}
    results = structured_search.search(query="", filters=brand_filters, size=10)
    for i, result in enumerate(results, 1):
        print(f"{i}. {result['title']} - {result['category']} - {result['price']}元")


def unstructured_search_demo(unstructured_data: List[Dict]):
    """非结构化数据检索演示"""
    print("\n========== 非结构化数据检索演示 ==========")
    
    # 初始化非结构化搜索模块
    unstructured_search = UnstructuredSearch()
    
    # 设置索引
    print("设置非结构化数据索引...")
    unstructured_search.setup_index()
    
    # 索引数据
    print("索引非结构化数据...")
    unstructured_search.index_data(unstructured_data)
    
    # 等待索引完成
    time.sleep(1)
    
    # 基本BM25搜索
    print("\n1. 基本BM25搜索 - 搜索'iPhone摄影':")
    results = unstructured_search.search(
        query="iPhone摄影", 
        use_bm25=True, 
        use_vector=False, 
        size=5
    )
    for i, result in enumerate(results, 1):
        print(f"{i}. {result['title']} - 得分: {result['_score']:.4f}")
        print(f"   摘要: {result['content'][:100]}...")
    
    # 基本向量搜索
    print("\n2. 基本向量搜索 - 搜索'手机选购指南':")
    results = unstructured_search.search(
        query="手机选购指南", 
        use_bm25=False, 
        use_vector=True, 
        size=5
    )
    for i, result in enumerate(results, 1):
        print(f"{i}. {result['title']} - 得分: {result['_score']:.4f}")
        print(f"   摘要: {result['content'][:100]}...")
    
    # 混合搜索(BM25+向量)
    print("\n3. 混合搜索(BM25+向量) - 搜索'人工智能摄影':")
    results = unstructured_search.search(
        query="人工智能摄影", 
        use_bm25=True, 
        use_vector=True, 
        bm25_weight=0.5, 
        vector_weight=0.5, 
        size=5
    )
    for i, result in enumerate(results, 1):
        print(f"{i}. {result['title']} - 得分: {result['_score']:.4f}")
        print(f"   摘要: {result['content'][:100]}...")
    
    # 使用伪反馈和重排序
    print("\n4. 使用伪反馈和重排序 - 搜索'华为手机体验':")
    results = unstructured_search.search(
        query="华为手机体验", 
        use_bm25=True, 
        use_vector=True, 
        use_pseudo_feedback=True, 
        use_rerank=True, 
        size=5
    )
    for i, result in enumerate(results, 1):
        print(f"{i}. {result['title']} - 得分: {result['_score']:.4f}")
        print(f"   摘要: {result['content'][:100]}...")


def hybrid_search_demo(structured_data: List[Dict], unstructured_data: List[Dict]):
    """混合检索系统演示"""
    print("\n========== 混合检索系统演示 ==========")
    
    # 初始化混合检索系统
    search_system = HybridSearchSystem()
    
    # 设置系统
    print("设置混合检索系统...")
    search_system.setup()
    
    # 索引数据
    print("索引结构化数据...")
    search_system.index_structured_data(structured_data)
    
    print("索引非结构化数据...")
    search_system.index_unstructured_data(unstructured_data)
    
    # 等待索引完成
    time.sleep(2)
    
    # 基本混合搜索
    print("\n1. 基本混合搜索 - 搜索'苹果产品':")
    results = search_system.search(
        query="苹果产品",
        search_type="all",
        size=10
    )
    for i, result in enumerate(results, 1):
        result_type = result['type']
        title = result.get('title', '')
        if result_type == 'structured':
            print(f"{i}. [{result_type}] {title} - {result.get('price', 'N/A')}元")
        else:
            print(f"{i}. [{result_type}] {title} - 来源: {result.get('source', 'N/A')}")
    
    # 使用不同的融合方法
    print("\n2. 使用加权分数融合 - 搜索'Mate系列':")
    results = search_system.search(
        query="Mate系列",
        search_type="all",
        fusion_method="weighted_score",
        structured_weight=0.6,
        unstructured_weight=0.4,
        size=10
    )
    for i, result in enumerate(results, 1):
        result_type = result['type']
        title = result.get('title', '')
        if result_type == 'structured':
            print(f"{i}. [{result_type}] {title} - {result.get('price', 'N/A')}元 - 加权分: {result.get('weighted_score', 0):.4f}")
        else:
            print(f"{i}. [{result_type}] {title} - 加权分: {result.get('weighted_score', 0):.4f}")
    
    # 高级搜索示例
    print("\n3. 高级搜索示例 - 搜索'高端手机'并应用过滤条件:")
    structured_filters = {
        "price_range": {"min": 6000, "max": 20000},
        "categories": ["手机"],
        "in_stock": True
    }
    unstructured_options = {
        "use_bm25": True,
        "use_vector": True,
        "use_pseudo_feedback": True,
        "use_rerank": True
    }
    
    results = search_system.advanced_search(
        query="高端手机",
        structured_filters=structured_filters,
        unstructured_options=unstructured_options,
        size=10
    )
    for i, result in enumerate(results, 1):
        result_type = result['type']
        title = result.get('title', '')
        if result_type == 'structured':
            print(f"{i}. [{result_type}] {title} - {result.get('price', 'N/A')}元")
        else:
            print(f"{i}. [{result_type}] {title} - 来源: {result.get('source', 'N/A')}")
    
    # 批量搜索示例
    print("\n4. 批量搜索示例:")
    queries = [
        {"query": "智能手机", "search_type": "all"},
        {"query": "笔记本电脑", "search_type": "structured"},
        {"query": "人工智能应用", "search_type": "unstructured"}
    ]
    
    batch_results = search_system.batch_search(queries=queries, size=3)
    
    for i, query_result in enumerate(batch_results, 1):
        query = query_result["query"]
        results = query_result["results"]
        print(f"\n查询 {i}: '{query}' ({len(results)}条结果)")
        for j, result in enumerate(results, 1):
            result_type = result.get('type', 'unknown')
            title = result.get('title', '')
            print(f"  {j}. [{result_type}] {title}")


def optimization_techniques_demo():
    """检索优化技术演示"""
    print("\n========== 检索优化技术演示 ==========")
    
    # 初始化混合检索系统
    search_system = HybridSearchSystem()
    
    # 搜索优化1: 使用缓存
    print("\n1. 缓存优化演示:")
    query = "高性能手机"
    
    # 第一次搜索 - 无缓存
    start_time = time.time()
    results1 = search_system.search(query=query, search_type="all", use_cache=True, size=5)
    time1 = time.time() - start_time
    print(f"  第一次搜索耗时: {time1:.4f}秒")
    
    # 第二次搜索 - 有缓存
    start_time = time.time()
    results2 = search_system.search(query=query, search_type="all", use_cache=True, size=5)
    time2 = time.time() - start_time
    print(f"  第二次搜索耗时: {time2:.4f}秒")
    
    # 计算加速比
    if time2 > 0:
        speedup = time1 / time2
        print(f"  缓存加速比: {speedup:.2f}倍")
    
    # 搜索优化2: 调整权重
    print("\n2. 权重调整优化演示:")
    print("  调整BM25和向量检索的权重可以显著影响搜索结果。")
    print("  例如，对于精确匹配需求，可以增加BM25权重；对于语义匹配需求，可以增加向量检索权重。")
    
    # 搜索优化3: 使用预过滤
    print("\n3. 预过滤优化演示:")
    print("  通过业务规则进行预过滤，可以减少搜索范围，提高检索效率。")
    print("  例如，针对用户角色、地域、时间段等进行过滤。")
    
    # 搜索优化4: 结果融合策略
    print("\n4. 结果融合策略演示:")
    print("  Reciprocal Rank Fusion (RRF)通常比简单的加权分数融合效果更好，")
    print("  特别是当不同检索系统的分数分布差异较大时。")


def main():
    """主函数"""
    print("知识图谱检索增强系统演示")
    print("=" * 50)
    
    # 设置环境
    if not setup_environment():
        print("环境检查失败，无法继续演示")
        return
    
    # 创建示例数据
    structured_data, unstructured_data = create_sample_data()
    
    # 执行各模块演示
    try:
        # 结构化数据检索演示
        structured_search_demo(structured_data)
        
        # 非结构化数据检索演示
        unstructured_search_demo(unstructured_data)
        
        # 混合检索系统演示
        hybrid_search_demo(structured_data, unstructured_data)
        
        # 检索优化技术演示
        optimization_techniques_demo()
        
    except Exception as e:
        print(f"演示过程中发生错误: {str(e)}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "=" * 50)
    print("演示完成。更多使用方法请参考USAGE_GUIDE.md文件。")


if __name__ == "__main__":
    main()