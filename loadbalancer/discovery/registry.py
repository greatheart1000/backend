from abc import ABC, abstractmethod
from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional, Callable
from enum import Enum
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
import threading
import time
import requests
import socket
import logging

logger = logging.getLogger(__name__)

class ServiceStatus(Enum):
    """服务状态枚举"""
    HEALTHY = "healthy"
    UNHEALTHY = "unhealthy"
    STARTING = "starting"
    STOPPING = "stopping"
    UNKNOWN = "unknown"

@dataclass
class ServiceInstance:
    """服务实例信息"""
    id: str
    name: str
    host: str
    port: int
    weight: int = 1
    status: ServiceStatus = ServiceStatus.HEALTHY
    metadata: Dict[str, Any] = None
    tags: List[str] = None
    register_time: datetime = None
    last_seen: datetime = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}
        if self.tags is None:
            self.tags = []
        if self.register_time is None:
            self.register_time = datetime.now()
        if self.last_seen is None:
            self.last_seen = datetime.now()
    
    @property
    def address(self) -> str:
        """获取完整地址"""
        return f"{self.host}:{self.port}"
    
    @property
    def url(self) -> str:
        """获取HTTP URL"""
        return f"http://{self.host}:{self.port}"
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        data = asdict(self)
        data['status'] = self.status.value
        data['register_time'] = self.register_time.isoformat()
        data['last_seen'] = self.last_seen.isoformat()
        return data
    
    def to_backend(self):
        """转换为Backend对象"""
        from algorithms.base import Backend
        backend = Backend(self.id, self.host, self.port, self.weight)
        backend.set_healthy(self.status == ServiceStatus.HEALTHY)
        return backend

class ServiceRegistry(ABC):
    """服务注册表抽象基类"""
    
    @abstractmethod
    def register(self, instance: ServiceInstance) -> bool:
        """注册服务实例"""
        pass
    
    @abstractmethod
    def deregister(self, service_id: str) -> bool:
        """注销服务实例"""
        pass
    
    @abstractmethod
    def discover(self, service_name: str) -> List[ServiceInstance]:
        """发现服务实例"""
        pass
    
    @abstractmethod
    def get_all_services(self) -> Dict[str, List[ServiceInstance]]:
        """获取所有服务"""
        pass
    
    @abstractmethod
    def update_instance_status(self, service_id: str, status: ServiceStatus) -> bool:
        """更新实例状态"""
        pass
    
    @abstractmethod
    def get_instance(self, service_id: str) -> Optional[ServiceInstance]:
        """获取特定服务实例"""
        pass

class InMemoryServiceRegistry(ServiceRegistry):
    """内存服务注册表实现"""
    
    def __init__(self):
        self.services: Dict[str, Dict[str, ServiceInstance]] = {}  # service_name -> service_id -> instance
        self._lock = threading.Lock()  # 简化为普通锁
    
    def register(self, instance: ServiceInstance) -> bool:
        """注册服务实例"""
        try:
            with self._lock:
                if instance.name not in self.services:
                    self.services[instance.name] = {}
                
                instance.register_time = datetime.now()
                instance.last_seen = datetime.now()
                self.services[instance.name][instance.id] = instance
                
                logger.info(f"Registered service instance: {instance.id} ({instance.address})")
                return True
        except Exception as e:
            logger.error(f"Failed to register service instance {instance.id}: {e}")
            return False
    
    def deregister(self, service_id: str) -> bool:
        """注销服务实例"""
        try:
            with self._lock:
                for service_name, instances in self.services.items():
                    if service_id in instances:
                        del instances[service_id]
                        if not instances:  # 如果服务下没有实例了，删除整个服务
                            del self.services[service_name]
                        logger.info(f"Deregistered service instance: {service_id}")
                        return True
                return False
        except Exception as e:
            logger.error(f"Failed to deregister service instance {service_id}: {e}")
            return False
    
    def discover(self, service_name: str) -> List[ServiceInstance]:
        """发现服务实例"""
        with self._lock:
            instances = self.services.get(service_name, {})
            # 只返回健康的实例
            return [
                instance for instance in instances.values()
                if instance.status == ServiceStatus.HEALTHY
            ]
    
    def get_all_services(self) -> Dict[str, List[ServiceInstance]]:
        """获取所有服务"""
        with self._lock:
            result = {}
            for service_name, instances in self.services.items():
                result[service_name] = list(instances.values())
            return result
    
    def update_instance_status(self, service_id: str, status: ServiceStatus) -> bool:
        """更新实例状态"""
        try:
            with self._lock:
                for instances in self.services.values():
                    if service_id in instances:
                        instances[service_id].status = status
                        instances[service_id].last_seen = datetime.now()
                        return True
                return False
        except Exception as e:
            logger.error(f"Failed to update status for service {service_id}: {e}")
            return False
    
    def get_instance(self, service_id: str) -> Optional[ServiceInstance]:
        """获取特定服务实例"""
        with self._lock:
            for instances in self.services.values():
                if service_id in instances:
                    return instances[service_id]
            return None
    
    def get_healthy_instances(self, service_name: str) -> List[ServiceInstance]:
        """获取健康的服务实例"""
        return self.discover(service_name)
    
    def get_all_instances(self, service_name: str) -> List[ServiceInstance]:
        """获取所有服务实例（包括不健康的）"""
        with self._lock:
            instances = self.services.get(service_name, {})
            return list(instances.values())
    
    def cleanup_expired_instances(self, ttl: timedelta):
        """清理过期的服务实例"""
        with self._lock:
            expired_services = []
            current_time = datetime.now()
            
            for service_name, instances in self.services.items():
                expired_instances = []
                for instance_id, instance in instances.items():
                    if current_time - instance.last_seen > ttl:
                        expired_instances.append(instance_id)
                
                for instance_id in expired_instances:
                    del instances[instance_id]
                    logger.info(f"Cleaned up expired instance: {instance_id}")
                
                if not instances:
                    expired_services.append(service_name)
            
            for service_name in expired_services:
                del self.services[service_name]

# 简化的读写锁实现（Python版本）
threading.RWLock = threading.RLock  # 简化实现，实际应用中可以使用更完整的读写锁