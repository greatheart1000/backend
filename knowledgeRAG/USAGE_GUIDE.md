# 知识图谱检索增强系统使用指南

本指南详细介绍如何使用知识图谱检索增强系统（KnowledgeRAG）进行结构化和非结构化数据的检索召回操作。

## 系统前提条件

在使用系统前，请确保已安装并配置以下服务：

- **Elasticsearch** (推荐8.10.0版本)
- **Redis** (推荐4.6.0或更高版本)
- **Python 3.8+**

## 安装依赖

首先安装项目所需的所有依赖包：

```bash
pip install -r requirements.txt
```

## 环境配置

系统支持通过环境变量配置关键参数：

```bash
# Elasticsearch配置
export ES_HOST=localhost
export ES_PORT=9200
export ES_USER=elastic
export ES_PASSWORD=changeme
export ES_SCHEME=http

# Redis配置
export REDIS_HOST=localhost
export REDIS_PORT=6379
export REDIS_DB=0

# 检索参数
export TOP_K=10
export BM25_WEIGHT=0.5
export VECTOR_WEIGHT=0.5
```

也可以直接修改`config.py`文件中的默认配置值。

## 快速启动

### 方法1：通过Flask API使用

启动系统服务：

```bash
python app.py
```

系统会自动初始化索引并生成示例数据，然后启动Flask Web服务，默认监听在`http://0.0.0.0:5000`。

### 方法2：通过Python代码直接使用

可以直接在Python代码中导入并使用各模块的功能。

## API接口使用

### 1. 基本搜索接口

**URL**: `/api/search`
**方法**: `POST`

**请求参数**: 
- `query`: 搜索查询字符串
- `search_type`: 搜索类型 (`all`, `structured`, `unstructured`)
- `size`: 返回结果数量
- `structured_params`: 结构化搜索参数
- `unstructured_params`: 非结构化搜索参数
- `fusion_method`: 结果融合方法 (`reciprocal_rank`, `weighted_score`)
- `structured_weight`: 结构化结果权重
- `unstructured_weight`: 非结构化结果权重

**示例请求**: 

```bash
curl -X POST http://localhost:5000/api/search \
  -H "Content-Type: application/json" \
  -d '{"query": "人工智能手机", "search_type": "all", "size": 10}'
```

### 2. 高级搜索接口

**URL**: `/api/advanced_search`
**方法**: `POST`

**请求参数**: 
- `query`: 搜索查询字符串
- `structured_filters`: 结构化数据过滤条件
- `unstructured_options`: 非结构化数据检索选项
- `knowledge_graph_boost`: 是否启用知识图谱增强
- `size`: 返回结果数量

**示例请求**: 

```bash
curl -X POST http://localhost:5000/api/advanced_search \
  -H "Content-Type: application/json" \
  -d '{
    "query": "手机",
    "structured_filters": {"price_range": {"min": 1000, "max": 5000}, "in_stock": true},
    "unstructured_options": {"use_pseudo_feedback": true, "use_rerank": true},
    "size": 10
  }'
```

### 3. 批量搜索接口

**URL**: `/api/batch_search`
**方法**: `POST`

**请求参数**: 
- `queries`: 查询列表，每个查询包含query和search_type等参数
- `size`: 每个查询返回的结果数量

**示例请求**: 

```bash
curl -X POST http://localhost:5000/api/batch_search \
  -H "Content-Type: application/json" \
  -d '{
    "queries": [
      {"query": "人工智能", "search_type": "unstructured"},
      {"query": "手机", "search_type": "structured"}
    ],
    "size": 5
  }'
```

### 4. 健康检查接口

**URL**: `/api/health`
**方法**: `GET`

**示例请求**: 

```bash
curl http://localhost:5000/api/health
```

## Python代码直接使用示例

### 1. 结构化数据检索使用

```python
from structured_search import StructuredSearch

# 初始化结构化搜索模块
structured_search = StructuredSearch()

# 索引数据
example_data = [
    {"title": "iPhone 14 Pro", "category": "手机", "brand": "Apple", "price": 8999, "stock": 100, "sales": 1000},
    {"title": "小米13", "category": "手机", "brand": "小米", "price": 3999, "stock": 200, "sales": 1500}
]
structured_search.index_data(example_data)

# 执行搜索
results = structured_search.search(
    query="手机",
    filters={"price_range": {"min": 3000, "max": 10000}, "in_stock": True},
    sort_by=[{"sales": {"order": "desc"}}],
    size=10
)

# 输出结果
print(f"找到{len(results)}条结果")
for result in results:
    print(f"{result['title']} - {result['price']}元 - 销量: {result['sales']}")
```

### 2. 非结构化数据检索使用

```python
from unstructured_search import UnstructuredSearch

# 初始化非结构化搜索模块
unstructured_search = UnstructuredSearch()

# 索引数据
documents = [
    {"title": "人工智能发展简史", "content": "人工智能是计算机科学的一个分支，致力于开发能够模拟人类智能的机器。"},
    {"title": "机器学习算法入门", "content": "机器学习是人工智能的核心技术，包括监督学习、无监督学习和强化学习。"}
]
unstructured_search.index_data(documents)

# 执行混合搜索（BM25+向量检索）
results = unstructured_search.search(
    query="人工智能技术",
    use_bm25=True,
    use_vector=True,
    bm25_weight=0.5,
    vector_weight=0.5,
    size=10,
    use_rerank=True,
    use_pseudo_feedback=True
)

# 输出结果
print(f"找到{len(results)}条结果")
for result in results:
    print(f"{result['title']} - 得分: {result['_score']}")
    print(f"摘要: {result['content'][:100]}...")
```

### 3. 混合检索系统使用

```python
from hybrid_search import HybridSearchSystem

# 初始化混合检索系统
search_system = HybridSearchSystem()

# 设置系统（创建索引）
search_system.setup()

# 索引结构化数据
structured_data = [
    {"title": "iPhone 14 Pro", "category": "手机", "brand": "Apple", "price": 8999, "stock": 100},
    {"title": "iPad Pro", "category": "平板", "brand": "Apple", "price": 6299, "stock": 50}
]
search_system.index_structured_data(structured_data)

# 索引非结构化数据
unstructured_data = [
    {"title": "iPhone 14 Pro评测", "content": "iPhone 14 Pro搭载A16芯片，性能强劲，相机系统有重大升级。"},
    {"title": "平板电脑选购指南", "content": "选择平板电脑时，需要考虑屏幕尺寸、性能、电池续航等因素。"}
]
search_system.index_unstructured_data(unstructured_data)

# 执行混合搜索
results = search_system.search(
    query="iPhone",
    search_type="all",
    structured_params={"filters": {"price_range": {"min": 5000}}},
    unstructured_params={"use_rerank": True},
    fusion_method="reciprocal_rank",
    size=10
)

# 输出结果
print(f"找到{len(results)}条结果")
for result in results:
    result_type = result['type']
    title = result.get('title', '')
    price = result.get('price', 'N/A')
    score = result.get('_score', 'N/A')
    print(f"[{result_type}] {title} - 价格: {price}元 - 得分: {score}")
```

### 4. 高级搜索功能使用

```python
from hybrid_search import HybridSearchSystem

# 初始化混合检索系统
search_system = HybridSearchSystem()

# 执行高级搜索
results = search_system.advanced_search(
    query="智能手机",
    structured_filters={
        "price_range": {"min": 2000, "max": 8000},
        "categories": ["手机"],
        "brands": ["Apple", "华为", "小米"],
        "in_stock": True
    },
    unstructured_options={
        "use_bm25": True,
        "use_vector": True,
        "bm25_weight": 0.6,
        "vector_weight": 0.4,
        "use_pseudo_feedback": True,
        "use_rerank": True
    },
    knowledge_graph_boost=False,
    size=10
)

# 输出结果
print(f"找到{len(results)}条结果")
for i, result in enumerate(results, 1):
    print(f"{i}. [{result['type']}] {result.get('title', '')}")
    if result['type'] == 'structured':
        print(f"   价格: {result.get('price', 'N/A')}元 - 销量: {result.get('sales', 'N/A')}")
    else:
        print(f"   来源: {result.get('source', 'N/A')} - 得分: {result.get('_score', 'N/A')}")
```

## 性能优化建议

1. **索引优化**：根据查询模式优化Elasticsearch索引结构
2. **缓存策略**：合理设置缓存过期时间，针对热点查询进行缓存
3. **资源分配**：根据数据规模和查询负载调整硬件资源
4. **批量处理**：使用批量接口减少网络开销
5. **模型选择**：根据实际需求选择合适的向量模型和排序模型

## 常见问题解决

1. **连接Elasticsearch失败**：检查ES服务是否启动，以及配置的主机、端口、用户名和密码是否正确
2. **向量模型加载失败**：确保有网络连接，首次使用需要下载模型
3. **中文分词不准确**：确认Elasticsearch已安装中文分词插件（如IK分词器）
4. **检索结果不理想**：调整BM25和向量检索的权重，或尝试使用伪反馈和重排序功能

## 扩展开发指南

1. **添加自定义同义词词典**：修改`structured_search.py`和`unstructured_search.py`中的`_load_synonyms`方法
2. **集成知识图谱**：实现`hybrid_search.py`中的`knowledge_graph`接口和`_enhance_with_knowledge_graph`方法
3. **自定义排序模型**：扩展`structured_search.py`中的`train_rank_model`方法，训练适合业务需求的排序模型
4. **添加新的检索算法**：在`utils.py`中实现新的搜索算法，并在各搜索模块中调用

通过以上方法，可以充分利用知识图谱检索增强系统的功能，实现高效、准确的结构化和非结构化数据检索召回。