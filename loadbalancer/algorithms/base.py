from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
import time
import threading
from datetime import datetime

class Backend:
    """后端服务实例"""
    
    def __init__(self, id: str, host: str, port: int, weight: int = 1):
        self.id = id
        self.host = host
        self.port = port
        self.weight = weight
        self.active_connections = 0
        self.is_healthy = True
        self.last_seen = datetime.now()
        self._lock = threading.RLock()
        
        # 统计信息
        self.total_requests = 0
        self.total_response_time = 0
        self.error_count = 0
    
    @property
    def address(self) -> str:
        """获取完整地址"""
        return f"{self.host}:{self.port}"
    
    @property
    def url(self) -> str:
        """获取HTTP URL"""
        return f"http://{self.host}:{self.port}"
    
    def increment_active(self):
        """增加活跃连接数"""
        with self._lock:
            self.active_connections += 1
    
    def decrement_active(self):
        """减少活跃连接数"""
        with self._lock:
            if self.active_connections > 0:
                self.active_connections -= 1
    
    def update_response_time(self, response_time_ms: float):
        """更新响应时间统计"""
        with self._lock:
            self.total_requests += 1
            self.total_response_time += response_time_ms
    
    def get_average_response_time(self) -> float:
        """获取平均响应时间"""
        with self._lock:
            if self.total_requests == 0:
                return 0.0
            return self.total_response_time / self.total_requests
    
    def mark_error(self):
        """标记错误"""
        with self._lock:
            self.error_count += 1
    
    def set_healthy(self, healthy: bool):
        """设置健康状态"""
        with self._lock:
            self.is_healthy = healthy
            if healthy:
                self.last_seen = datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'id': self.id,
            'host': self.host,
            'port': self.port,
            'weight': self.weight,
            'active_connections': self.active_connections,
            'is_healthy': self.is_healthy,
            'last_seen': self.last_seen.isoformat(),
            'total_requests': self.total_requests,
            'average_response_time': self.get_average_response_time(),
            'error_count': self.error_count
        }

class BackendPool:
    """后端服务池"""
    
    def __init__(self):
        self.backends: Dict[str, Backend] = {}
        self._lock = threading.RWMutex()
    
    def add_backend(self, backend: Backend):
        """添加后端服务"""
        with self._lock.write_lock():
            self.backends[backend.id] = backend
    
    def remove_backend(self, backend_id: str):
        """移除后端服务"""
        with self._lock.write_lock():
            if backend_id in self.backends:
                del self.backends[backend_id]
    
    def get_backend(self, backend_id: str) -> Optional[Backend]:
        """获取指定后端服务"""
        with self._lock.read_lock():
            return self.backends.get(backend_id)
    
    def get_all_backends(self) -> List[Backend]:
        """获取所有后端服务"""
        with self._lock.read_lock():
            return list(self.backends.values())
    
    def get_healthy_backends(self) -> List[Backend]:
        """获取健康的后端服务"""
        with self._lock.read_lock():
            return [backend for backend in self.backends.values() 
                   if backend.is_healthy]
    
    def size(self) -> int:
        """获取后端服务数量"""
        with self._lock.read_lock():
            return len(self.backends)
    
    def update_backends(self, backends: List[Backend]):
        """更新后端服务列表"""
        with self._lock.write_lock():
            self.backends.clear()
            for backend in backends:
                self.backends[backend.id] = backend

class LoadBalancer(ABC):
    """负载均衡器抽象基类"""
    
    def __init__(self):
        self.pool = BackendPool()
        self._lock = threading.Lock()
    
    @abstractmethod
    def next_backend(self, client_ip: str = None) -> Optional[Backend]:
        """获取下一个后端服务"""
        pass
    
    def add_backend(self, backend: Backend):
        """添加后端服务"""
        self.pool.add_backend(backend)
    
    def remove_backend(self, backend_id: str):
        """移除后端服务"""
        self.pool.remove_backend(backend_id)
    
    def get_backend(self, backend_id: str) -> Optional[Backend]:
        """获取指定后端服务"""
        return self.pool.get_backend(backend_id)
    
    def get_all_backends(self) -> List[Backend]:
        """获取所有后端服务"""
        return self.pool.get_all_backends()
    
    def get_healthy_backends(self) -> List[Backend]:
        """获取健康的后端服务"""
        return self.pool.get_healthy_backends()
    
    def update_backends(self, backends: List[Backend]):
        """更新后端服务列表"""
        self.pool.update_backends(backends)
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        backends = self.get_all_backends()
        healthy_count = len(self.get_healthy_backends())
        
        total_requests = sum(b.total_requests for b in backends)
        total_errors = sum(b.error_count for b in backends)
        avg_response_time = sum(b.get_average_response_time() for b in backends) / len(backends) if backends else 0
        
        return {
            'algorithm': self.__class__.__name__,
            'total_backends': len(backends),
            'healthy_backends': healthy_count,
            'unhealthy_backends': len(backends) - healthy_count,
            'total_requests': total_requests,
            'total_errors': total_errors,
            'error_rate': total_errors / total_requests if total_requests > 0 else 0,
            'average_response_time': avg_response_time,
            'backends': [b.to_dict() for b in backends]
        }

# 简化的读写锁实现（仅用于演示）
class RWLock:
    """简化的读写锁"""
    def __init__(self):
        self._read_count = 0
        self._readers = threading.Lock()
        self._writer = threading.Lock()
    
    def read_lock(self):
        return ReadLock(self)
    
    def write_lock(self):
        return WriteLock(self)

class ReadLock:
    def __init__(self, rw_lock):
        self.rw_lock = rw_lock
    
    def __enter__(self):
        self.rw_lock._readers.acquire()
        self.rw_lock._read_count += 1
        if self.rw_lock._read_count == 1:
            self.rw_lock._writer.acquire()
        self.rw_lock._readers.release()
    
    def __exit__(self, *args):
        self.rw_lock._readers.acquire()
        self.rw_lock._read_count -= 1
        if self.rw_lock._read_count == 0:
            self.rw_lock._writer.release()
        self.rw_lock._readers.release()

class WriteLock:
    def __init__(self, rw_lock):
        self.rw_lock = rw_lock
    
    def __enter__(self):
        self.rw_lock._writer.acquire()
    
    def __exit__(self, *args):
        self.rw_lock._writer.release()

# 为BackendPool添加读写锁
threading.RWMutex = RWLock