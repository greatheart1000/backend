# RAG知识库系统

基于Redis缓存的六阶段RAG管道系统，包含意图识别、上下文管理、混合检索、精排融合、答案生成等模块。

## 功能特性

- 六阶段RAG管道处理
- 多级Redis缓存优化
- 意图识别与动态权重分配
- 混合检索(BM25+向量)
- RRF融合与BGE精排
- 会话上下文管理
- API服务接口

## 系统架构

### 六阶段管道

1. **意图与权重分析**
   - 分析Query意图（A/B/C/D类型）
   - 确定BM25和Vector权重
   - 核心技术：LLM/Prompt工程或轻量级分类模型
   - Redis交互：读写缓存A（意图/权重）

2. **向量化与会话管理**
   - 将Query转换为向量表示
   - 获取会话历史
   - 核心技术：Embedding模型，滑动窗口
   - Redis交互：读写缓存D（查询向量）和缓存E（会话历史）

3. **混合检索（粗排）**
   - 在ES中执行动态加权的script_score查询
   - 核心技术：ES Hybrid Search，动态权重
   - Redis交互：读写缓存B（Top M ID列表）

4. **精排与融合**
   - RRF融合 + BGE Reranker精排
   - 确定最终Top K文档
   - 核心技术：RRF + BGE Reranker
   - Redis交互：检查缓存C（最终答案）

5. **答案生成**
   - 构建Prompt，调用Qwen API生成答案
   - 核心技术：Qwen API，Prompt Engineering

6. **结果返回与缓存**
   - 返回答案给用户，更新会话历史
   - 核心技术：用户体验优化
   - Redis交互：写入缓存C（最终答案）和更新缓存E（会话历史）

## 项目结构

```
rag_system/
├── app.py              # 主应用入口
├── api.py              # Web API服务
├── init.py             # 系统初始化脚本
├── check_env.py        # 环境检查工具
├── start.sh            # 启动脚本
├── Dockerfile          # Docker部署文件
├── requirements.txt    # 依赖清单
├── config/
│   └── settings.py     # 配置文件
├── cache/
│   └── cache_manager.py # 缓存管理器
├── documents/
│   └── doc_processor.py # 文档处理器
├── models/
│   ├── intent_classifier.py  # 意图分类器
│   ├── context_manager.py    # 上下文管理器
│   ├── dynamic_retriever.py  # 动态检索器
│   ├── reranker.py           # 精排器
│   └── answer_generator.py   # 答案生成器
├── scripts/
│   └── import_data.py        # 数据导入脚本
├── services/
│   └── rag_pipeline.py       # RAG管道控制器
├── tests/                    # 测试文件
└── docs/                     # 文档资料
```

## 安装依赖

在运行系统之前，需要安装所需的依赖包：

```bash
pip install -r requirements.txt
```

注意：某些依赖包（如torch）可能需要较长时间安装，请耐心等待。

如果遇到网络问题，可以使用国内镜像源：

```bash
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
```

## 配置环境

在运行系统之前，需要设置以下环境变量：

```bash
export REDIS_HOST=localhost
export REDIS_PORT=6379
export ELASTICSEARCH_HOST=localhost
export ELASTICSEARCH_PORT=9200
export QWEN_API_KEY=your_qwen_api_key
```

### Elasticsearch配置说明

系统使用Elasticsearch作为主要的文档存储和检索引擎：

1. **索引结构**：
   - 索引名称：`rag_documents`
   - 字段包含：`content`（文本内容）、`title`（标题）、`vector`（向量表示）、`metadata`（元数据）

2. **向量字段配置**：
   - 字段类型：`dense_vector`
   - 向量维度：384（与默认嵌入模型匹配）

3. **混合检索**：
   - BM25关键词检索
   - 向量相似度检索
   - 动态权重融合

## 初始化系统

```bash
python init.py
```

初始化脚本将：
1. 创建Elasticsearch索引
2. 设置正确的索引映射
3. 准备系统运行环境

## 导入数据

系统提供数据导入脚本，支持JSON和文本格式的数据导入：

```bash
# 导入JSON格式数据
python scripts/import_data.py sample_data.json --type json

# 导入文本格式数据（每行一个文档）
python scripts/import_data.py data.txt --type text
```

### 数据格式

1. **JSON格式**：
   ```json
   [
     {
       "id": "文档唯一标识",
       "title": "文档标题",
       "content": "文档内容",
       "metadata": {
         "category": "分类",
         "tags": ["标签1", "标签2"]
       }
     }
   ]
   ```

2. **文本格式**：
   ```
   这是第一行文档内容
   这是第二行文档内容
   这是第三行文档内容
   ```

## 运行系统

```bash
python app.py --query "你的问题" --session_id "会话ID"
```

## 启动API服务

```bash
python api.py
```

API服务将启动在 `http://localhost:8000`

### API接口

- `GET /` - 查询表单界面
- `POST /query` - 处理查询接口
- `GET /health` - 健能检查接口

## 使用示例

更多使用示例请参考 [使用示例文档](docs/usage_example.md)

### POST /query 请求格式

```json
{
  "query": "你的问题",
  "session_id": "会话ID"
}
```

### POST /query 响应格式

```json
{
  "query": "你的问题",
  "answer": "生成的答案",
  "intent": "识别的意图类型",
  "from_cache": false,
  "candidates_count": 100,
  "final_docs_count": 10
}
```

## 缓存策略

系统使用Redis实现五级缓存，每级缓存都有特定的优化目标：

- **缓存A**：意图识别结果 - 避免重复的意图分类计算
- **缓存B**：检索候选列表 - 避免重复的数据库检索操作
- **缓存C**：最终答案 - 对热点查询直接返回结果
- **缓存D**：查询向量 - 避免重复的文本向量化操作
- **缓存E**：会话历史 - 维护对话上下文连贯性

### 每级缓存的作用和意义

1. **缓存A（意图识别结果）**：
   - **作用**：存储查询意图分类结果和检索权重
   - **意义**：避免对相同查询重复进行意图分析，节省LLM或分类模型的计算资源
   - **价值**：减少模型推理开销，提升分类效率

2. **缓存B（检索候选列表）**：
   - **作用**：存储混合检索后的候选文档ID列表
   - **意义**：避免重复执行耗时的ES检索操作
   - **价值**：减少数据库查询负载，提升检索效率

3. **缓存C（最终答案）**：
   - **作用**：存储最终生成的答案结果
   - **意义**：对于完全相同的查询，直接返回答案，跳过整个RAG流程
   - **价值**：实现热点查询的极速响应，优化用户体验

4. **缓存D（查询向量）**：
   - **作用**：存储文本到向量的转换结果
   - **意义**：避免重复的嵌入计算
   - **价值**：节省SentenceTransformer的推理时间

5. **缓存E（会话历史）**：
   - **作用**：存储用户会话上下文信息
   - **意义**：维护对话连贯性，支持上下文相关的多轮对话
   - **价值**：提供自然流畅的对话体验

### 为什么需要五级缓存？

1. **性能优化**: 不同层级的缓存针对不同的计算瓶颈进行优化，最大化系统响应速度
2. **成本控制**: 减少重复的模型推理和数据库查询，降低API调用成本
3. **用户体验**: 多层次缓存显著提升用户交互体验，特别是热点查询的响应时间
4. **资源利用**: 合理分配计算资源，避免不必要的重复计算

### 语义相似度缓存

系统支持基于语义相似度的智能缓存匹配：

1. **精确匹配**：完全相同的查询直接返回缓存结果（毫秒级响应）
2. **语义匹配**：语义相似但表达不同的查询可复用相关缓存（100-300毫秒响应）
3. **阈值控制**：默认相似度阈值为0.95，可配置调整

**示例**：
- 用户查询："什么是人工智能？" → 缓存答案
- 用户查询："人工智能是什么？" → 语义相似度0.96 → 复用缓存答案

### Redis Cluster支持

系统支持Redis Cluster部署以处理大规模并发场景：

```bash
# 配置Redis Cluster节点
export REDIS_CLUSTER_NODES="host1:port1,host2:port2,host3:port3"
```

优势：
- 水平扩展支持大规模并发
- 高可用性保障
- 分布式存储提升性能

### 相似查询处理机制

系统通过多级缓存机制智能处理相似查询：

1. **完全相同查询**：直接从缓存C返回答案，响应时间在毫秒级
2. **高度相似查询**：通过语义相似度计算，可能复用相关缓存结果
3. **不同查询**：执行完整RAG流程，并将结果缓存以备后续使用

**示例场景**：
- 用户首次查询："什么是人工智能？" → 执行完整RAG流程（2-5秒）
- 用户再次查询："什么是人工智能？" → 直接从缓存返回（50-200毫秒）
- 用户查询："人工智能是什么？" → 执行完整RAG流程，但结果会被缓存

更多关于相似查询处理的详细信息，请参考 [相似查询处理文档](docs/similarity_query_processing.md)

## 模型说明

- **意图分类**：facebook/bart-large-mnli
- **文本嵌入**：sentence-transformers/all-MiniLM-L6-v2
- **精排模型**：BAAI/bge-reranker-base
- **生成模型**：Qwen API

## 性能优化

1. 多级缓存减少重复计算
2. 向量检索与关键词检索结合
3. 结果缓存避免重复生成
4. 会话上下文管理提升对话体验

## 文档

- [系统架构设计](docs/architecture.md)
- [使用示例](docs/usage_example.md)
- [Elasticsearch使用指南](docs/elasticsearch_guide.md)
- [文档处理指南](docs/document_processing_guide.md)
- [相似查询处理](docs/similarity_query_processing.md)
