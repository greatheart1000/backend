from typing import List, Dict, Any
import openai
import json
import logging
from openai import OpenAI
from cache.cache_manager import cache_manager
from config.settings import settings

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AnswerGenerator:
    def __init__(self):
        """初始化答案生成器"""
        # 初始化Qwen API客户端
        self.client = OpenAI(
            api_key=settings.QWEN_API_KEY,
            base_url=settings.QWEN_API_BASE
        )
    
    def generate_answer(self, query: str, documents: List[Dict[str, Any]], 
                       query_vector: Any = None, session_history: List[Dict[str, str]] = None) -> str:
        """
        基于检索到的文档生成答案
        
        Args:
            query: 用户查询
            documents: 检索到的相关文档
            query_vector: 查询向量（可选）
            session_history: 会话历史（可选）
            
        Returns:
            str: 生成的答案
        """
        # 构建缓存键
        doc_ids = [doc["id"] for doc in documents]
        cache_key = f"answer:{hash(query)}:{hash(str(sorted(doc_ids)))}"
        
        # 尝试从缓存获取结果
        cached_answer = cache_manager.get(cache_key)
        if cached_answer:
            logger.info("从缓存获取答案")
            return cached_answer
        
        # 构建上下文
        context = self._build_context(documents)
        
        # 构建Prompt
        prompt = self._build_prompt(query, context, session_history)
        
        # 调用Qwen API生成答案
        try:
            response = self.client.chat.completions.create(
                model="qwen-plus",  # 或者使用 qwen-turbo, qwen-max 等
                messages=[
                    {"role": "system", "content": "你是一个智能问答助手，请基于提供的文档内容准确回答用户问题。"},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=1000
            )
            
            answer = response.choices[0].message.content
            
            # 缓存结果
            cache_manager.set(cache_key, answer, settings.CACHE_EXPIRE_TIME)
            
            return answer
        except Exception as e:
            logger.error(f"答案生成失败: {e}")
            return "抱歉，我无法生成答案，请稍后重试。"
    
    def _build_context(self, documents: List[Dict[str, Any]]) -> str:
        """
        构建文档上下文
        
        Args:
            documents: 文档列表
            
        Returns:
            str: 格式化的文档上下文
        """
        if not documents:
            return ""
        
        # 按文档ID分组块
        doc_groups = {}
        for doc in documents:
            source = doc.get("source", {})
            doc_id = source.get("doc_id", "unknown")
            if doc_id not in doc_groups:
                doc_groups[doc_id] = []
            doc_groups[doc_id].append(source)
        
        # 为每个文档构建上下文
        context_parts = []
        for doc_id, chunks in doc_groups.items():
            # 按块索引排序
            chunks.sort(key=lambda x: x.get("chunk_index", 0))
            
            # 获取文档标题
            title = chunks[0].get("title", "Unknown Document")
            
            # 合并相关块内容
            content_parts = []
            for chunk in chunks[:3]:  # 只使用前3个相关块
                content = chunk.get("content", "")
                chunk_level = chunk.get("chunk_level", "unknown")
                content_parts.append(f"[{chunk_level.upper()}] {content}")
            
            combined_content = " ".join(content_parts)
            context_parts.append(f"文档: {title}\n内容: {combined_content}\n")
        
        return "\n".join(context_parts)
    
    def _build_prompt(self, query: str, context: str, session_history: List[Dict[str, str]] = None) -> str:
        """
        构建Prompt
        
        Args:
            query: 用户查询
            context: 文档上下文
            session_history: 会话历史
            
        Returns:
            str: 构建的Prompt
        """
        prompt_parts = []
        
        # 添加会话历史（如果有）
        if session_history:
            history_text = "\n".join([
                f"用户: {interaction['query']}\n助手: {interaction['response']}"
                for interaction in session_history[-2:]  # 只使用最近2轮对话
            ])
            prompt_parts.append(f"对话历史:\n{history_text}\n")
        
        # 添加当前查询和文档上下文
        prompt_parts.append(f"用户问题: {query}\n")
        prompt_parts.append(f"相关文档:\n{context}\n")
        prompt_parts.append("请基于以上文档内容回答用户问题，如果文档中没有相关信息，请说明无法基于提供的文档回答该问题。")
        
        return "\n".join(prompt_parts)

# 全局答案生成器实例
answer_generator = AnswerGenerator()