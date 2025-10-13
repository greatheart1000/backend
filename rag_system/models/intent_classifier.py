from typing import Dict, Tuple
from transformers import pipeline
import torch
import logging
from cache.cache_manager import cache_manager
from config.settings import settings

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class IntentClassifier:
    def __init__(self):
        """初始化意图分类器"""
        # 初始化意图分类模型
        # 注意：这里使用一个轻量级的零样本分类模型作为示例
        # 在实际应用中，可能需要训练专门的意图分类模型
        self.classifier = pipeline(
            "zero-shot-classification",
            model=settings.INTENT_MODEL,
            device=0 if torch.cuda.is_available() else -1
        )
        
        # 定义意图类别
        self.intent_labels = [
            "A类：事实问答",  # Fact-based QA
            "B类：推理问题",  # Reasoning-based
            "C类：操作指导",  # Instructional
            "D类：闲聊对话"   # Chit-chat
        ]
        
        # 默认权重
        self.default_weights = {
            "bm25": 0.5,
            "vector": 0.5
        }
    
    def classify_intent(self, query: str) -> Tuple[str, Dict[str, float]]:
        """
        分析查询意图并确定检索权重
        
        Args:
            query: 用户查询
            
        Returns:
            tuple: (意图类别, 权重字典)
        """
        # 构建缓存键
        cache_key = f"intent:{hash(query)}"
        
        # 尝试从缓存获取结果
        cached_result = cache_manager.get(cache_key)
        if cached_result:
            logger.info(f"从缓存获取意图分类结果: {cached_result[0]}")
            return cached_result
        
        try:
            # 执行意图分类
            result = self.classifier(query, self.intent_labels)
            
            # 获取最高分的意图类别
            intent = result['labels'][0]
            confidence = result['scores'][0]
            
            # 根据意图类型确定权重
            weights = self._determine_weights(intent, confidence)
            
            # 缓存结果
            cache_manager.set(cache_key, (intent, weights), settings.CACHE_EXPIRE_TIME)
            
            logger.info(f"意图分类完成: {intent} (置信度: {confidence:.2f})")
            return intent, weights
        except Exception as e:
            logger.error(f"意图分类失败: {e}")
            # 返回默认意图和权重
            return "D类：闲聊对话", self.default_weights.copy()
    
    def _determine_weights(self, intent: str, confidence: float) -> Dict[str, float]:
        """
        根据意图类型和置信度确定检索权重
        
        Args:
            intent: 意图类别
            confidence: 分类置信度
            
        Returns:
            Dict: 权重字典
        """
        # 基于意图类型的权重分配策略
        if "A类" in intent:
            # 事实问答更依赖精确匹配
            return {
                "bm25": 0.7,
                "vector": 0.3
            }
        elif "B类" in intent:
            # 推理问题需要语义理解
            return {
                "bm25": 0.3,
                "vector": 0.7
            }
        elif "C类" in intent:
            # 操作指导需要结合关键词和语义
            return {
                "bm25": 0.5,
                "vector": 0.5
            }
        elif "D类" in intent:
            # 闲聊对话更注重语义相似性
            return {
                "bm25": 0.2,
                "vector": 0.8
            }
        else:
            # 默认权重
            return self.default_weights.copy()

# 全局意图分类器实例
intent_classifier = IntentClassifier()