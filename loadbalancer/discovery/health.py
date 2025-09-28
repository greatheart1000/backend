from abc import ABC, abstractmethod
from typing import List, Callable, Optional, Set
import threading
import time
import requests
import socket
import logging
from datetime import datetime, timedelta
from discovery.registry import ServiceInstance, ServiceRegistry, ServiceStatus

logger = logging.getLogger(__name__)

class HealthChecker(ABC):
    """健康检查器抽象基类"""
    
    @abstractmethod
    def start(self):
        """开始健康检查"""
        pass
    
    @abstractmethod
    def stop(self):
        """停止健康检查"""
        pass
    
    @abstractmethod
    def add_instance(self, instance: ServiceInstance):
        """添加需要检查的实例"""
        pass
    
    @abstractmethod
    def remove_instance(self, instance_id: str):
        """移除实例"""
        pass
    
    @abstractmethod
    def is_healthy(self, instance_id: str) -> bool:
        """检查实例是否健康"""
        pass

class HTTPHealthChecker(HealthChecker):
    """HTTP健康检查器"""
    
    def __init__(self, 
                 registry: ServiceRegistry,
                 check_interval: int = 10,
                 timeout: int = 5,
                 health_path: str = '/health'):
        self.registry = registry
        self.check_interval = check_interval
        self.timeout = timeout
        self.health_path = health_path
        
        self.instances: Set[str] = set()  # instance_id集合
        self.health_status: dict = {}  # instance_id -> bool
        self.is_running = False
        self.check_thread: Optional[threading.Thread] = None
        self.stop_event = threading.Event()
        self._lock = threading.Lock()
        
        # 健康检查结果回调
        self.on_health_changed: Optional[Callable[[str, bool], None]] = None
        
        # HTTP会话，复用连接
        self.session = requests.Session()
        self.session.timeout = self.timeout
    
    def set_health_changed_callback(self, callback: Callable[[str, bool], None]):
        """设置健康状态变化回调"""
        self.on_health_changed = callback
    
    def start(self):
        """开始健康检查"""
        with self._lock:
            if self.is_running:
                logger.warning("Health checker is already running")
                return
            
            self.is_running = True
            self.stop_event.clear()
            self.check_thread = threading.Thread(target=self._health_check_loop, daemon=True)
            self.check_thread.start()
            logger.info("HTTP health checker started")
    
    def stop(self):
        """停止健康检查"""
        with self._lock:
            if not self.is_running:
                logger.warning("Health checker is not running")
                return
            
            self.is_running = False
            self.stop_event.set()
            
            if self.check_thread and self.check_thread.is_alive():
                self.check_thread.join(timeout=5)
            
            self.session.close()
            logger.info("HTTP health checker stopped")
    
    def add_instance(self, instance: ServiceInstance):
        """添加需要检查的实例"""
        with self._lock:
            self.instances.add(instance.id)
            self.health_status[instance.id] = True  # 默认为健康
            logger.debug(f"Added instance to health check: {instance.id}")
    
    def remove_instance(self, instance_id: str):
        """移除实例"""
        with self._lock:
            self.instances.discard(instance_id)
            self.health_status.pop(instance_id, None)
            logger.debug(f"Removed instance from health check: {instance_id}")
    
    def is_healthy(self, instance_id: str) -> bool:
        """检查实例是否健康"""
        with self._lock:
            return self.health_status.get(instance_id, False)
    
    def _health_check_loop(self):
        """健康检查循环"""
        while not self.stop_event.wait(self.check_interval):
            try:
                self._perform_health_checks()
            except Exception as e:
                logger.error(f"Error in health check loop: {e}")
    
    def _perform_health_checks(self):
        """执行健康检查"""
        with self._lock:
            instance_ids = list(self.instances)
        
        # 并发执行健康检查
        threads = []
        for instance_id in instance_ids:
            thread = threading.Thread(
                target=self._check_single_instance,
                args=(instance_id,),
                daemon=True
            )
            threads.append(thread)
            thread.start()
        
        # 等待所有检查完成
        for thread in threads:
            thread.join(timeout=self.timeout + 1)
    
    def _check_single_instance(self, instance_id: str):
        """检查单个实例的健康状态"""
        try:
            instance = self.registry.get_instance(instance_id)
            if not instance:
                logger.warning(f"Instance {instance_id} not found in registry")
                return
            
            url = f"http://{instance.host}:{instance.port}{self.health_path}"
            
            try:
                response = self.session.get(url, timeout=self.timeout)
                is_healthy = 200 <= response.status_code < 300
            except requests.RequestException:
                is_healthy = False
            
            self._update_health_status(instance_id, is_healthy)
            
        except Exception as e:
            logger.error(f"Error checking health for instance {instance_id}: {e}")
            self._update_health_status(instance_id, False)
    
    def _update_health_status(self, instance_id: str, is_healthy: bool):
        """更新健康状态"""
        with self._lock:
            old_status = self.health_status.get(instance_id, True)
            self.health_status[instance_id] = is_healthy
        
        # 如果状态发生变化，更新注册表并调用回调
        if old_status != is_healthy:
            status = ServiceStatus.HEALTHY if is_healthy else ServiceStatus.UNHEALTHY
            self.registry.update_instance_status(instance_id, status)
            
            logger.info(f"Instance {instance_id} health changed: {is_healthy}")
            
            if self.on_health_changed:
                try:
                    self.on_health_changed(instance_id, is_healthy)
                except Exception as e:
                    logger.error(f"Error in health changed callback: {e}")
    
    def get_stats(self) -> dict:
        """获取健康检查统计信息"""
        with self._lock:
            total_instances = len(self.instances)
            healthy_instances = sum(1 for status in self.health_status.values() if status)
            
            return {
                'type': 'http',
                'total_instances': total_instances,
                'healthy_instances': healthy_instances,
                'unhealthy_instances': total_instances - healthy_instances,
                'check_interval': self.check_interval,
                'timeout': self.timeout,
                'health_path': self.health_path,
                'is_running': self.is_running
            }

class TCPHealthChecker(HealthChecker):
    """TCP健康检查器"""
    
    def __init__(self, 
                 registry: ServiceRegistry,
                 check_interval: int = 10,
                 timeout: int = 3):
        self.registry = registry
        self.check_interval = check_interval
        self.timeout = timeout
        
        self.instances: Set[str] = set()
        self.health_status: dict = {}
        self.is_running = False
        self.check_thread: Optional[threading.Thread] = None
        self.stop_event = threading.Event()
        self._lock = threading.Lock()
        
        self.on_health_changed: Optional[Callable[[str, bool], None]] = None
    
    def set_health_changed_callback(self, callback: Callable[[str, bool], None]):
        """设置健康状态变化回调"""
        self.on_health_changed = callback
    
    def start(self):
        """开始健康检查"""
        with self._lock:
            if self.is_running:
                logger.warning("TCP health checker is already running")
                return
            
            self.is_running = True
            self.stop_event.clear()
            self.check_thread = threading.Thread(target=self._health_check_loop, daemon=True)
            self.check_thread.start()
            logger.info("TCP health checker started")
    
    def stop(self):
        """停止健康检查"""
        with self._lock:
            if not self.is_running:
                logger.warning("TCP health checker is not running")
                return
            
            self.is_running = False
            self.stop_event.set()
            
            if self.check_thread and self.check_thread.is_alive():
                self.check_thread.join(timeout=5)
            
            logger.info("TCP health checker stopped")
    
    def add_instance(self, instance: ServiceInstance):
        """添加需要检查的实例"""
        with self._lock:
            self.instances.add(instance.id)
            self.health_status[instance.id] = True
            logger.debug(f"Added instance to TCP health check: {instance.id}")
    
    def remove_instance(self, instance_id: str):
        """移除实例"""
        with self._lock:
            self.instances.discard(instance_id)
            self.health_status.pop(instance_id, None)
            logger.debug(f"Removed instance from TCP health check: {instance_id}")
    
    def is_healthy(self, instance_id: str) -> bool:
        """检查实例是否健康"""
        with self._lock:
            return self.health_status.get(instance_id, False)
    
    def _health_check_loop(self):
        """健康检查循环"""
        while not self.stop_event.wait(self.check_interval):
            try:
                self._perform_health_checks()
            except Exception as e:
                logger.error(f"Error in TCP health check loop: {e}")
    
    def _perform_health_checks(self):
        """执行健康检查"""
        with self._lock:
            instance_ids = list(self.instances)
        
        # 并发执行健康检查
        threads = []
        for instance_id in instance_ids:
            thread = threading.Thread(
                target=self._check_single_instance,
                args=(instance_id,),
                daemon=True
            )
            threads.append(thread)
            thread.start()
        
        # 等待所有检查完成
        for thread in threads:
            thread.join(timeout=self.timeout + 1)
    
    def _check_single_instance(self, instance_id: str):
        """检查单个实例的健康状态"""
        try:
            instance = self.registry.get_instance(instance_id)
            if not instance:
                logger.warning(f"Instance {instance_id} not found in registry")
                return
            
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(self.timeout)
                result = sock.connect_ex((instance.host, instance.port))
                sock.close()
                is_healthy = (result == 0)
            except Exception:
                is_healthy = False
            
            self._update_health_status(instance_id, is_healthy)
            
        except Exception as e:
            logger.error(f"Error checking TCP health for instance {instance_id}: {e}")
            self._update_health_status(instance_id, False)
    
    def _update_health_status(self, instance_id: str, is_healthy: bool):
        """更新健康状态"""
        with self._lock:
            old_status = self.health_status.get(instance_id, True)
            self.health_status[instance_id] = is_healthy
        
        if old_status != is_healthy:
            status = ServiceStatus.HEALTHY if is_healthy else ServiceStatus.UNHEALTHY
            self.registry.update_instance_status(instance_id, status)
            
            logger.info(f"Instance {instance_id} TCP health changed: {is_healthy}")
            
            if self.on_health_changed:
                try:
                    self.on_health_changed(instance_id, is_healthy)
                except Exception as e:
                    logger.error(f"Error in TCP health changed callback: {e}")
    
    def get_stats(self) -> dict:
        """获取健康检查统计信息"""
        with self._lock:
            total_instances = len(self.instances)
            healthy_instances = sum(1 for status in self.health_status.values() if status)
            
            return {
                'type': 'tcp',
                'total_instances': total_instances,
                'healthy_instances': healthy_instances,
                'unhealthy_instances': total_instances - healthy_instances,
                'check_interval': self.check_interval,
                'timeout': self.timeout,
                'is_running': self.is_running
            }