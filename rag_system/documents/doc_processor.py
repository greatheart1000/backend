"""
文档处理模块
负责文档切分、文本分块和向量化处理
"""

import re
import logging
import jieba
from typing import List, Dict, Tuple, Any
from sentence_transformers import SentenceTransformer
import numpy as np
from config.settings import settings

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DocumentProcessor:
    def __init__(self):
        """初始化文档处理器"""
        self.embedding_model = SentenceTransformer(settings.EMBEDDING_MODEL)
    
    def split_document(self, content: str, chunk_size: int = 500, overlap: int = 50) -> List[Dict[str, Any]]:
        """
        将文档切分为多个块
        
        Args:
            content: 文档内容
            chunk_size: 块大小（字符数）
            overlap: 重叠大小（字符数）
            
        Returns:
            List[Dict]: 文档块列表，每个块包含内容和元数据
        """
        chunks = []
        
        # 方法1: 按句子切分
        sentences = self._split_into_sentences(content)
        current_chunk = ""
        current_length = 0
        
        for sentence in sentences:
            sentence_length = len(sentence)
            
            # 如果当前块加上新句子超过块大小，则保存当前块
            if current_length + sentence_length > chunk_size and current_chunk:
                # 添加块到结果列表
                chunks.append({
                    "content": current_chunk.strip(),
                    "length": len(current_chunk),
                    "type": "sentence_chunk"
                })
                
                # 保留重叠部分
                current_chunk = self._get_overlap_content(current_chunk, overlap)
                current_length = len(current_chunk)
            
            # 添加新句子
            current_chunk += sentence + " "
            current_length += sentence_length + 1
        
        # 添加最后一个块
        if current_chunk.strip():
            chunks.append({
                "content": current_chunk.strip(),
                "length": len(current_chunk),
                "type": "sentence_chunk"
            })
        
        return chunks
    
    def _split_into_sentences(self, text: str) -> List[str]:
        """
        将文本切分为句子（支持中英文）
        
        Args:
            text: 输入文本
            
        Returns:
            List[str]: 句子列表
        """
        # 中文句子切分
        chinese_sentences = re.split(r'[。！？.!?]+', text)
        
        # 进一步处理，使用jieba进行中文分词辅助切分
        processed_sentences = []
        for sentence in chinese_sentences:
            sentence = sentence.strip()
            if sentence:
                # 对于较长的句子，可以进一步切分
                if len(sentence) > 200:
                    # 使用标点符号进一步切分
                    sub_sentences = re.split(r'[，,；;]', sentence)
                    processed_sentences.extend([s.strip() for s in sub_sentences if s.strip()])
                else:
                    processed_sentences.append(sentence)
        
        # 过滤空句子
        sentences = [s for s in processed_sentences if s]
        return sentences
    
    def _get_overlap_content(self, content: str, overlap: int) -> str:
        """
        获取重叠内容
        
        Args:
            content: 原始内容
            overlap: 重叠字符数
            
        Returns:
            str: 重叠内容
        """
        if len(content) <= overlap:
            return content
        
        # 找到合适的重叠点（尽量在句子边界）
        overlap_start = len(content) - overlap
        last_period = content.rfind('。', overlap_start)
        last_comma = content.rfind('，', overlap_start)
        
        # 选择最接近的标点符号作为重叠起点
        overlap_point = max(last_period, last_comma)
        if overlap_point > overlap_start:
            return content[overlap_point + 1:]
        else:
            return content[overlap_start:]
    
    def create_hierarchical_chunks(self, content: str) -> Dict[str, List[Dict[str, Any]]]:
        """
        创建分层文档块（大块和小块）
        
        Args:
            content: 文档内容
            
        Returns:
            Dict: 包含大块和小块的字典
        """
        # 大块：1000字符，重叠100字符
        large_chunks = self.split_document(content, chunk_size=1000, overlap=100)
        for i, chunk in enumerate(large_chunks):
            chunk["chunk_id"] = f"large_{i}"
            chunk["level"] = "large"
        
        # 小块：300字符，重叠30字符
        small_chunks = self.split_document(content, chunk_size=300, overlap=30)
        for i, chunk in enumerate(small_chunks):
            chunk["chunk_id"] = f"small_{i}"
            chunk["level"] = "small"
        
        return {
            "large_chunks": large_chunks,
            "small_chunks": small_chunks
        }
    
    def vectorize_chunks(self, chunks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        对文档块进行向量化
        
        Args:
            chunks: 文档块列表
            
        Returns:
            List[Dict]: 包含向量的文档块列表
        """
        vectorized_chunks = []
        
        for chunk in chunks:
            try:
                # 生成向量
                vector = self.embedding_model.encode(chunk["content"])
                
                # 添加向量到块中
                chunk_copy = chunk.copy()
                chunk_copy["vector"] = vector.tolist()  # 转换为列表以便存储
                
                vectorized_chunks.append(chunk_copy)
                
            except Exception as e:
                logger.error(f"向量化块失败: {e}")
                # 即使向量化失败，也保留原始块
                vectorized_chunks.append(chunk)
        
        return vectorized_chunks
    
    def process_document(self, doc_id: str, title: str, content: str, 
                        metadata: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """
        处理完整文档（切分+向量化）
        
        Args:
            doc_id: 文档ID
            title: 文档标题
            content: 文档内容
            metadata: 元数据
            
        Returns:
            List[Dict]: 处理后的文档块列表
        """
        logger.info(f"开始处理文档: {title}")
        
        # 创建分层块
        hierarchical_chunks = self.create_hierarchical_chunks(content)
        
        # 合并所有块
        all_chunks = hierarchical_chunks["large_chunks"] + hierarchical_chunks["small_chunks"]
        
        # 添加文档元数据
        for i, chunk in enumerate(all_chunks):
            chunk["doc_id"] = doc_id
            chunk["title"] = title
            chunk["chunk_index"] = i
            chunk["metadata"] = metadata or {}
        
        # 向量化所有块
        vectorized_chunks = self.vectorize_chunks(all_chunks)
        
        logger.info(f"文档处理完成，生成 {len(vectorized_chunks)} 个块")
        
        return vectorized_chunks

# 全局文档处理器实例
doc_processor = DocumentProcessor()