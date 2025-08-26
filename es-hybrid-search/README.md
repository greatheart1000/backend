# 知识图谱检索增强系统 (KnowledgeRAG)

一个高性能的结构化和非结构化数据检索系统，结合了BM25、向量检索、机器学习排序和混合检索技术，提供准确、快速的信息检索服务。

## 项目概述

本系统旨在提供一个完整的解决方案，用于提高结构化和非结构化数据的检索召回准确率。系统融合了多种检索技术，包括传统的文本检索（BM25）、向量检索（Dense Retrieval）和机器学习排序，可以根据不同的数据类型和应用场景进行优化配置。

## 核心功能

### 结构化数据检索优化
- **索引和字段优化**：支持复合索引、字段级权重调整、分区和列存储
- **同义词和标准化**：内置同义词映射和字段标准化处理
- **精细化匹配策略**：针对不同字段类型使用不同的匹配模式
- **机器学习排序**：支持LR、GBDT等模型的二次排序
- **业务上下文过滤**：基于用户角色、权限等进行预过滤
- **缓存机制**：使用Redis缓存热点查询结果

### 非结构化数据检索优化
- **混合检索**：BM25+向量检索（Dense+Sparse Hybrid）
- **伪反馈机制**：自动扩充查询以提高召回率
- **查询扩展与重写**：支持同义词、拼写纠错和实体识别
- **多粒度切分**：支持文档和段落级别的检索
- **Cross-Encoder重排序**：使用深度模型进行精排
- **在线学习与反馈闭环**：支持用户行为反馈的模型优化

### 混合检索系统
- **结果融合**：支持Reciprocal Rank Fusion和加权分数融合
- **统一API**：提供结构化、非结构化和混合检索的统一接口
- **批量处理**：支持多查询的批量处理
- **高级搜索**：结合知识图谱和多维度筛选

## 技术栈

- **后端框架**：Flask
- **搜索引擎**：Elasticsearch
- **向量模型**：Sentence Transformers (all-MiniLM-L6-v2)
- **机器学习**：scikit-learn, transformers
- **缓存**：Redis
- **编程语言**：Python 3.8+

## 安装指南

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 配置环境变量

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

### 3. 安装和配置Elasticsearch和Redis

系统依赖Elasticsearch和Redis服务，请确保这两个服务已正确安装和配置。

## 快速开始

### 1. 启动服务

```bash
python app.py
```

系统会自动初始化索引并生成示例数据，然后启动Flask Web服务，默认监听在`http://0.0.0.0:5000`。

### 2. 使用API进行检索

系统提供了RESTful API接口，可以通过HTTP请求进行检索操作。

#### 基本搜索

```bash
curl -X POST http://localhost:5000/api/search \
  -H "Content-Type: application/json" \
  -d '{"query": "人工智能", "search_type": "all", "size": 10}'
```

#### 高级搜索

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

## API接口说明

### 搜索接口 `/api/search`

**请求参数**：
- `query`：搜索查询字符串
- `search_type`：搜索类型（"all"、"structured"、"unstructured"）
- `size`：返回结果数量
- `structured_params`：结构化搜索参数
  - `filters`：过滤条件
  - `sort_by`：排序规则
- `unstructured_params`：非结构化搜索参数
  - `use_bm25`：是否使用BM25
  - `use_vector`：是否使用向量检索
  - `bm25_weight`：BM25权重
  - `vector_weight`：向量权重
  - `use_pseudo_feedback`：是否使用伪反馈
  - `use_rerank`：是否使用重排序
- `fusion_method`：结果融合方法（"reciprocal_rank"、"weighted_score"）
- `structured_weight`：结构化结果权重
- `unstructured_weight`：非结构化结果权重
- `user_context`：用户上下文信息

**返回结果**：

- `success`：操作是否成功
- `query`：查询字符串
- `results`：搜索结果列表
- `total`：结果数量

### 高级搜索接口 `/api/advanced_search`

**请求参数**：
- `query`：搜索查询字符串
- `structured_filters`：结构化数据过滤条件
- `unstructured_options`：非结构化数据检索选项
- `knowledge_graph_boost`：是否启用知识图谱增强
- `size`：返回结果数量

**返回结果**：

- `success`：操作是否成功
- `query`：查询字符串
- `results`：搜索结果列表
- `total`：结果数量

### 批量搜索接口 `/api/batch_search`

**请求参数**：
- `queries`：查询列表，每个查询包含query和search_type等参数
- `size`：每个查询返回的结果数量

**返回结果**：

- `success`：操作是否成功
- `results`：每个查询的结果
- `total_queries`：查询总数

### 健康检查接口 `/api/health`

**返回结果**：
- `success`：服务是否正常运行
- `status`：服务状态
- `timestamp`：时间戳

## 项目结构

```
knowledgeRAG/
├── config.py           # 配置文件
├── utils.py            # 工具类（ES客户端、向量编码器、缓存等）
├── structured_search.py # 结构化数据检索模块
├── unstructured_search.py # 非结构化数据检索模块
├── hybrid_search.py    # 混合检索系统
├── app.py              # Flask应用程序和API接口
├── requirements.txt    # 项目依赖
└── README.md           # 项目文档
```

## 使用示例

### 结构化数据检索示例

```python
from structured_search import StructuredSearch

# 初始化结构化搜索模块
structured_search = StructuredSearch()

# 设置索引
structured_search.setup_index()

# 索引数据
products = [
    {"title": "iPhone 14 Pro", "category": "手机", "brand": "Apple", "price": 8999, "stock": 100, "sales": 1000},
    {"title": "小米13", "category": "手机", "brand": "小米", "price": 3999, "stock": 200, "sales": 1500}
]
structured_search.index_data(products)

# 执行搜索
results = structured_search.search(
    query="手机",
    filters={"price_range": {"min": 3000, "max": 10000}, "in_stock": True},
    sort_by=[{"sales": {"order": "desc"}}],
    size=10
)

print(f"找到{len(results)}条结果")
for result in results:
    print(f"{result['title']} - {result['price']}元")
```

### 非结构化数据检索示例

```python
from unstructured_search import UnstructuredSearch

# 初始化非结构化搜索模块
unstructured_search = UnstructuredSearch()

# 设置索引
unstructured_search.setup_index()

# 索引数据
documents = [
    {"title": "人工智能发展简史", "content": "人工智能是计算机科学的一个分支，致力于开发能够模拟人类智能的机器..."},
    {"title": "机器学习算法入门", "content": "机器学习是人工智能的核心技术，包括监督学习、无监督学习和强化学习..."}
]
unstructured_search.index_data(documents)

# 执行搜索（混合BM25和向量检索）
results = unstructured_search.search(
    query="人工智能技术",
    use_bm25=True,
    use_vector=True,
    bm25_weight=0.5,
    vector_weight=0.5,
    size=10,
    use_rerank=True
)

print(f"找到{len(results)}条结果")
for result in results:
    print(f"{result['title']} - 得分: {result['_score']}")
```

### 混合检索系统示例

```python
from hybrid_search import HybridSearchSystem

# 初始化混合检索系统
search_system = HybridSearchSystem()

# 设置系统
search_system.setup()

# 索引数据
# ...省略数据索引代码...

# 执行混合搜索
results = search_system.search(
    query="人工智能手机",
    search_type="all",
    structured_params={"filters": {"price_range": {"min": 2000}}},
    unstructured_params={"use_rerank": True},
    fusion_method="reciprocal_rank",
    size=10
)

print(f"找到{len(results)}条结果")
for result in results:
    print(f"[{result['type']}] {result.get('title', '')}")
```

## 性能优化建议

1. **索引优化**：根据查询模式优化Elasticsearch索引结构
2. **缓存策略**：合理设置缓存过期时间，针对热点查询进行缓存
3. **资源分配**：根据数据规模和查询负载调整硬件资源
4. **批量处理**：使用批量接口减少网络开销
5. **模型选择**：根据实际需求选择合适的向量模型和排序模型

## 注意事项

1. 本系统依赖Elasticsearch和Redis服务，请确保这些服务正常运行
2. 首次启动时会生成示例数据并创建索引，可能需要一定时间
3. 向量模型下载需要网络连接，首次使用可能会较慢
4. 在生产环境中，建议关闭调试模式并配置适当的日志记录
5. 对于大规模数据，建议调整批量处理参数以提高索引效率

## 扩展方向

1. 集成知识图谱增强检索能力
2. 添加实时数据更新和索引刷新机制
3. 实现分布式部署以提高系统可扩展性
4. 添加更多的机器学习模型支持，如BERT、GPT等
5. 提供可视化管理界面



是的，思路正是如此：

1. Query Understanding

   ——从用户的自由文本里抽取出

   - 结构化条件（时间区间、实体／ID、数值范围、用户角色权限……）
   - 核心关键词（全文检索用）

2. **DSL 组装**——把结构化条件放到 `bool.filter`，把关键词全文检索放到 `bool.must`，可选地再加向量检索、高亮、分组聚合、重排等

3. **执行 & 优化**——提交给 ES，结合前面提到的索引／查询／集群优化手段提升性能

下面给出一个精简模板和 Python 拼装示例，供参考。

------

## 1. Mustache 搜索模板（存 ES 上）

```http
PUT _scripts/mixed_search
{
  "script": {
    "lang": "mustache",
    "source": {
      "size":  "{{size}}",
      "query": {
        "bool": {
          "filter": [
            {{#has_time}}
            {
              "range": {
                "timestamp": {
                  "gte": "{{time_from}}",
                  "lte": "{{time_to}}"
                }
              }
            }{{#has_entity}},{{/has_entity}}{{/has_time}}
            {{#has_entity}}
            {
              "term": { "{{entity_field}}.keyword": "{{entity_value}}" }
            }{{/has_entity}}
          ],
          "must": [
            {
              "multi_match": {
                "query":  "{{keywords}}",
                "fields": ["title^3","title.ngram^2","description"],
                "operator": "and",
                "fuzziness":  "AUTO"
              }
            }
          ]
        }
      },
      "highlight": {
        "fields": {
          "title": {}, "description": {}
        }
      }
    }
  }
}
```

- `{{#has_time}}…{{/has_time}}`、`{{#has_entity}}…{{/has_entity}}` 用于条件化地插入 filter。

------

## 2. Python 示例：解析＋调用模板

```python
import dateparser, spacy
from elasticsearch import Elasticsearch

nlp = spacy.load("en_core_web_sm")
es  = Elasticsearch()

def parse_user_query(q):
    doc = nlp(q)
    # 1) 时间抽取（示例仅演示“from…to…”）
    if "from" in q and "to" in q:
        a,b = q.split("to", 1)
        t0 = dateparser.parse(a.split("from",1)[1].strip())
        t1 = dateparser.parse(b.strip())
        time_from, time_to = t0.isoformat(), t1.isoformat()
        has_time = True
    else:
        has_time = False
        time_from = time_to = ""

    # 2) 实体抽取（示例抽人名、ORG、GPE）
    entity_field = entity_value = ""
    has_entity = False
    for ent in doc.ents:
        if ent.label_ in ("PERSON","ORG","GPE"):
            entity_field = ent.label_.lower()
            entity_value = ent.text
            has_entity = True
            break

    # 3) 关键词：简单取非实体、非停用词
    keywords = " ".join(
      tok.text for tok in doc 
      if not tok.ent_type_ and not tok.is_stop and tok.is_alpha
    ).strip()

    return {
      "has_time":     has_time,
      "time_from":    time_from,
      "time_to":      time_to,
      "has_entity":   has_entity,
      "entity_field": entity_field,
      "entity_value": entity_value,
      "keywords":     keywords or q,  # fallback
      "size":         10
    }

def es_mixed_search(user_q):
    params = parse_user_query(user_q)
    return es.search_template(
      index="products",
      id="mixed_search",
      params=params
    )

# 调用
resp = es_mixed_search(
  "Show me orders by Alice from Nov 1 2024 to Nov 30 2024"
)
print(resp)
```

------

### 为什么这样做能兼顾“结构化”＆“非结构化”：

- 结构化 filter（时间／实体／权限）走 Lucene 的 Filter Cache，精准且无评分消耗
- 非结构化全文检索走倒排索引，多字段、多权重、模糊和高亮都可灵活配置
- 如需语义检索，可在同一模板里继续插入 `knn` 段，或在二次排序里加 Cross-Encoder

结合前面提到的 “索引优化”、“缓存”、“热-温-冷分层”、“分片路由” 等手段，就能打造一个既精准又高效的全场景检索系统。