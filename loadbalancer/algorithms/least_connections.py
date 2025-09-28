from algorithms.base import LoadBalancer, Backend
from typing import Optional, Dict
import threading
import time

class LeastConnectionsBalancer(LoadBalancer):
    """最少连接负载均衡器"""
    
    def next_backend(self, client_ip: str = None) -> Optional[Backend]:
        """使用最少连接算法获取后端服务"""
        backends = self.get_healthy_backends()
        if not backends:
            return None
        
        # 找到连接数最少的后端服务
        min_connections = float('inf')
        selected = None
        
        for backend in backends:
            if backend.active_connections < min_connections:
                min_connections = backend.active_connections
                selected = backend
        
        return selected

class WeightedLeastConnectionsBalancer(LoadBalancer):
    """加权最少连接负载均衡器"""
    
    def next_backend(self, client_ip: str = None) -> Optional[Backend]:
        """使用加权最少连接算法获取后端服务"""
        backends = self.get_healthy_backends()
        if not backends:
            return None
        
        # 计算每个后端的连接数与权重的比值，选择比值最小的
        min_ratio = float('inf')
        selected = None
        
        for backend in backends:
            weight = max(backend.weight, 1)  # 避免除零错误
            ratio = backend.active_connections / weight
            
            if ratio < min_ratio:
                min_ratio = ratio
                selected = backend
        
        return selected

class FastestResponseBalancer(LoadBalancer):
    """最快响应时间负载均衡器
    
    结合连接数和响应时间进行负载均衡
    """
    
    def __init__(self, connection_weight: float = 0.6, response_time_weight: float = 0.4):
        super().__init__()
        self.connection_weight = connection_weight
        self.response_time_weight = response_time_weight
        self.response_times: Dict[str, 'ResponseTimeTracker'] = {}
        self._tracker_lock = threading.Lock()
    
    def next_backend(self, client_ip: str = None) -> Optional[Backend]:
        """选择连接数少且响应时间快的后端服务"""
        backends = self.get_healthy_backends()
        if not backends:
            return None
        
        min_score = float('inf')
        selected = None
        
        with self._tracker_lock:
            for backend in backends:
                # 获取连接数得分（标准化到0-1）
                max_connections = max((b.active_connections for b in backends), default=1)
                connection_score = backend.active_connections / max_connections if max_connections > 0 else 0
                
                # 获取响应时间得分（标准化到0-1）
                if backend.id not in self.response_times:
                    self.response_times[backend.id] = ResponseTimeTracker()
                
                avg_response_time = self.response_times[backend.id].get_average()
                max_response_time = max((
                    self.response_times.get(b.id, ResponseTimeTracker()).get_average() 
                    for b in backends
                ), default=100)
                
                response_time_score = avg_response_time / max_response_time if max_response_time > 0 else 0
                
                # 计算综合得分（得分越低越好）
                score = (connection_score * self.connection_weight + 
                        response_time_score * self.response_time_weight)
                
                if score < min_score:
                    min_score = score
                    selected = backend
        
        return selected
    
    def update_response_time(self, backend_id: str, response_time_ms: float):
        """更新后端服务的响应时间"""
        with self._tracker_lock:
            if backend_id not in self.response_times:
                self.response_times[backend_id] = ResponseTimeTracker()
            self.response_times[backend_id].add_response_time(response_time_ms)
    
    def get_response_time_stats(self, backend_id: str) -> Dict[str, float]:
        """获取响应时间统计信息"""
        with self._tracker_lock:
            if backend_id not in self.response_times:
                return {'average': 0, 'count': 0, 'min': 0, 'max': 0}
            return self.response_times[backend_id].get_stats()
    
    def clear_response_time_stats(self):
        """清空响应时间统计"""
        with self._tracker_lock:
            self.response_times.clear()

class ResponseTimeTracker:
    """响应时间跟踪器"""
    
    def __init__(self, max_samples: int = 100):
        self.max_samples = max_samples
        self.response_times = []
        self.total_time = 0
        self.count = 0
        self._lock = threading.Lock()
    
    def add_response_time(self, response_time_ms: float):
        """添加响应时间样本"""
        with self._lock:
            if len(self.response_times) >= self.max_samples:
                # 移除最旧的样本
                removed = self.response_times.pop(0)
                self.total_time -= removed
            
            self.response_times.append(response_time_ms)
            self.total_time += response_time_ms
            self.count += 1
    
    def get_average(self) -> float:
        """获取平均响应时间"""
        with self._lock:
            if not self.response_times:
                return 100.0  # 默认值
            return self.total_time / len(self.response_times)
    
    def get_stats(self) -> Dict[str, float]:
        """获取详细统计信息"""
        with self._lock:
            if not self.response_times:
                return {'average': 100.0, 'count': 0, 'min': 0, 'max': 0}
            
            return {
                'average': self.total_time / len(self.response_times),
                'count': len(self.response_times),
                'min': min(self.response_times),
                'max': max(self.response_times)
            }