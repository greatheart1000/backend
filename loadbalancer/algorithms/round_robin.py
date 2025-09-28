from algorithms.base import LoadBalancer, Backend
from typing import Optional
import threading

class RoundRobinBalancer(LoadBalancer):
    """轮询负载均衡器"""
    
    def __init__(self):
        super().__init__()
        self.current_index = 0
    
    def next_backend(self, client_ip: str = None) -> Optional[Backend]:
        """使用轮询算法获取下一个后端服务"""
        backends = self.get_healthy_backends()
        if not backends:
            return None
        
        with self._lock:
            backend = backends[self.current_index % len(backends)]
            self.current_index = (self.current_index + 1) % len(backends)
            return backend
    
    def reset(self):
        """重置轮询计数器"""
        with self._lock:
            self.current_index = 0