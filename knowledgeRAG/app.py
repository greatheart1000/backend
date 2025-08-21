from flask import Flask, request, jsonify
from hybrid_search import HybridSearchSystem
import numpy as np
import time
import random
import os

app = Flask(__name__)
search_system = HybridSearchSystem()

# 示例数据生成函数
def generate_sample_structured_data(num_items: int = 1000) -> list:
    """生成结构化数据样本"""
    categories = ["手机", "电脑", "平板", "耳机", "智能手表"]
    brands = ["Apple", "Samsung", "华为", "小米", "OPPO", "VIVO", "联想", "戴尔"]
    
    data = []
    for i in range(num_items):
        category = random.choice(categories)
        brand = random.choice(brands)
        
        # 生成产品标题
        titles = {
            "手机": [f"{brand} 智能手机 {random.randint(1000, 9999)}", f"{brand} 5G手机 {random.randint(1000, 9999)}系列"],
            "电脑": [f"{brand} 笔记本电脑 {random.randint(2022, 2024)}款", f"{brand} 台式机 {random.randint(1000, 9999)}型号"],
            "平板": [f"{brand} 平板电脑 {random.randint(7, 13)}英寸", f"{brand} 平板Pro {random.randint(1000, 9999)}"],
            "耳机": [f"{brand} 蓝牙耳机 主动降噪", f"{brand} 无线耳机 {random.randint(1000, 9999)}型号"],
            "智能手表": [f"{brand} 智能手表 运动监测", f"{brand} 手表Pro {random.randint(1000, 9999)}"]
        }
        
        data.append({
            "id": f"structured_{i}",
            "title": random.choice(titles[category]),
            "category": category,
            "brand": brand,
            "price": round(random.uniform(99.99, 9999.99), 2),
            "stock": random.randint(0, 1000),
            "sales": random.randint(0, 10000),
            "rating": round(random.uniform(1.0, 5.0), 1),
            "description": f"这是一款高品质的{brand}{category}，具有出色的性能和设计，适合各种使用场景。"
        })
    
    return data

def generate_sample_unstructured_data(num_items: int = 500) -> list:
    """生成非结构化数据样本"""
    topics = ["人工智能", "大数据分析", "云计算", "区块链技术", "物联网", "网络安全", "机器学习", "深度学习"]
    sources = ["技术博客", "学术论文", "新闻文章", "产品文档", "用户手册", "行业报告"]
    
    data = []
    for i in range(num_items):
        topic = random.choice(topics)
        source = random.choice(sources)
        
        # 生成内容
        contents = {
            "人工智能": [
                "人工智能（Artificial Intelligence，简称AI）是计算机科学的一个分支，旨在创造能够模拟人类智能的机器。AI技术包括机器学习、深度学习、自然语言处理等多个领域。近年来，随着计算能力的提升和算法的进步，AI技术在各个行业得到了广泛应用。",
                "机器学习是人工智能的核心技术之一，通过让计算机从数据中学习规律，无需明确编程即可完成任务。监督学习、无监督学习和强化学习是机器学习的主要类型。"
            ],
            "大数据分析": [
                "大数据分析是指对规模巨大的数据进行分析，以提取有价值的信息和洞察。大数据具有Volume（大量）、Velocity（高速）、Variety（多样）和Value（价值）等特点。",
                "大数据分析技术包括数据挖掘、统计分析、机器学习等。通过大数据分析，企业可以更好地了解客户需求，优化业务流程，提高决策效率。"
            ],
            "云计算": [
                "云计算是一种通过网络提供计算资源（如服务器、存储、数据库、网络、软件等）的模式。云计算具有按需自助服务、广泛的网络访问、资源池化、快速弹性和可计量服务等特点。",
                "云计算服务模型主要包括基础设施即服务（IaaS）、平台即服务（PaaS）和软件即服务（SaaS）。云计算部署模型包括公有云、私有云和混合云。"
            ],
            "区块链技术": [
                "区块链是一种分布式账本技术，具有去中心化、不可篡改、透明和安全等特点。区块链由一系列区块组成，每个区块包含一批交易记录，通过密码学技术连接在一起。",
                "区块链技术最初用于比特币等加密货币，但现在已经扩展到供应链管理、金融服务、医疗健康、数字身份等多个领域。智能合约是区块链的重要应用之一。"
            ],
            "物联网": [
                "物联网（Internet of Things，简称IoT）是指通过互联网将各种物理设备连接起来，实现数据收集、交换和分析的网络。IoT设备包括传感器、智能家电、工业设备等。",
                "物联网技术的关键组成部分包括传感器技术、通信技术、数据处理和分析技术以及云平台。物联网的应用包括智能家居、智能城市、工业物联网等。"
            ],
            "网络安全": [
                "网络安全是指保护计算机网络和系统免受未经授权的访问、使用、披露、破坏、修改或干扰的措施。网络安全威胁包括黑客攻击、恶意软件、网络钓鱼、拒绝服务攻击等。",
                "网络安全防护措施包括防火墙、入侵检测和防御系统、加密技术、访问控制、安全审计等。随着网络威胁的不断演变，网络安全已成为当今数字化时代的重要挑战。"
            ],
            "机器学习": [
                "机器学习是人工智能的一个分支，致力于研究如何使计算机能够从数据中学习并改进性能。机器学习算法可以分为监督学习、无监督学习、半监督学习和强化学习等类型。",
                "常见的机器学习算法包括线性回归、逻辑回归、决策树、随机森林、支持向量机、聚类算法等。这些算法在预测分析、模式识别、推荐系统等领域有广泛应用。"
            ],
            "深度学习": [
                "深度学习是机器学习的一个子领域，基于人工神经网络模型，特别是具有多个隐藏层的深度神经网络。深度学习在计算机视觉、自然语言处理、语音识别等领域取得了突破性进展。",
                "常见的深度学习架构包括卷积神经网络（CNN）、循环神经网络（RNN）、长短期记忆网络（LSTM）、Transformer等。深度学习需要大量的数据和计算资源来训练复杂的神经网络模型。"
            ]
        }
        
        data.append({
            "id": f"unstructured_{i}",
            "title": f"{topic}研究进展与应用",
            "content": random.choice(contents[topic]),
            "source": source
        })
    
    return data

# 初始化系统
def init_system():
    """初始化检索系统"""
    try:
        print("正在初始化检索系统...")
        start_time = time.time()
        
        # 设置索引
        search_system.setup()
        
        # 生成并索引示例数据
        print("正在生成结构化数据样本...")
        structured_data = generate_sample_structured_data(1000)
        print(f"生成了{len(structured_data)}条结构化数据")
        
        print("正在索引结构化数据...")
        search_system.index_structured_data(structured_data)
        
        print("正在生成非结构化数据样本...")
        unstructured_data = generate_sample_unstructured_data(500)
        print(f"生成了{len(unstructured_data)}条非结构化数据")
        
        print("正在索引非结构化数据...")
        search_system.index_unstructured_data(unstructured_data)
        
        end_time = time.time()
        print(f"检索系统初始化完成，耗时{end_time - start_time:.2f}秒")
    except Exception as e:
        print(f"初始化检索系统时出错: {str(e)}")

# API路由
@app.route('/api/search', methods=['POST'])
def api_search():
    """搜索API接口"""
    try:
        data = request.json
        query = data.get('query', '')
        search_type = data.get('search_type', 'all')
        size = data.get('size', 10)
        
        # 结构化搜索参数
        structured_params = data.get('structured_params', {})
        
        # 非结构化搜索参数
        unstructured_params = data.get('unstructured_params', {})
        
        # 融合参数
        fusion_method = data.get('fusion_method', 'reciprocal_rank')
        structured_weight = data.get('structured_weight', 0.5)
        unstructured_weight = data.get('unstructured_weight', 0.5)
        
        # 用户上下文
        user_context = data.get('user_context', None)
        
        # 执行搜索
        results = search_system.search(
            query=query,
            search_type=search_type,
            structured_params=structured_params,
            unstructured_params=unstructured_params,
            fusion_method=fusion_method,
            structured_weight=structured_weight,
            unstructured_weight=unstructured_weight,
            size=size,
            user_context=user_context
        )
        
        return jsonify({
            'success': True,
            'query': query,
            'results': results,
            'total': len(results)
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/advanced_search', methods=['POST'])
def api_advanced_search():
    """高级搜索API接口"""
    try:
        data = request.json
        query = data.get('query', '')
        structured_filters = data.get('structured_filters', None)
        unstructured_options = data.get('unstructured_options', None)
        knowledge_graph_boost = data.get('knowledge_graph_boost', False)
        size = data.get('size', 10)
        
        # 执行高级搜索
        results = search_system.advanced_search(
            query=query,
            structured_filters=structured_filters,
            unstructured_options=unstructured_options,
            knowledge_graph_boost=knowledge_graph_boost,
            size=size
        )
        
        return jsonify({
            'success': True,
            'query': query,
            'results': results,
            'total': len(results)
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/batch_search', methods=['POST'])
def api_batch_search():
    """批量搜索API接口"""
    try:
        data = request.json
        queries = data.get('queries', [])
        size = data.get('size', 10)
        
        # 执行批量搜索
        results = search_system.batch_search(
            queries=queries,
            size=size
        )
        
        return jsonify({
            'success': True,
            'results': results,
            'total_queries': len(queries)
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/health', methods=['GET'])
def api_health():
    """健康检查接口"""
    return jsonify({
        'success': True,
        'status': 'running',
        'timestamp': time.time()
    })

# 主函数
if __name__ == '__main__':
    # 初始化系统
    init_system()
    
    # 启动Flask应用
    app.run(host='0.0.0.0', port=5000, debug=True)