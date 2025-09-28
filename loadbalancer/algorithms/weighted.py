from algorithms.base import LoadBalancer, Backend
from typing import Optional, Dict
import threading

class WeightedRoundRobinBalancer(LoadBalancer):
    """加权轮询负载均衡器"""
    
    def __init__(self):
        super().__init__()
        self.weights: Dict[str, int] = {}  # backend_id -> current_weight
    
    def next_backend(self, client_ip: str = None) -> Optional[Backend]:
        """使用加权轮询算法获取下一个后端服务"""
        backends = self.get_healthy_backends()
        if not backends:
            return None
        
        with self._lock:
            # 初始化权重信息
            for backend in backends:
                if backend.id not in self.weights:
                    self.weights[backend.id] = 0
            
            # 计算总权重
            total_weight = sum(backend.weight for backend in backends)
            if total_weight == 0:
                # 如果所有权重都为0，使用简单轮询
                return backends[0]
            
            # 更新当前权重并选择最大的
            selected = None
            max_current_weight = -1
            
            for backend in backends:
                self.weights[backend.id] += backend.weight
                if self.weights[backend.id] > max_current_weight:
                    max_current_weight = self.weights[backend.id]
                    selected = backend
            
            # 减少选中服务器的当前权重
            if selected:
                self.weights[selected.id] -= total_weight
            
            return selected

class SmoothWeightedRoundRobinBalancer(LoadBalancer):
    """平滑加权轮询负载均衡器
    
    这个实现提供更好的负载分布，避免权重高的服务器
    在短时间内被连续选择
    """
    
    def __init__(self):
        super().__init__()
        self.current_weights: Dict[str, int] = {}  # backend_id -> current_weight
    
    def next_backend(self, client_ip: str = None) -> Optional[Backend]:
        """使用平滑加权轮询算法获取下一个后端服务"""
        backends = self.get_healthy_backends()
        if not backends:
            return None
        
        with self._lock:
            # 初始化或更新权重信息
            for backend in backends:
                if backend.id not in self.current_weights:
                    self.current_weights[backend.id] = 0
            
            # 清理不存在的后端
            existing_ids = {b.id for b in backends}
            self.current_weights = {
                k: v for k, v in self.current_weights.items() 
                if k in existing_ids
            }
            
            # 计算总权重
            total_weight = sum(backend.weight for backend in backends)
            if total_weight == 0:
                return backends[0]
            
            # 选择当前权重最高的后端
            selected = None
            max_current_weight = float('-inf')
            
            # 第一步：每个后端的当前权重加上其配置权重
            for backend in backends:
                self.current_weights[backend.id] += backend.weight
                
                if self.current_weights[backend.id] > max_current_weight:
                    max_current_weight = self.current_weights[backend.id]
                    selected = backend
            
            # 第二步：将选中后端的当前权重减去总权重
            if selected:
                self.current_weights[selected.id] -= total_weight
            
            return selected
    
    def get_weight_status(self) -> Dict[str, int]:
        """获取当前权重状态（用于调试）"""
        with self._lock:
            return self.current_weights.copy()