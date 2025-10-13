# Elasticsearch使用指南

## Elasticsearch配置

### 环境变量设置

在使用RAG系统之前，请确保设置以下环境变量：

```bash
export ELASTICSEARCH_HOST=localhost
export ELASTICSEARCH_PORT=9200
```

### Docker启动Elasticsearch（推荐）

如果您没有安装Elasticsearch，可以使用Docker快速启动：

```bash
# 启动单节点Elasticsearch
docker run -d --name elasticsearch -p 9200:9200 -p 9300:9300 -e "discovery.type=single-node" -e "xpack.security.enabled=false" docker.elastic.co/elasticsearch/elasticsearch:8.0.0
```

## 索引结构

RAG系统使用名为`rag_documents`的索引，其结构如下：

```json
{
  "mappings": {
    "properties": {
      "content": {
        "type": "text"
      },
      "title": {
        "type": "text"
      },
      "vector": {
        "type": "dense_vector",
        "dims": 384
      },
      "metadata": {
        "type": "object",
        "enabled": false
      }
    }
  }
}
```

## 数据导入

### 使用导入脚本

系统提供了便捷的数据导入脚本：

```bash
# 导入JSON数据
python scripts/import_data.py sample_data.json --type json

# 导入文本数据
python scripts/import_data.py sample_data.txt --type text
```

### 手动创建索引

如果您需要手动创建索引，可以使用以下curl命令：

```bash
# 创建索引
curl -X PUT "localhost:9200/rag_documents" -H 'Content-Type: application/json' -d'
{
  "mappings": {
    "properties": {
      "content": {
        "type": "text"
      },
      "title": {
        "type": "text"
      },
      "vector": {
        "type": "dense_vector",
        "dims": 384
      },
      "metadata": {
        "type": "object",
        "enabled": false
      }
    }
  }
}
'
```

### 手动索引文档

使用curl命令手动索引文档：

```bash
curl -X POST "localhost:9200/rag_documents/_doc/doc_1" -H 'Content-Type: application/json' -d'
{
  "title": "示例文档",
  "content": "这是示例文档的内容",
  "vector": [0.1, 0.2, 0.3, "..."],  # 384维向量
  "metadata": {
    "category": "example",
    "tags": ["示例", "测试"]
  }
}
'
```

## 查询测试

### 检查索引状态

```bash
# 检查索引是否存在
curl -X GET "localhost:9200/_cat/indices?v"

# 获取索引映射
curl -X GET "localhost:9200/rag_documents/_mapping"
```

### 搜索测试

```bash
# 基本文本搜索
curl -X GET "localhost:9200/rag_documents/_search" -H 'Content-Type: application/json' -d'
{
  "query": {
    "match": {
      "content": "人工智能"
    }
  }
}
'

# 向量相似度搜索
curl -X GET "localhost:9200/rag_documents/_search" -H 'Content-Type: application/json' -d'
{
  "query": {
    "script_score": {
      "query": {
        "match_all": {}
      },
      "script": {
        "source": "cosineSimilarity(params.query_vector, 'vector') + 1.0",
        "params": {
          "query_vector": [0.1, 0.2, 0.3, "..."]  # 查询向量
        }
      }
    }
  }
}
'
```

## 性能优化建议

### 索引优化

1. **批量导入**：使用bulk API进行批量数据导入
2. **索引刷新**：适当调整索引刷新间隔
3. **分片设置**：根据数据量合理设置分片数量

### 查询优化

1. **字段选择**：只返回需要的字段
2. **分页处理**：合理使用分页避免大量数据传输
3. **缓存利用**：利用Elasticsearch的查询缓存机制

### 监控和维护

1. **定期检查**：监控索引健康状态
2. **日志分析**：分析慢查询日志
3. **备份策略**：定期备份重要数据

## 故障排除

### 常见问题

1. **连接失败**：
   - 检查Elasticsearch服务是否启动
   - 检查网络连接和端口配置
   - 检查防火墙设置

2. **索引不存在**：
   - 运行初始化脚本创建索引
   - 手动创建索引

3. **向量维度不匹配**：
   - 确保向量维度与索引映射一致（384维）
   - 检查嵌入模型配置

### 日志查看

```bash
# 查看Elasticsearch日志（Docker）
docker logs elasticsearch

# 查看RAG系统日志
# 日志会输出到控制台，可根据需要重定向到文件
```

通过以上指南，您应该能够成功配置和使用Elasticsearch作为RAG系统的存储和检索后端。