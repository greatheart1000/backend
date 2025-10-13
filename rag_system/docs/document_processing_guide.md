# 文档处理指南

## 概述

本文档详细介绍RAG系统中的文档处理流程，包括文档切分、分层处理和向量化等关键步骤。

## 文档处理流程

### 1. 文档切分策略

系统采用分层切分策略，生成不同粒度的文档块：

#### 大块（Large Chunks）
- **大小**：1000字符
- **重叠**：100字符
- **用途**：保持段落完整性，适合长文本理解

#### 小块（Small Chunks）
- **大小**：300字符
- **重叠**：30字符
- **用途**：提高检索精度，适合精确匹配

### 2. 切分算法

```python
def split_document(content, chunk_size=500, overlap=50):
    """
    文档切分算法
    """
    # 1. 按句子切分
    sentences = split_into_sentences(content)
    
    # 2. 按块大小合并句子
    chunks = []
    current_chunk = ""
    
    for sentence in sentences:
        if len(current_chunk) + len(sentence) > chunk_size:
            # 保存当前块
            chunks.append(current_chunk)
            # 保留重叠部分
            current_chunk = get_overlap_content(current_chunk, overlap)
        
        current_chunk += sentence + " "
    
    # 添加最后一个块
    if current_chunk:
        chunks.append(current_chunk)
    
    return chunks
```

### 3. 向量化处理

系统对每个文档块进行向量化处理：

#### 向量化策略
- **对所有块向量化**：无论是大块还是小块，都生成对应的向量表示
- **使用模型**：SentenceTransformer (all-MiniLM-L6-v2)
- **向量维度**：384维

#### 向量化优势
1. **语义检索**：支持基于语义相似度的检索
2. **多粒度匹配**：大块提供上下文，小块提供精确匹配
3. **缓存优化**：向量可缓存，避免重复计算

## 文档结构

处理后的文档在Elasticsearch中的存储结构：

```json
{
  "content": "文档块内容",
  "title": "文档标题",
  "doc_id": "原始文档ID",
  "chunk_id": "块类型标识",
  "chunk_level": "块级别(large/small)",
  "chunk_index": "块索引",
  "length": "块长度",
  "vector": [0.1, 0.2, 0.3, "..."],  // 384维向量
  "metadata": {
    "tags": ["标签1", "标签2"],
    "category": "分类"
  }
}
```

## 使用示例

### 1. 处理单个文档

```python
from documents.doc_processor import doc_processor

# 文档内容
content = """
人工智能（Artificial Intelligence，AI）是计算机科学的一个分支，
它企图了解智能的实质，并生产出一种新的能以人类智能相似的方式做出反应的智能机器。
人工智能研究包括机器人、语言识别、图像识别、自然语言处理和专家系统等。
"""

# 处理文档
chunks = doc_processor.process_document(
    doc_id="ai_intro_001",
    title="人工智能简介",
    content=content,
    metadata={"category": "technology", "tags": ["AI", "计算机科学"]}
)

print(f"生成 {len(chunks)} 个文档块")
```

### 2. 导入数据到Elasticsearch

```bash
# 导入JSON格式数据
python scripts/import_data.py sample_data.json --type json

# 导入文本格式数据
python scripts/import_data.py sample_data.txt --type text
```

## 性能优化

### 1. 切分优化
- **句子边界对齐**：尽量在句子边界切分，保持语义完整性
- **重叠策略**：通过重叠确保上下文连续性
- **层级设计**：大块保持上下文，小块提高精度

### 2. 向量化优化
- **批量处理**：支持批量向量化提高效率
- **缓存机制**：相同内容的块共享向量计算结果
- **模型选择**：平衡准确性和计算效率

### 3. 存储优化
- **字段设计**：合理设计ES字段类型和索引策略
- **向量索引**：启用向量索引加速相似度检索
- **分层检索**：支持按块级别检索

## 最佳实践

### 1. 文档预处理
- 清理无关字符和格式
- 标准化文本编码
- 提取元数据信息

### 2. 切分参数调优
- 根据文档类型调整块大小
- 根据检索需求调整重叠大小
- 平衡块数量和检索精度

### 3. 质量控制
- 验证切分结果的语义完整性
- 检查向量化质量
- 监控存储效率

## 故障排除

### 常见问题

1. **切分结果不理想**
   - 调整块大小参数
   - 检查句子切分逻辑
   - 优化重叠策略

2. **向量化失败**
   - 检查模型加载状态
   - 验证文本编码格式
   - 查看内存使用情况

3. **ES索引问题**
   - 检查索引映射配置
   - 验证向量维度匹配
   - 查看ES日志信息

通过以上文档处理机制，系统能够有效地将原始文档转换为适合RAG检索的结构化块，为后续的检索和问答提供高质量的数据基础。