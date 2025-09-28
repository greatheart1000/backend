from algorithms.base import LoadBalancer, Backend
from typing import Optional, Dict, List
import hashlib
import bisect
import threading

class IPHashBalancer(LoadBalancer):
    """IP哈希负载均衡器"""
    
    def __init__(self, hash_function='md5'):
        super().__init__()
        self.hash_function = hash_function
    
    def next_backend(self, client_ip: str = None) -> Optional[Backend]:
        """使用IP哈希算法获取后端服务"""
        backends = self.get_healthy_backends()
        if not backends:
            return None
        
        if not client_ip:
            # 如果没有客户端IP，返回第一个后端
            return backends[0]
        
        # 计算客户端IP的哈希值
        if self.hash_function == 'md5':
            hash_value = int(hashlib.md5(client_ip.encode()).hexdigest(), 16)
        elif self.hash_function == 'sha1':
            hash_value = int(hashlib.sha1(client_ip.encode()).hexdigest(), 16)
        else:
            # 默认使用简单的哈希
            hash_value = hash(client_ip)
        
        # 使用哈希值对后端数量取模
        index = hash_value % len(backends)
        return backends[index]

class ConsistentHashBalancer(LoadBalancer):
    """一致性哈希负载均衡器
    
    相比简单的IP哈希，一致性哈希在节点变化时能提供更好的稳定性
    """
    
    def __init__(self, virtual_nodes: int = 150):
        super().__init__()
        self.virtual_nodes = virtual_nodes
        self.hash_ring: Dict[int, str] = {}  # hash_value -> backend_id
        self.sorted_keys: List[int] = []
        self._ring_lock = threading.Lock()
    
    def _hash(self, key: str) -> int:
        """计算哈希值"""
        return int(hashlib.md5(key.encode()).hexdigest(), 16)
    
    def _rebuild_ring(self):
        """重建哈希环"""
        with self._ring_lock:
            self.hash_ring.clear()
            self.sorted_keys.clear()
            
            backends = self.get_all_backends()
            for backend in backends:
                # 为每个后端创建虚拟节点
                for i in range(self.virtual_nodes):
                    virtual_key = f"{backend.address}:{i}"
                    hash_value = self._hash(virtual_key)
                    self.hash_ring[hash_value] = backend.id
            
            # 对哈希值进行排序
            self.sorted_keys = sorted(self.hash_ring.keys())
    
    def add_backend(self, backend: Backend):
        """添加后端服务"""
        super().add_backend(backend)
        self._rebuild_ring()
    
    def remove_backend(self, backend_id: str):
        """移除后端服务"""
        super().remove_backend(backend_id)
        self._rebuild_ring()
    
    def update_backends(self, backends: List[Backend]):
        """更新后端服务列表"""
        super().update_backends(backends)
        self._rebuild_ring()
    
    def next_backend(self, client_ip: str = None) -> Optional[Backend]:
        """使用一致性哈希算法获取后端服务"""
        if not client_ip:
            backends = self.get_healthy_backends()
            return backends[0] if backends else None
        
        with self._ring_lock:
            if not self.sorted_keys:
                self._rebuild_ring()
            
            if not self.sorted_keys:
                return None
            
            # 计算客户端IP的哈希值
            hash_value = self._hash(client_ip)
            
            # 在哈希环上找到第一个大于等于hash值的节点
            idx = bisect.bisect_right(self.sorted_keys, hash_value)
            
            # 如果没找到，使用第一个节点（环形结构）
            if idx == len(self.sorted_keys):
                idx = 0
            
            # 找到对应的后端
            backend_id = self.hash_ring[self.sorted_keys[idx]]
            backend = self.get_backend(backend_id)
            
            # 如果后端不健康，尝试找下一个健康的后端
            if backend and not backend.is_healthy:
                for i in range(1, len(self.sorted_keys)):
                    next_idx = (idx + i) % len(self.sorted_keys)
                    next_backend_id = self.hash_ring[self.sorted_keys[next_idx]]
                    next_backend = self.get_backend(next_backend_id)
                    if next_backend and next_backend.is_healthy:
                        return next_backend
                return None  # 没有健康的后端
            
            return backend
    
    def get_ring_status(self) -> Dict[str, any]:
        """获取哈希环状态（用于调试）"""
        with self._ring_lock:
            backend_distribution = {}
            for backend_id in self.hash_ring.values():
                backend_distribution[backend_id] = backend_distribution.get(backend_id, 0) + 1
            
            return {
                'total_virtual_nodes': len(self.hash_ring),
                'virtual_nodes_per_backend': self.virtual_nodes,
                'backend_distribution': backend_distribution,
                'ring_size': len(self.sorted_keys)
            }